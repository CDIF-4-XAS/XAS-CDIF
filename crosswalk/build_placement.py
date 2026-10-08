#!/usr/bin/env python3
"""Build cdifxas-placement.tsv: where each CDIF XAS concept goes in CDIF JSON-LD.

The SSSOM sets in this directory take a source field (XDI token, NeXus
path) to a CDIF XAS concept. They say nothing about the second step --
which object in the CDIF JSON-LD document a concept's value is placed on.
That step is implemented in code, and this table is DERIVED from one
implementation: the `CONCEPT_SLOTS` table in `emit.py` of
CDIF-4-XAS/cdifnexmetadata. It is not curated here, and an edit to the
TSV is overwritten by the next build -- change `emit.py` and re-run.

Not SSSOM, on purpose: a placement is not an alignment between two
vocabularies. "edge energy goes in an additionalProperty of the
acquisition activity" has no object IRI and no SSSOM predicate that
means it. Like cdifxas-units.tsv, it is a fact about the concept, so it
is a plain TSV with a commented header.

`emit.py` is read with `ast`, not imported, so this needs nothing from
cdifnexmetadata beyond its source. The checkout is found beside this
repository, or at $CDIFNEXMETADATA.

Checks, any of which fails the build:
  * every concept in CONCEPT_SLOTS exists in XAS_Glossary_SKOS.json
  * every slot target is one this script knows how to describe -- a new
    target in emit.py has to be described here before it can be published

Usage:
    python crosswalk/build_placement.py [--check]
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_crosswalk import GLOSSARY, iter_concepts  # noqa: E402

OUT = HERE / "cdifxas-placement.tsv"
EMIT = Path("src/cdifnexmetadata/emit.py")

# Where each emit.py slot target lands in the document, read off
# emit_document() and _instruments(). Paths are from the root Dataset;
# [x] filters an array to the item whose schema:additionalType is x.
ACTIVITY = "prov:wasGeneratedBy[xas:analysisevent]"
INSTRUMENT = ACTIVITY + "/prov:used/schema:instrument[{}]"
TARGETS = {
    "facility": (
        "schema:contributor[schema:roleName=Facility]/schema:contributor"
        "/schema:name ; " + ACTIVITY + "/schema:location/schema:name",
        "name"),
    "instrument": (INSTRUMENT.format("xas:beamline") + "/schema:name",
                   "name"),
    "source": (INSTRUMENT.format("xas:source")
               + "/schema:additionalProperty", "PropertyValue"),
    "monochromator": (INSTRUMENT.format("xas:xraymonochromator")
                      + "/schema:additionalProperty", "PropertyValue"),
    "sample": (ACTIVITY + "/schema:object/schema:additionalProperty",
               "PropertyValue"),
    "activity": (ACTIVITY + "/schema:additionalProperty", "PropertyValue"),
    "keyword": ("schema:keywords", "DefinedTerm"),
    "technique": ("schema:measurementTechnique", "DefinedTerm"),
}

COLS = ["subject_id", "subject_label", "target", "jsonld_path",
        "value_form", "property_id", "name"]


def find_cdifnexmetadata() -> Path | None:
    env = os.environ.get("CDIFNEXMETADATA")
    if env:
        return Path(env)
    p = HERE.parent.parent / "cdifnexmetadata"
    return p if p.is_dir() else None


def read_slots(emit_py: Path) -> dict[str, tuple[str, str, str]]:
    """CONCEPT_SLOTS from emit.py, as {concept: (target, prop, label)}."""
    tree = ast.parse(emit_py.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (isinstance(node, ast.AnnAssign)
                and getattr(node.target, "id", None) == "CONCEPT_SLOTS"):
            table = node.value
            break
    else:
        raise SystemExit(f"CONCEPT_SLOTS not found in {emit_py}")
    slots = {}
    for k, v in zip(table.keys, table.values):
        args = [ast.literal_eval(a) for a in v.args]
        target, prop = args[0], args[1]
        label = args[2] if len(args) > 2 else ""
        slots[ast.literal_eval(k)] = (target, prop, label)
    return slots


def pref_label(node: dict) -> str:
    v = node.get("skos:prefLabel", "")
    if isinstance(v, list):
        v = v[0] if v else ""
    return v.get("@value", "") if isinstance(v, dict) else v


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="validate only, write nothing")
    args = ap.parse_args(argv)

    repo = find_cdifnexmetadata()
    if repo is None or not (repo / EMIT).is_file():
        print(f"cannot find {EMIT} -- check out CDIF-4-XAS/cdifnexmetadata "
              f"beside this repository, or set $CDIFNEXMETADATA")
        return 1
    slots = read_slots(repo / EMIT)
    rev = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()

    doc = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    labels = {n["@id"].rsplit("/", 1)[-1]: pref_label(n)
              for n in iter_concepts(doc)}

    problems = []
    rows = []
    for concept, (target, prop, label) in sorted(slots.items()):
        local = concept.split(":", 1)[-1]
        if local not in labels:
            problems.append(f"{concept}: not in the glossary")
        if target not in TARGETS:
            problems.append(f"{concept}: slot target {target!r} is not "
                            f"described in build_placement.TARGETS")
            continue
        path, form = TARGETS[target]
        rows.append({
            "subject_id": concept,
            "subject_label": labels.get(local, ""),
            "target": target,
            "jsonld_path": path,
            "value_form": form,
            "property_id": f"xas:{prop}" if form == "PropertyValue" else "",
            "name": label,
        })

    print(f"{len(slots)} concepts in CONCEPT_SLOTS "
          f"({repo / EMIT} @ {rev[:8] or 'unknown'})")
    for p in problems:
        print(f"  ! {p}")
    if args.check or problems:
        return 1 if problems else 0

    header = [
        "# title: CDIF XAS concept placement in CDIF JSON-LD",
        "# description: Where cdifnexmetadata places the value of each "
        "CDIF XAS concept. Derived from CONCEPT_SLOTS in emit.py, not "
        "curated; regenerate with crosswalk/build_placement.py.",
        "# derived_from: https://github.com/CDIF-4-XAS/cdifnexmetadata/"
        f"blob/{rev or 'main'}/{EMIT.as_posix()}",
        "# mapping_tool: crosswalk/build_placement.py",
        "# path_notation: from the root Dataset; [x] selects the array "
        "item whose schema:additionalType is x; ' ; ' separates two places",
        "# unlisted_concepts: emitted as a PropertyValue in "
        + ACTIVITY + "/schema:additionalProperty",
    ]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n")
        w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t",
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {OUT.name} ({len(rows)} concepts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
