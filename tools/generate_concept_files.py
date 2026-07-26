#!/usr/bin/env python3
"""Emit one SKOS JSON-LD file per concept from XAS_Glossary_SKOS_v2_draft.json.

Reads the master SKOS JSON-LD glossary and writes, for every skos:Concept in
the @graph, a standalone per-concept JSON-LD file at

    XAS-CDIF-1.0_release/docs/concepts/{localname}.jsonld

The localname is the last path segment of the concept's @id (e.g.
`https://w3id.org/cdif/xas/samplepreparation` -> `samplepreparation`).

Each per-concept file is self-contained:
  - Carries the master @context so it parses without external lookups.
  - Contains that concept alone (bare, not in an @graph wrapper).
  - Keeps the concept's original @id as identity — the file location is
    where the RDF is *served from*, not what the concept *is called*.

If a concept has a `broader` link, the inverse `narrower` is materialized on
each parent so per-concept files are traversable both ways. (In the current
v2 source no concept carries `broader`, so this is a no-op today; kept in
place so it lights up automatically the first time hierarchy is introduced.)

Existing files under XAS-CDIF-1.0_release/docs/concepts/ whose basenames no
longer correspond to a concept in the source are removed, so stale files
don't linger after renames.

No external Python dependencies beyond the standard library.

Usage:
    python tools/generate_concept_files.py
    python tools/generate_concept_files.py --source XAS_Glossary_SKOS_v2_draft.json
    python tools/generate_concept_files.py --out XAS-CDIF-1.0_release/docs/concepts
    python tools/generate_concept_files.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "XAS_Glossary_SKOS_v2_draft.json"
DEFAULT_OUT = REPO_ROOT / "XAS-CDIF-1.0_release" / "docs" / "concepts"


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def get_id(v):
    if isinstance(v, dict):
        return v.get("@id", "")
    if isinstance(v, str):
        return v
    return ""


def localname_of(uri: str) -> str:
    """Return the last path segment of a URI."""
    if not uri:
        return ""
    tail = uri.rstrip("/").rsplit("/", 1)[-1]
    return tail


def compute_narrower(concepts):
    """Return {parent_uri: [child_uri, ...]} from the inverse of `broader`.

    Uses the SAME `broader` shape the master file uses — a list (or scalar)
    of {@id: parent} references — so this stays consistent with the HTML
    generator.
    """
    narrower = {}
    for c in concepts:
        for b in as_list(c.get("broader")):
            parent = get_id(b)
            child = c.get("@id")
            if parent and child:
                narrower.setdefault(parent, []).append({"@id": child})
    return narrower


def build_concept_file(concept, context, narrower_for_this):
    """Return the dict written to disk for a single concept."""
    # Concept fields land in a predictable order (a stable file diff matters
    # more here than a fancy ordering — it's what CI or a reviewer looks at).
    preferred_order = [
        "@id",
        "@type",
        "prefLabel",
        "altLabel",
        "notation",
        "definition",
        "note",
        "inScheme",
        "broader",
        "narrower",
        "seeAlso",
        "foaf:focus",
        "references",
    ]

    body = {"@context": context}
    seen = set()
    for key in preferred_order:
        if key == "narrower":
            if narrower_for_this:
                body[key] = narrower_for_this
            seen.add(key)
            continue
        if key in concept:
            body[key] = concept[key]
            seen.add(key)

    # Preserve any fields the source carries that we didn't anticipate,
    # in stable (sorted) order. This keeps the generator forward-compatible
    # with new SKOS properties added upstream without a code change.
    for key in sorted(concept.keys()):
        if key not in seen:
            body[key] = concept[key]

    return body


def write_json(path: Path, data, dry_run: bool) -> bool:
    """Write data to path (indent=2, utf-8, no trailing whitespace).

    Returns True if a change was written (or would be), False if the file
    already matches. Skips the write when dry_run=True.
    """
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current == payload:
            return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                    help=f"Master SKOS JSON-LD file (default: {DEFAULT_SOURCE.relative_to(REPO_ROOT)})")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help=f"Output directory for per-concept .jsonld files (default: {DEFAULT_OUT.relative_to(REPO_ROOT)})")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing files.")
    args = ap.parse_args(argv)

    if not args.source.exists():
        print(f"error: source file not found: {args.source}", file=sys.stderr)
        return 2

    doc = json.loads(args.source.read_text(encoding="utf-8"))
    context = doc.get("@context")
    graph = doc.get("@graph", [])
    if context is None:
        print("error: source is missing a top-level @context", file=sys.stderr)
        return 2

    concepts = [e for e in graph if e.get("@type") == "skos:Concept"]
    if not concepts:
        print("error: no skos:Concept entries found in @graph", file=sys.stderr)
        return 2

    narrower = compute_narrower(concepts)

    # Track expected filenames so we can prune stale ones.
    written = 0
    unchanged = 0
    skipped = []
    expected_files = set()

    for concept in concepts:
        uri = concept.get("@id", "")
        local = localname_of(uri)
        if not local:
            skipped.append(uri or "<no @id>")
            continue
        out_path = args.out / f"{local}.jsonld"
        expected_files.add(out_path.name)
        body = build_concept_file(concept, context, narrower.get(uri))
        changed = write_json(out_path, body, args.dry_run)
        if changed:
            written += 1
        else:
            unchanged += 1

    # Prune stale files (those whose concept URI is no longer in the source).
    pruned = []
    if args.out.exists():
        for existing in sorted(args.out.glob("*.jsonld")):
            if existing.name not in expected_files:
                pruned.append(existing.name)
                if not args.dry_run:
                    existing.unlink()

    verb = "Would write" if args.dry_run else "Wrote"
    print(f"{verb} {written} file(s), {unchanged} unchanged, "
          f"in {args.out.relative_to(REPO_ROOT) if args.out.is_relative_to(REPO_ROOT) else args.out}")
    if skipped:
        print(f"  skipped (no derivable localname): {len(skipped)}")
        for s in skipped[:5]:
            print(f"    - {s}")
    if pruned:
        verb2 = "Would prune" if args.dry_run else "Pruned"
        print(f"  {verb2} {len(pruned)} stale file(s):")
        for name in pruned[:10]:
            print(f"    - {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
