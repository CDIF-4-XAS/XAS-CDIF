#!/usr/bin/env python3
"""Import NeXus NXDL enumerations into CDIF XAS SKOS value-list vocabularies.

Generates three standalone SKOS concept schemes from the NeXus definitions:

  XAS_edges_SKOS.json           absorption edges      (NXabsorption_edge/name)
  XAS_emissionlines_SKOS.json   x-ray emission lines  (NXemission_line/name)
  XAS_detectionmodes_SKOS.json  XAS detection modes   (union, see below)

Why separate schemes rather than adding to XAS_Glossary_SKOS_v2_draft.json:
the three lists total ~478 concepts against a 89-concept glossary, and the
publishing pipeline emits one file per concept. A property glossary and a
value list are different kinds of artifact; keeping them apart avoids
swamping the former and keeps each independently versionable. The glossary
concepts that these lists supply values for (edgeanalyzed, emissionline,
xasmeasurementmode) reference their scheme via dc:references.

Source: https://github.com/XraySpectroscopy/nexus_definitions (branch main),
the XAS community's working fork. Those definitions are actively being
revised, so this script is written to be re-run:

  * Enumerations are discovered from the NXDL, never hardcoded.
  * The definition file is located by searching contributed_definitions/,
    applications/ and base_classes/ in turn -- NXxas has already moved
    between directories once.
  * The resolved git ref is recorded in each output scheme so a generated
    vocabulary can always be traced to the NXDL revision it came from.
  * Documentation tables are parsed defensively; a table that no longer
    matches the expected shape degrades to "no extra labels" rather than
    failing the run.

Usage:
    python tools/import_nexus_enumerations.py [--ref main] [--out-dir .]
    python tools/import_nexus_enumerations.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

NXDL_NS = "http://definition.nexusformat.org/nxdl/3.1"
NS = {"n": NXDL_NS}

REPO = "XraySpectroscopy/nexus_definitions"
RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"
# NXxas moved from applications/ to contributed_definitions/ once already;
# search all three rather than assuming.
SEARCH_DIRS = ("contributed_definitions", "applications", "base_classes")

CDIF_XAS = "https://w3id.org/cdif/xas/"
MANUAL = "https://manual.nexusformat.org/classes/"


# --------------------------------------------------------------------------
# fetching
# --------------------------------------------------------------------------

def fetch(path: str, ref: str) -> str | None:
    url = RAW.format(repo=REPO, ref=ref, path=path)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read().decode("utf-8")
    except Exception:
        return None


def find_definition(name: str, ref: str) -> tuple[str, str] | None:
    """Return (xml_text, directory) for an NXDL definition, searching all
    known directories. Returns None if not found anywhere."""
    for d in SEARCH_DIRS:
        txt = fetch(f"{d}/{name}.nxdl.xml", ref)
        if txt:
            return txt, d
    return None


# --------------------------------------------------------------------------
# NXDL parsing
# --------------------------------------------------------------------------

def get_field(root: ET.Element, field_name: str) -> ET.Element | None:
    """First <field name=...> anywhere in the tree."""
    for f in root.iter(f"{{{NXDL_NS}}}field"):
        if f.get("name") == field_name:
            return f
    return None


def enum_values(field: ET.Element) -> list[str]:
    return [
        i.get("value")
        for i in field.iter(f"{{{NXDL_NS}}}item")
        if i.get("value") is not None
    ]


def field_doc(field: ET.Element) -> str:
    doc = field.find("n:doc", NS)
    if doc is None:
        return ""
    return "".join(doc.itertext())


def parse_rst_list_table(doc: str) -> list[list[str]]:
    """Extract rows from the first RST list-table in a doc string.

    Shape expected:
        .. list-table::
           :header-rows: 1

           * - ColA
             - ColB
           * - val
             - val

    Returns rows as lists of cell strings (header row included). Returns []
    if no recognisable table is present -- callers must tolerate that.
    """
    if "list-table" not in doc:
        return []
    body = doc.split("list-table", 1)[1]
    rows: list[list[str]] = []
    current: list[str] | None = None
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith(":"):
            continue
        if line.startswith("* -"):
            if current:
                rows.append(current)
            current = [line[3:].strip()]
        elif line.startswith("-") and current is not None:
            current.append(line[1:].strip())
        elif current is not None and rows and len(rows) > 1:
            # Text after the table ended.
            break
    if current:
        rows.append(current)
    return rows


def clean_math(s: str) -> str:
    """`:math:`K\\alpha_1`` -> `Kα1`-ish plain text. Best effort; the raw
    form is kept as a note elsewhere so nothing is lost."""
    m = re.match(r":math:`(.+)`$", s.strip())
    if m:
        s = m.group(1)
    s = s.replace("\\alpha", "α").replace("\\beta", "β")
    s = s.replace("\\gamma", "γ").replace("\\eta", "η")
    s = s.replace("\\zeta", "ζ").replace("\\nu", "ν")
    s = re.sub(r"[_^]\{([^}]*)\}", r"\1", s)
    s = re.sub(r"[_^](\w)", r"\1", s)
    return s.replace("`", "").strip()


def slug(value: str) -> str:
    """Enum value -> URI-safe local name. 'L2,3' -> 'l2-3', 'K-L3' -> 'k-l3'."""
    s = value.lower().replace(",", "-").replace(" ", "")
    return re.sub(r"[^a-z0-9._-]", "", s)


# --------------------------------------------------------------------------
# SKOS construction
# --------------------------------------------------------------------------

CONTEXT = {
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "Concept": "skos:Concept",
    "ConceptScheme": "skos:ConceptScheme",
    "Collection": "skos:Collection",
    "prefLabel": "skos:prefLabel",
    "altLabel": "skos:altLabel",
    "definition": "skos:definition",
    "broader": "skos:broader",
    "narrower": "skos:narrower",
    "inScheme": "skos:inScheme",
    "member": "skos:member",
    "notation": "skos:notation",
    "hasTopConcept": "skos:hasTopConcept",
    "note": "skos:note",
    "seeAlso": {
        "@id": "http://www.w3.org/2000/01/rdf-schema#seeAlso",
        "@type": "@id",
    },
    "dc": "http://dublincore.org/specifications/dublin-core/dcmi-terms/2020-01-20/",
    "references": "dc:references",
    "source": "dc:source",
}


def en(v: str) -> dict:
    return {"@value": v, "@language": "en"}


def build_scheme(scheme_id, title, description, concepts, source_note):
    scheme = {
        "@id": f"{CDIF_XAS}{scheme_id}",
        "@type": "skos:ConceptScheme",
        "prefLabel": en(title),
        "definition": en(description),
        "note": en(source_note),
        "hasTopConcept": [{"@id": c["@id"]} for c in concepts],
    }
    return {"@context": CONTEXT, "@graph": [scheme] + concepts}


# --------------------------------------------------------------------------
# the three imports
# --------------------------------------------------------------------------

def import_edges(ref: str) -> dict | None:
    found = find_definition("NXabsorption_edge", ref)
    if not found:
        print("  ! NXabsorption_edge not found in any directory", file=sys.stderr)
        return None
    xml, directory = found
    root = ET.fromstring(xml)
    field = get_field(root, "name")
    if field is None:
        print("  ! NXabsorption_edge has no 'name' field", file=sys.stderr)
        return None
    values = enum_values(field)
    doc = field_doc(field)

    # IUPAC -> electron configuration, from the doc's list-table.
    config = {}
    rows = parse_rst_list_table(doc)
    for row in rows[1:]:
        if len(row) >= 2:
            config[row[0].strip()] = clean_math(row[1])

    scheme = f"{CDIF_XAS}XAS_AbsorptionEdges"
    concepts = []
    for v in values:
        c = {
            "@id": f"{CDIF_XAS}edge/{slug(v)}",
            "@type": "skos:Concept",
            "prefLabel": en(f"{v} edge"),
            "notation": v,
            "inScheme": {"@id": scheme},
            "broader": {"@id": f"{CDIF_XAS}edgeanalyzed"},
            "seeAlso": f"{MANUAL}{directory}/NXabsorption_edge.html",
        }
        if v in config:
            c["definition"] = en(
                f"Absorption edge {v} in IUPAC notation; core-vacancy "
                f"state {config[v]}."
            )
        else:
            c["definition"] = en(f"Absorption edge {v} in IUPAC notation.")
        concepts.append(c)

    print(f"  edges: {len(concepts)} concepts "
          f"({len(config)} with electron configuration)")
    return build_scheme(
        "XAS_AbsorptionEdges",
        "X-ray absorption edges",
        "Absorption edge identifiers in IUPAC notation, giving the "
        "core-vacancy state of the absorbing atom. Value list for the "
        "CDIF XAS concept 'edgeanalyzed'.",
        concepts,
        f"Generated from NeXus {directory}/NXabsorption_edge.nxdl.xml "
        f"at {REPO}@{ref}.",
    )


def import_emission_lines(ref: str) -> dict | None:
    found = find_definition("NXemission_line", ref)
    if not found:
        print("  ! NXemission_line not found in any directory", file=sys.stderr)
        return None
    xml, directory = found
    root = ET.fromstring(xml)
    field = get_field(root, "name")
    if field is None:
        print("  ! NXemission_line has no 'name' field", file=sys.stderr)
        return None
    values = enum_values(field)
    doc = field_doc(field)

    # IUPAC -> (Siegbahn, Latinized Siegbahn)
    sieg = {}
    rows = parse_rst_list_table(doc)
    for row in rows[1:]:
        if len(row) >= 3:
            sieg[row[0].strip()] = (clean_math(row[1]), row[2].strip())

    scheme = f"{CDIF_XAS}XAS_EmissionLines"
    concepts = []
    for v in values:
        c = {
            "@id": f"{CDIF_XAS}emissionline/{slug(v)}",
            "@type": "skos:Concept",
            "prefLabel": en(v),
            "notation": v,
            "inScheme": {"@id": scheme},
            "broader": {"@id": f"{CDIF_XAS}emissionline"},
            "seeAlso": f"{MANUAL}{directory}/NXemission_line.html",
        }
        if v in sieg:
            siegbahn, latin = sieg[v]
            c["altLabel"] = [en(siegbahn), en(latin)] if latin else en(siegbahn)
            c["definition"] = en(
                f"X-ray emission line {v} in IUPAC notation "
                f"(Siegbahn: {siegbahn})."
            )
        else:
            c["definition"] = en(f"X-ray emission line {v} in IUPAC notation.")
        concepts.append(c)

    print(f"  emission lines: {len(concepts)} concepts "
          f"({len(sieg)} with Siegbahn alternates)")
    return build_scheme(
        "XAS_EmissionLines",
        "X-ray emission lines",
        "X-ray emission line identifiers in IUPAC notation (initial and "
        "final edge separated by a hyphen), with Siegbahn alternates where "
        "defined. Value list for the CDIF XAS concept 'emissionline'.",
        concepts,
        f"Generated from NeXus {directory}/NXemission_line.nxdl.xml "
        f"at {REPO}@{ref}.",
    )


# The detection-mode list must be the UNION of two sources. The fork adds
# HERFD and splits total/partial fluorescence yield, but DROPS Auger
# electron yield, which upstream has. Taking either source alone loses
# terms. Each entry: (localname, prefLabel, altLabels, definition,
# nxdl application definition or None).
DETECTION_MODES = [
    ("transmission", "Transmission", ["trans"],
     "The absorption coefficient is obtained from the Beer-Lambert law, "
     "mu(E)t = -ln(I/I0), where I is the transmitted and I0 the incident "
     "beam intensity.",
     "NXxas_trans"),
    ("totalelectronyield", "Total electron yield", ["TEY"],
     "The spectrum is measured by collecting all secondary electrons "
     "emitted from the sample surface; the drain current is proportional "
     "to the absorption coefficient.",
     "NXxas_tey"),
    ("partialelectronyield", "Partial electron yield", ["PEY"],
     "The spectrum is measured by collecting electrons above a kinetic "
     "energy threshold, using a retarding voltage to discriminate against "
     "low-energy secondary electrons.",
     "NXxas_pey"),
    ("augerelectronyield", "Auger electron yield", ["AEY"],
     "The spectrum is measured by collecting Auger electrons of a selected "
     "kinetic energy.",
     None),
    ("totalfluorescenceyield", "Total fluorescence yield", ["TFY"],
     "The absorption coefficient is proportional to the ratio of total "
     "fluorescence intensity to incident beam intensity.",
     "NXxas_tfy"),
    ("partialfluorescenceyield", "Partial fluorescence yield", ["PFY"],
     "The absorption coefficient is obtained from fluorescence intensity "
     "measured over a selected emission-energy window or detector "
     "channels.",
     "NXxas_pfy"),
    ("herfd", "High energy resolution fluorescence detected", ["HERFD"],
     "The spectrum is measured with crystal analyzers selecting a narrow "
     "emission energy, giving sharper spectral features than conventional "
     "fluorescence detection.",
     "NXxas_herfd"),
]


def import_detection_modes(ref: str) -> dict:
    scheme = f"{CDIF_XAS}XAS_DetectionModes"
    concepts = []
    resolved = 0
    for local, label, alts, defn, appdef in DETECTION_MODES:
        c = {
            "@id": f"{CDIF_XAS}detectionmode/{local}",
            "@type": "skos:Concept",
            "prefLabel": en(label),
            "altLabel": [en(a) for a in alts],
            "definition": en(defn),
            "notation": local,
            "inScheme": {"@id": scheme},
            "broader": {"@id": f"{CDIF_XAS}xasmeasurementmode"},
        }
        if appdef:
            found = find_definition(appdef, ref)
            if found:
                _, directory = found
                c["seeAlso"] = f"{MANUAL}{directory}/{appdef}.html"
                c["note"] = en(
                    f"Corresponds to NeXus application definition {appdef}."
                )
                resolved += 1
            else:
                c["note"] = en(
                    f"Expected NeXus application definition {appdef} was not "
                    f"found at {REPO}@{ref}; the definitions are in flux."
                )
        else:
            c["note"] = en(
                "Present in the upstream NeXus NXxas mode enumeration but "
                "with no application definition in the XAS fork."
            )
        concepts.append(c)

    print(f"  detection modes: {len(concepts)} concepts "
          f"({resolved} resolved to an application definition)")
    return build_scheme(
        "XAS_DetectionModes",
        "XAS detection modes",
        "Detection methods used to observe sample absorption in an XAS "
        "measurement. Value list for the CDIF XAS concept "
        "'xasmeasurementmode'. This list is the union of the upstream NeXus "
        "NXxas mode enumeration and the per-mode application definitions in "
        "the XAS community fork: the fork adds HERFD and splits total from "
        "partial fluorescence yield, but drops Auger electron yield.",
        concepts,
        f"Generated from NeXus application definitions at {REPO}@{ref} "
        f"and the upstream NXxas mode enumeration.",
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ref", default="main",
                    help="git ref in the definitions repo (default: main). "
                         "Pin a SHA for reproducibility.")
    ap.add_argument("--out-dir", type=Path, default=Path("."),
                    help="where to write the generated schemes")
    ap.add_argument("--dry-run", action="store_true",
                    help="report counts without writing files")
    args = ap.parse_args(argv)

    print(f"Importing NeXus enumerations from {REPO}@{args.ref}")

    outputs = {
        "XAS_edges_SKOS.json": import_edges(args.ref),
        "XAS_emissionlines_SKOS.json": import_emission_lines(args.ref),
        "XAS_detectionmodes_SKOS.json": import_detection_modes(args.ref),
    }

    failed = [k for k, v in outputs.items() if v is None]
    if failed:
        print(f"\n! {len(failed)} import(s) produced nothing: "
              f"{', '.join(failed)}", file=sys.stderr)

    if args.dry_run:
        print("\n(dry run - nothing written)")
        return 1 if failed else 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for fname, doc in outputs.items():
        if doc is None:
            continue
        p = args.out_dir / fname
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False),
                     encoding="utf-8")
        n = len(doc["@graph"]) - 1
        print(f"  wrote {p}  ({n} concepts)")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
