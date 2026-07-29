#!/usr/bin/env python3
"""Build SSSOM alignment sets for the CDIF XAS concept hub.

Architecture: concept-keyed, with XDI and NeXus as two bindings.

    XDI token  --\
                  >--  CDIF XAS concept (hub)  -->  CDIF JSON-LD
    NeXus path --/

This script emits two SSSOM mapping sets:

    xdi-to-cdifxas.sssom.tsv      XDI token      -> CDIF XAS concept
    cdifxas-to-nexus.sssom.tsv    CDIF XAS concept -> NeXus concept path

Scope: **all six detection modes** of the restructured NeXus NXxas
family -- transmission, total and partial electron yield, total and
partial fluorescence yield, and high energy resolution fluorescence
detected -- plus the mode-independent concepts on the NXxas base.

The XDI set covers transmission only, which is not an omission: XDI is a
transmission/fluorescence-era format and defines no tokens for retarding
voltage, emission-line selection, or crystal-analyzer geometry. Those
concepts reach CDIF through the NeXus binding alone.

** Mappings are curated, validation is automated **

SSSOM predicates are judgments (exactMatch vs closeMatch vs relatedMatch
is not inferable), so the mapping rows below are hand-authored. What IS
automated is checking that every subject and object actually exists in
its source vocabulary:

  * CDIF XAS concepts are checked against XAS_Glossary_SKOS.json
  * XDI tokens are checked against the concept keys the production RML
    mapping actually reads (resources/mapping_dds.ttl in
    (Github) smrgeoinfo/cdif-xas), so the alignment cannot drift from the
    converter. That repository is found by looking beside this one, or
    at $CDIF_XAS_RML. Not finding it is a validation failure, not a
    skipped check -- pass --no-rml-check to build without it.
  * NeXus paths are checked against the live NXDL definitions;
    as of 2026-07-28 when this note was writted, the definitions are under
    review and revisions for a new NXxas profile; the current working
    repository is https://github.com/XraySpectroscopy/nexus_definitions, which
    is forked from https://github.com/nexusformat/definitions

That last check is the point: the XAS definitions are in flux, so a
renamed or moved field surfaces here as a validation failure rather than
as silently wrong output.

Usage:
    python crosswalk/build_crosswalk.py [--ref main] [--no-validate]
    python crosswalk/build_crosswalk.py --check   # validate only
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

NXDL_NS = "http://definition.nexusformat.org/nxdl/3.1"
REPO = "XraySpectroscopy/nexus_definitions"
RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"
SEARCH_DIRS = ("contributed_definitions", "applications", "base_classes")

HERE = Path(__file__).resolve().parent
GLOSSARY = HERE.parent / "XAS_Glossary_SKOS.json"
# Production RML mapping -- the ground truth for which XDI-derived concept
# keys the converter actually consumes. It lives in a separate repository,
# so look for a checkout beside this one. $CDIF_XAS_RML overrides, and is
# honoured even when it points at nothing so the error can name it.
RML_CANDIDATES = (
    "cdif-xas-UKDS/resources/mapping_dds.ttl",
    "cdif-xas/resources/mapping_dds.ttl",
)


def find_rml_mapping() -> Path | None:
    """The production RML mapping, or None if no checkout is beside us."""
    override = os.environ.get("CDIF_XAS_RML")
    if override:
        return Path(override)
    for rel in RML_CANDIDATES:
        candidate = HERE.parent.parent / rel
        if candidate.is_file():
            return candidate
    return None

CURATOR = "https://orcid.org/0000-0001-6041-5302"   # S. M. Richard

# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------
# cdifxas: the concept hub. Minted under CDIF's own w3id namespace so the
#   URIs are stable and redirectable -- when an official NeXus concept
#   vocabulary exists, these can be redirected to it without breaking
#   anything already deployed.
# xdi:     XDI dictionary tokens. Minted under the same namespace for the
#   same reason; the XDI spec defines no IRIs.
# nxdl:    NeXus concept paths. PROVISIONAL. The NeXusOntology PURLs
#   (purl.org/nexusformat/definitions/) are dead -- domain never
#   registered, open issue #6 -- and an open PR renames every IRI, so they
#   cannot be used. These are minted under CDIF w3id on the same
#   mint-now-redirect-later basis. seeAlso in the metadata points at the
#   resolvable NeXus manual pages.
CURIE_MAP = {
    "cdifxas": "https://w3id.org/cdif/xas/",
    "xdi": "https://w3id.org/cdif/xdi/",
    "nxdl": "https://w3id.org/cdif/nxdl/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "semapv": "https://w3id.org/semapv/vocab/",
    "orcid": "https://orcid.org/",
}

E, C, B, N, R = (
    "skos:exactMatch", "skos:closeMatch", "skos:broadMatch",
    "skos:narrowMatch", "skos:relatedMatch",
)
MANUAL = "semapv:ManualMappingCuration"

# ---------------------------------------------------------------------------
# Mapping set 1: XDI token -> CDIF XAS concept
# ---------------------------------------------------------------------------
# Columns: xdi_token, rml_key (None if the token is a data column rather
#          than a header), cdif_concept, predicate, confidence, comment
#
# Note the deliberate split between XDI *header* tokens and XDI *data
# columns*. `Detector.I0` is a description of the detector; the `i0`
# column is the measured incident intensity. They are different things
# and get different predicates -- this precision is the reason to use
# SSSOM rather than a two-column lookup.
XDI_TO_CDIFXAS = [
    ("Element.symbol", "cdi:Element_symbol", "elementanalyzed", E, 1.0,
     "Absorbing element symbol."),
    ("Element.edge", "cdi:Element_edge", "edgeanalyzed", E, 1.0,
     "Absorption edge in IUPAC notation."),
    ("Scan.edge_energy", "cdi:Scan_edge_energy", "edgeenergy", E, 1.0,
     "Tabulated edge energy for the element/edge combination."),
    ("Mono.d_spacing", "cdi:Mono_d_spacing", "dspacing", E, 1.0,
     "Monochromator crystal d-spacing."),
    ("Mono.name", "cdi:Mono_name", "monochromatortype", C, 0.8,
     "XDI Mono.name conflates crystal material and reflection "
     "(e.g. 'Si(111)'); the CDIF concept is the material type alone."),
    ("Facility.name", "cdi:Facility_name", "facility", E, 1.0,
     "Name of the synchrotron facility."),
    ("Beamline.name", "cdi:Beamline_name", "beamline", E, 1.0,
     "Name of the beamline."),
    ("Facility.xray_source", None, "xraysourcetype", E, 1.0,
     "Insertion device or bending magnet type."),
    ("Beamline.xray_source", None, "xraysourcetype", E, 1.0,
     "Not a dictionary tag -- the dictionary defines Facility.xray_source "
     "-- but 118 of the 272 files in the XAS Data Library write it under "
     "Beamline and only 39 under Facility. Same concept either way."),
    ("Sample.prep", "cdi:Sample_prep", "samplepreparation", E, 1.0,
     "Free-text sample preparation description."),
    ("Sample.preparation", None, "samplepreparation", E, 1.0,
     "Not a dictionary tag -- the dictionary defines Sample.prep -- but "
     "files write it, and the value is the same free text. Without this "
     "row the description is silently dropped: xdl_CeO2.xdi's 'powder on "
     "tape' reached nothing. Same reasoning as Beamline.xray_source."),
    ("Sample.temperature", None, "temperature", E, 1.0,
     "Sample temperature during measurement."),
    ("Detector.I0", "cdi:Detector_I0", "incidentintensity", R, 0.7,
     "XDI Detector.I0 describes the detector hardware; the CDIF concept "
     "is the measured intensity it produces. Related, not equivalent -- "
     "the measured values come from the i0 data column."),
    ("Detector.I1", "cdi:Detector_I1", "transmittedintensity", R, 0.7,
     "As Detector.I0: describes hardware, not the measured values."),
    # Data columns -- these carry the measured arrays.
    ("Column.energy", None, "monochromatorenergy", E, 1.0,
     "Data column: incident photon energy."),
    ("Column.i0", None, "incidentintensity", E, 1.0,
     "Data column: incident beam intensity."),
    ("Column.itrans", None, "transmittedintensity", E, 1.0,
     "Data column: transmitted beam intensity."),
    ("Column.irefer", None, "referenceintensity", E, 1.0,
     "Data column: reference-channel intensity."),
    ("Column.mutrans", None, "absorptioncoefficient", E, 1.0,
     "Data column: mu(E)t = -ln(itrans/i0)."),
    ("Column.ifluor", None, "fluorescenceintensity", E, 1.0,
     "Data column: fluorescence intensity. Present in 32 of the 272 "
     "files in the XAS Data Library, and the only thing that "
     "distinguishes a fluorescence measurement from a transmission one, "
     "since XDI has no detection-mode field."),
    ("Column.mufluor", None, "fluorescenceabsorptioncoefficient", E, 1.0,
     "Data column: mu(E) derived from the fluorescence channel."),
    ("Column.murefer", None, "referenceabsorptioncoefficient", E, 1.0,
     "Data column: mu(E) derived from the reference channel."),
]

# ---------------------------------------------------------------------------
# Mapping set 2: CDIF XAS concept -> NeXus concept path
# ---------------------------------------------------------------------------
# Columns: cdif_concept, nexus_definition, nexus_path, predicate,
#          confidence, comment
#
# `nexus_path` is the path WITHIN the named definition, in NXDL
# name:NXclass form. Validation resolves the definition and confirms the
# terminal field exists.
#
# Paths are taken from base classes wherever the concept is a property of
# a kind of thing rather than a requirement of the technique -- an
# application definition says what a file MUST contain, a base class
# defines what a thing of that kind CAN have.
CDIFXAS_TO_NEXUS = [
    ("elementanalyzed", "NXxas", "/ENTRY:NXentry/element:NXelement/name",
     E, 1.0, "Element identity, first-class via the NXelement base class."),
    ("edgeanalyzed", "NXabsorption_edge", "/name", E, 1.0,
     "Edge name in IUPAC notation; 39-value enumeration imported as "
     "cdifxas:XAS_AbsorptionEdges."),
    ("edgeenergy", "NXabsorption_edge", "/energy", E, 1.0,
     "Edge energy (NX_ENERGY)."),
    ("monochromatorenergy", "NXxas_trans",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/monochromator:NXmonochromator/energy",
     E, 1.0, "Incident photon energy selected by the monochromator."),
    ("absorptioncoefficient", "NXxas_trans", "/ENTRY:NXentry/intensity",
     E, 1.0,
     "In NXxas_trans the entry-level intensity IS mu(E)t = -ln(I/I0), "
     "per the definition's own documentation."),
    ("incidentintensity", "NXxas_trans",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/i0:NXdetector/data", E, 1.0,
     "Per-channel detector group named i0."),
    ("transmittedintensity", "NXxas_trans",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/itrans:NXdetector/data", E, 1.0,
     "Per-channel detector group named itrans."),
    ("referenceintensity", "NXxas_trans",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/iref:NXdetector/data", E, 1.0,
     "Simultaneous reference channel. Note NXxas_trans ALSO defines a "
     "reference:NXsubentry for an independent reference spectrum -- a "
     "different concept that CDIF currently conflates with this one."),
    ("dspacing", "NXxas_trans",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/monochromator:NXmonochromator/"
     "crystal:NXcrystal/d_spacing", E, 1.0, "Crystal d-spacing (NX_LENGTH)."),
    ("monochromatortype", "NXxas_trans",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/monochromator:NXmonochromator/"
     "crystal:NXcrystal/type", E, 1.0, "Crystal material, e.g. Si, Ge."),
    ("monochromatorchemicalformula", "NXcrystal", "/chemical_formula",
     E, 1.0,
     "Base class: NXcrystal/chemical_formula is the crystal's CIF formula "
     "wherever an NXcrystal appears. Distinct from monochromatortype, "
     "which is NXcrystal/type -- the Athena/GSECARS files write the "
     "formula and omit the type, and were previously being read into "
     "monochromatortype through the legacy table, which said 'crystal "
     "material rather than a monochromator type' in its own comment."),
    ("reflectionplane", "NXxas_trans",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/monochromator:NXmonochromator/"
     "crystal:NXcrystal/reflection", E, 1.0, "Miller indices hkl (NX_INT[3])."),
    ("facility", "NXsource", "/name", E, 1.0,
     "Base class, not the application definition -- NXsource/name is the "
     "facility name wherever an NXsource appears."),
    ("xraysourcetype", "NXsource", "/type", E, 1.0,
     "Base class. Insertion device / bending magnet type."),
    ("probe", "NXsource", "/probe", E, 1.0,
     "Base class. Enumerated; x-ray for XAS."),
    ("beamline", "NXinstrument", "/name", E, 1.0,
     "Base class. NXinstrument/name is the beamline name."),
    ("temperature", "NXsample", "/temperature", E, 1.0,
     "Base class (NX_TEMPERATURE)."),
    ("sampledescription", "NXsample", "/description", E, 1.0,
     "Free-text description of the sample. samplepreparation used to "
     "claim this field as a closeMatch for want of anywhere better; it "
     "no longer does, since one field mapping into two concepts would "
     "write the same value twice. NeXus has no preparation field at all "
     "-- NXsample/preparation_date covers only the date -- so "
     "samplepreparation has no NeXus row and reaches CDIF through the "
     "XDI binding alone."),
    ("calculated", "NXxas", "/ENTRY:NXentry/is_experimental", R, 1.0,
     "INVERTED POLARITY -- is_experimental is the negation of calculated. "
     "Deliberately relatedMatch, never exactMatch; a converter must flip "
     "the boolean."),
    ("xasmeasurementmode", "NXxas_trans", "", N, 1.0,
     "In the restructured NXxas family the detection mode IS the "
     "application definition, so the definition itself is a narrower "
     "term of the mode concept rather than a field within it. Value list "
     "imported as cdifxas:XAS_DetectionModes."),

    # -----------------------------------------------------------------------
    # Total electron yield -- NXxas_tey
    # -----------------------------------------------------------------------
    ("xasmeasurementmode", "NXxas_tey", "", N, 1.0,
     "Detection mode as application definition."),
    ("electronyieldintensity", "NXxas_tey",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/iey:NXdetector/data", E, 1.0,
     "Drain current / total electron current."),
    ("electronyieldabsorptioncoefficient", "NXxas_tey",
     "/ENTRY:NXentry/intensity", E, 1.0,
     "Entry-level intensity in TEY is the absorption coefficient derived "
     "from electron yield, not a raw count."),
    ("incidentintensity", "NXxas_tey",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/i0:NXdetector/data", E, 1.0,
     "Incident beam intensity; same concept across all modes."),

    # -----------------------------------------------------------------------
    # Total fluorescence yield -- NXxas_tfy
    # -----------------------------------------------------------------------
    ("xasmeasurementmode", "NXxas_tfy", "", N, 1.0,
     "Detection mode as application definition."),
    ("fluorescenceintensity", "NXxas_tfy",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/ifluor:NXdetector/data", E, 1.0,
     "Total fluorescence intensity."),
    ("fluorescenceabsorptioncoefficient", "NXxas_tfy",
     "/ENTRY:NXentry/intensity", E, 1.0,
     "Entry-level intensity in TFY is mu(E) proportional to If/I0, per "
     "the definition's documentation."),
    ("incidentintensity", "NXxas_tfy",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/i0:NXdetector/data", E, 1.0,
     "Incident beam intensity."),

    # -----------------------------------------------------------------------
    # Partial electron yield -- NXxas_pey
    # -----------------------------------------------------------------------
    ("xasmeasurementmode", "NXxas_pey", "", N, 1.0,
     "Detection mode as application definition."),
    ("electronyieldintensity", "NXxas_pey",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/iey:NXdetector/data", E, 1.0,
     "Electron yield above the kinetic-energy threshold."),
    ("retardingvoltage", "NXxas_pey",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/iey:NXdetector/retarding_voltage",
     E, 1.0,
     "Bias selecting electrons above a kinetic energy threshold. The "
     "distinguishing parameter of PEY versus TEY."),
    ("incidentintensity", "NXxas_pey",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/i0:NXdetector/data", E, 1.0,
     "Incident beam intensity."),

    # -----------------------------------------------------------------------
    # Partial fluorescence yield -- NXxas_pfy
    # -----------------------------------------------------------------------
    ("xasmeasurementmode", "NXxas_pfy", "", N, 1.0,
     "Detection mode as application definition."),
    ("emissionline", "NXxas_pfy",
     "/ENTRY:NXentry/LINE_emission_line:NXemission_line/name", E, 1.0,
     "Selected emission line; 432-value enumeration imported as "
     "cdifxas:XAS_EmissionLines."),
    ("emissionenergywindow", "NXxas_pfy",
     "/ENTRY:NXentry/emission_energy_window", E, 1.0,
     "Lower and upper bounds of the accepted emission energy range."),
    ("fluorescenceintensity", "NXxas_pfy",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/ifluor:NXdetector/data", E, 1.0,
     "Fluorescence intensity within the selected window."),
    ("deadtime", "NXxas_pfy",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/ifluor:NXdetector/dead_time",
     E, 1.0, "Detector dead time per energy point."),
    ("counttime", "NXxas_pfy",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/ifluor:NXdetector/count_time",
     E, 1.0, "Detector live time per energy point."),
    ("incidentintensity", "NXxas_pfy",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/i0:NXdetector/data", E, 1.0,
     "Incident beam intensity."),

    # -----------------------------------------------------------------------
    # High energy resolution fluorescence detected -- NXxas_herfd
    # -----------------------------------------------------------------------
    ("xasmeasurementmode", "NXxas_herfd", "", N, 1.0,
     "Detection mode as application definition."),
    ("emissionline", "NXxas_herfd",
     "/ENTRY:NXentry/emission_line:NXemission_line/name", E, 1.0,
     "Selected emission line. Note the group name differs from "
     "NXxas_pfy's LINE_emission_line -- a parser must not assume one "
     "spelling."),
    ("emissionenergy", "NXxas_herfd", "/ENTRY:NXentry/emission_energy",
     E, 1.0, "Emission energy the spectrometer is set to."),
    ("analyzercrystal", "NXxas_herfd",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/analyzerCRYSTAL:NXcrystal",
     E, 1.0,
     "The energy-analyzing crystal, distinct from the monochromator "
     "crystal that selects incident energy."),
    ("braggangle", "NXxas_herfd",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/analyzerCRYSTAL:NXcrystal/"
     "bragg_angle", E, 1.0, "Bragg angle of the nominal reflection."),
    ("bendingradius", "NXxas_herfd",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/analyzerCRYSTAL:NXcrystal/"
     "bending_radius", E, 1.0,
     "Bending radius; twice the Rowland radius in Johann geometry."),
    ("rowlandradius", "NXxas_herfd",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/analyzerCRYSTAL:NXcrystal/"
     "rowland_radius", E, 1.0, "Radius of the Rowland circle."),
    ("analyzergeometry", "NXxas_herfd",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/analyzerCRYSTAL:NXcrystal/"
     "geometry_type", E, 1.0, "Johann or Johansson."),
    ("analyzerdiameter", "NXxas_herfd",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/analyzerCRYSTAL:NXcrystal/"
     "diameter", E, 1.0, "Crystal analyzer wafer diameter."),
    ("energyresolution", "NXxas_herfd",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/analyzerCRYSTAL:NXcrystal/"
     "energy_resolution", E, 1.0,
     "Energy bandwidth of the crystal analyzer. Existing CDIF concept -- "
     "in HERFD it is a property of the analyzer, not the monochromator."),
    ("fluorescenceintensity", "NXxas_herfd",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/ifluor:NXdetector/data", E, 1.0,
     "Fluorescence intensity at the selected emission energy."),
    ("incidentintensity", "NXxas_herfd",
     "/ENTRY:NXentry/INSTRUMENT:NXinstrument/i0:NXdetector/data", E, 1.0,
     "Incident beam intensity."),

    # -----------------------------------------------------------------------
    # Mode-independent, from the NXxas base
    # -----------------------------------------------------------------------
    ("intensityuncertainty", "NXxas", "/ENTRY:NXentry/intensity_errors",
     E, 1.0, "Errors on the spectrum intensity; defined on the base."),
]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def iter_concepts(doc):
    """Yield every skos:Concept in a rooted CDIF concept scheme document."""
    stack = list(doc.get("skos:hasTopConcept", []))
    while stack:
        node = stack.pop()
        yield node
        stack.extend(node.get("skos:narrower", []))


def load_glossary_concepts() -> set[str]:
    d = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    return {n["@id"].rsplit("/", 1)[-1] for n in iter_concepts(d)}


def load_rml_keys() -> tuple[Path | None, set[str] | None]:
    """Concept keys the production RML mapping actually reads.

    Returns the path looked at (None if no candidate exists) and the keys
    (None if it could not be read), so the caller can say what is wrong.
    """
    path = find_rml_mapping()
    if path is None or not path.is_file():
        return path, None
    import re
    txt = path.read_text(encoding="utf-8", errors="replace")
    return path, set(re.findall(r"\$\['(cdi:[A-Za-z_0-9]+)'\]", txt))


_nxdl_cache: dict[str, ET.Element | None] = {}


def load_nxdl(name: str, ref: str) -> ET.Element | None:
    if name in _nxdl_cache:
        return _nxdl_cache[name]
    root = None
    for d in SEARCH_DIRS:
        url = RAW.format(repo=REPO, ref=ref, path=f"{d}/{name}.nxdl.xml")
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                root = ET.fromstring(r.read().decode("utf-8"))
            break
        except Exception:
            continue
    _nxdl_cache[name] = root
    return root


def nxdl_has_field(root: ET.Element, path: str) -> bool:
    """Confirm the terminal field of a name:NXclass path exists.

    Deliberately checks only the leaf name rather than walking the full
    path: the XAS definitions are being revised and intermediate group
    nesting shifts. A missing leaf is a real break; a moved intermediate
    is noise.
    """
    if not path:
        return True   # definition-level mapping, no field to check
    leaf = path.rstrip("/").rsplit("/", 1)[-1]
    if ":" in leaf:
        return True   # terminal is a group, not a field
    return any(
        f.get("name") == leaf
        for f in root.iter(f"{{{NXDL_NS}}}field")
    )


def validate(ref: str, rml_check: bool = True) -> list[str]:
    problems: list[str] = []

    concepts = load_glossary_concepts()
    print(f"  glossary: {len(concepts)} concepts")

    rml_keys = None
    if not rml_check:
        print("  RML mapping: check disabled (--no-rml-check)")
    else:
        rml_path, rml_keys = load_rml_keys()
        if rml_keys is None:
            where = (f"{rml_path}" if rml_path is not None
                     else " or ".join(RML_CANDIDATES)
                     + f" beside {HERE.parent}")
            problems.append(
                f"RML mapping not readable at {where} -- the XDI key check "
                f"cannot run. Check out smrgeoinfo/cdif-xas beside this "
                f"repository, set $CDIF_XAS_RML, or pass --no-rml-check to "
                f"build without the check.")
        else:
            print(f"  RML mapping: {len(rml_keys)} concept keys "
                  f"({rml_path})")

    # Set 1
    for token, rml_key, concept, *_ in XDI_TO_CDIFXAS:
        if concept not in concepts:
            problems.append(
                f"XDI->CDIF: object cdifxas:{concept} not in glossary "
                f"(subject xdi:{token})")
        if rml_key and rml_keys is not None and rml_key not in rml_keys:
            problems.append(
                f"XDI->CDIF: {rml_key} is not read by mapping_dds.ttl "
                f"(subject xdi:{token}) -- alignment has drifted from "
                f"the converter")

    # Set 2
    for concept, defn, path, *_ in CDIFXAS_TO_NEXUS:
        if concept not in concepts:
            problems.append(
                f"CDIF->NeXus: subject cdifxas:{concept} not in glossary")
        root = load_nxdl(defn, ref)
        if root is None:
            problems.append(
                f"CDIF->NeXus: NXDL {defn} not found in any of "
                f"{SEARCH_DIRS} at {REPO}@{ref}")
            continue
        if not nxdl_has_field(root, path):
            leaf = path.rstrip('/').rsplit('/', 1)[-1]
            problems.append(
                f"CDIF->NeXus: field '{leaf}' not found in {defn} "
                f"(cdifxas:{concept}) -- the definition may have changed")

    return problems


# ---------------------------------------------------------------------------
# Emit
# ---------------------------------------------------------------------------

SSSOM_COLS = [
    "subject_id", "subject_label", "predicate_id", "object_id",
    "object_label", "mapping_justification", "confidence", "author_id",
    "comment",
]


def yaml_header(meta: dict) -> str:
    lines = []
    for k, v in meta.items():
        if isinstance(v, dict):
            lines.append(f"# {k}:")
            for kk, vv in v.items():
                lines.append(f"#   {kk}: {vv}")
        elif isinstance(v, list):
            lines.append(f"# {k}:")
            for item in v:
                lines.append(f"#   - {item}")
        else:
            lines.append(f"# {k}: {v}")
    return "\n".join(lines) + "\n"


def write_set(path: Path, meta: dict, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(yaml_header(meta))
        w = csv.DictWriter(f, fieldnames=SSSOM_COLS, delimiter="\t",
                           extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def build_xdi_set(ref: str) -> tuple[dict, list[dict]]:
    rows = []
    for token, rml_key, concept, pred, conf, comment in XDI_TO_CDIFXAS:
        note = comment
        if rml_key:
            note += f" [converter key: {rml_key}]"
        rows.append({
            "subject_id": f"xdi:{token}",
            "subject_label": token,
            "predicate_id": pred,
            "object_id": f"cdifxas:{concept}",
            "object_label": concept,
            "mapping_justification": MANUAL,
            "confidence": conf,
            "author_id": f"orcid:{CURATOR.rsplit('/', 1)[-1]}",
            "comment": note,
        })
    meta = {
        "mapping_set_id": "https://w3id.org/cdif/xas/crosswalk/xdi-to-cdifxas",
        "mapping_set_title":
            "XDI dictionary terms to CDIF XAS concepts (all detection modes)",
        "mapping_set_description":
            "One of two bindings onto the CDIF XAS concept hub. Subject "
            "IRIs are minted under CDIF w3id because the XDI specification "
            "defines none. Scope is the transmission slice.",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "mapping_provider": "https://github.com/smrgeoinfo/XAS-CDIF",
        "creator_id": [f"orcid:{CURATOR.rsplit('/', 1)[-1]}"],
        "mapping_tool": "crosswalk/build_crosswalk.py",
        "subject_source": "XDI/1.0 dictionary",
        "object_source": "https://w3id.org/cdif/xas/",
        "curie_map": CURIE_MAP,
    }
    return meta, rows


def build_nexus_set(ref: str) -> tuple[dict, list[dict]]:
    rows = []
    for concept, defn, path, pred, conf, comment in CDIFXAS_TO_NEXUS:
        obj = f"nxdl:{defn}{path}" if path else f"nxdl:{defn}"
        rows.append({
            "subject_id": f"cdifxas:{concept}",
            "subject_label": concept,
            "predicate_id": pred,
            "object_id": obj,
            "object_label": path.rstrip("/").rsplit("/", 1)[-1] or defn,
            "mapping_justification": MANUAL,
            "confidence": conf,
            "author_id": f"orcid:{CURATOR.rsplit('/', 1)[-1]}",
            "comment": comment,
        })
    meta = {
        "mapping_set_id":
            "https://w3id.org/cdif/xas/crosswalk/cdifxas-to-nexus",
        "mapping_set_title":
            "CDIF XAS concepts to NeXus concept paths (all detection modes)",
        "mapping_set_description":
            "One of two bindings onto the CDIF XAS concept hub. Object "
            "IRIs are PROVISIONAL: the NeXusOntology PURLs do not resolve "
            "(domain unregistered) and an open PR renames every IRI, so "
            "paths are minted under CDIF w3id on a mint-now, "
            "redirect-later basis. Mappings target NeXus BASE classes "
            "wherever the concept is a property of a kind of thing rather "
            "than a requirement of the technique.",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "mapping_provider": "https://github.com/smrgeoinfo/XAS-CDIF",
        "creator_id": [f"orcid:{CURATOR.rsplit('/', 1)[-1]}"],
        "mapping_tool": "crosswalk/build_crosswalk.py",
        "subject_source": "https://w3id.org/cdif/xas/",
        "object_source": f"https://github.com/{REPO}@{ref}",
        "object_source_note":
            "Resolvable documentation: "
            "https://manual.nexusformat.org/classes/",
        "curie_map": CURIE_MAP,
    }
    return meta, rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ref", default="main",
                    help="git ref in the NeXus definitions repo")
    ap.add_argument("--check", action="store_true",
                    help="validate only, write nothing")
    ap.add_argument("--no-validate", action="store_true",
                    help="write without checking against source vocabularies")
    ap.add_argument("--no-rml-check", action="store_true",
                    help="skip the XDI-key-against-mapping_dds.ttl check, "
                         "for when no cdif-xas checkout is available")
    args = ap.parse_args(argv)

    print(f"CDIF XAS crosswalk -- all six detection modes")
    print(f"NeXus definitions: {REPO}@{args.ref}\n")

    problems: list[str] = []
    if not args.no_validate:
        print("Validating against source vocabularies:")
        problems = validate(args.ref, rml_check=not args.no_rml_check)
        if problems:
            print(f"\n{len(problems)} problem(s):")
            for p in problems:
                print(f"  ! {p}")
        else:
            print("  all subjects and objects resolve\n")

    if args.check:
        return 1 if problems else 0

    meta1, rows1 = build_xdi_set(args.ref)
    meta2, rows2 = build_nexus_set(args.ref)
    write_set(HERE / "xdi-to-cdifxas.sssom.tsv", meta1, rows1)
    write_set(HERE / "cdifxas-to-nexus.sssom.tsv", meta2, rows2)
    print(f"  wrote xdi-to-cdifxas.sssom.tsv     ({len(rows1)} mappings)")
    print(f"  wrote cdifxas-to-nexus.sssom.tsv   ({len(rows2)} mappings)")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
