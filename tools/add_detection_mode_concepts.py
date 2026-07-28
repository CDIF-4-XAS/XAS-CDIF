#!/usr/bin/env python3
"""Add XAS detection-mode concepts to the CDIF XAS glossary.

Item 2 of the recommendations in XAS_Glossary_vs_NeXus_analysis.md. The
glossary was written against transmission-mode XAS (largely XDI-derived)
and has no vocabulary for the electron-yield, partial-fluorescence-yield
or HERFD modes that the restructured NeXus NXxas family now defines.

Fourteen concepts are added. Definitions are grounded in the NXDL <doc>
text of the corresponding fields rather than invented -- see the
`source` note on each -- so the glossary and NeXus stay saying the same
thing.

Deliberately NOT added: the geometry and transformation plumbing that
NXxas_pfy and NXxas_herfd carry (NXcoordinate_system directions,
depends_on chains, NXtransformations offsets). That is NeXus file-layout
mechanics, not discovery-level semantics, and importing it would put
dozens of non-concepts into a glossary meant for discovery.

Idempotent: re-running skips concepts already present.

Usage:
    python tools/add_detection_mode_concepts.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

GLOSSARY = Path(__file__).resolve().parent.parent / "XAS_Glossary_SKOS.json"
CDIF = "https://w3id.org/cdif/xas/"
SCHEME = CDIF + "CDIF4XAS_Reference_Concepts"
MANUAL = "https://manual.nexusformat.org/classes/contributed_definitions/"

# (localname, prefLabel, definition, notation|None, broader|None, nxdl source)
CONCEPTS = [
    # --- measured signal, electron-yield modes -----------------------------
    ("electronyieldintensity", "Electron yield intensity",
     "Intensity measured as the drain current or total electron current "
     "from electrons emitted by the sample surface, used to derive the "
     "absorption coefficient in electron-yield detection.",
     "iey", None, "NXxas_tey.html"),
    ("electronyieldabsorptioncoefficient",
     "Electron yield absorption coefficient",
     "Absorption coefficient derived from electron yield, proportional to "
     "the ratio of the electron yield intensity and the incident beam "
     "intensity.",
     None, "absorptioncoefficient", "NXxas_tey.html"),
    ("retardingvoltage", "Retarding voltage",
     "Retarding voltage (bias) applied to select electrons above a kinetic "
     "energy threshold, discriminating against low-energy secondary "
     "electrons in partial electron yield detection.",
     None, None, "NXxas_pey.html"),

    # --- emission selection, PFY / HERFD ------------------------------------
    ("emissionenergy", "Emission energy",
     "Emission energy at which the spectrometer is set in high energy "
     "resolution fluorescence detected measurement.",
     None, None, "NXxas_herfd.html"),
    ("emissionenergywindow", "Emission energy window",
     "Lower and upper bounds of the detected emission energy window: the "
     "energy range over which fluorescence photons are accepted, whether "
     "defined by a detector channel range or a spectrometer region of "
     "interest.",
     None, None, "NXxas_pfy.html"),

    # --- crystal analyzer, HERFD -------------------------------------------
    ("analyzercrystal", "Analyzer crystal",
     "Crystal used to energy-analyze emitted fluorescence in high energy "
     "resolution fluorescence detected measurement, distinct from the "
     "monochromator crystal that selects the incident energy.",
     None, None, "NXxas_herfd.html"),
    ("braggangle", "Bragg angle",
     "Bragg angle of the nominal reflection of a crystal analyzer.",
     None, None, "NXxas_herfd.html"),
    ("bendingradius", "Bending radius",
     "Bending radius of a spherically bent crystal analyzer. In Johann "
     "geometry this is twice the Rowland radius.",
     None, None, "NXxas_herfd.html"),
    ("rowlandradius", "Rowland radius",
     "Radius of the Rowland circle, on which the sample, crystal centre "
     "and detector focus all lie.",
     None, None, "NXxas_herfd.html"),
    ("analyzergeometry", "Analyzer geometry",
     "Type of crystal analyzer geometry, such as Johann or Johansson.",
     None, None, "NXxas_herfd.html"),
    ("analyzerdiameter", "Analyzer diameter",
     "Diameter of the crystal analyzer wafer.",
     None, None, "NXxas_herfd.html"),

    # --- detector counting, PFY --------------------------------------------
    ("deadtime", "Dead time",
     "Detector dead time per energy point: the interval during which the "
     "detector cannot register further events.",
     None, None, "NXxas_pfy.html"),
    ("counttime", "Count time",
     "Detector live time per energy point: the interval during which the "
     "detector is actively counting.",
     None, None, "NXxas_pfy.html"),

    # --- uncertainty --------------------------------------------------------
    ("intensityuncertainty", "Intensity uncertainty",
     "Errors associated with the intensity of the spectrum.",
     None, None, "NXxas.html"),
]


def en(v: str) -> dict:
    return {"@value": v, "@language": "en"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    doc = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    existing = {
        n["@id"] for n in doc["@graph"] if n.get("@type") == "skos:Concept"
    }
    scheme = next(
        (n for n in doc["@graph"] if n.get("@type") == "skos:ConceptScheme"),
        None,
    )
    if scheme is None:
        print("! no ConceptScheme found in the glossary", file=sys.stderr)
        return 1

    added, skipped = [], []
    for local, label, definition, notation, broader, src in CONCEPTS:
        cid = CDIF + local
        if cid in existing:
            skipped.append(local)
            continue
        node = {
            "@id": cid,
            "@type": "skos:Concept",
            "prefLabel": en(label),
            "definition": en(definition),
            "inScheme": {"@id": SCHEME},
            "seeAlso": MANUAL + src,
            "note": en(
                f"Definition adapted from the NeXus NXDL documentation in "
                f"{src.replace('.html', '')}."
            ),
        }
        if notation:
            node["notation"] = notation
        if broader:
            node["broader"] = {"@id": CDIF + broader}
        else:
            scheme.setdefault("hasTopConcept", []).append({"@id": cid})
        doc["@graph"].append(node)
        added.append(local)

    print(f"added:   {len(added)}")
    for a in added:
        print(f"  + {a}")
    if skipped:
        print(f"skipped (already present): {len(skipped)}")
        for s in skipped:
            print(f"  = {s}")

    if args.dry_run:
        print("\n(dry run - nothing written)")
        return 0

    GLOSSARY.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    total = sum(1 for n in doc["@graph"] if n.get("@type") == "skos:Concept")
    print(f"\nglossary now: {total} concepts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
