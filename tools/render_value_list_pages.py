#!/usr/bin/env python3
"""Render the three value-list vocabularies as HTML pages.

The glossary has its own page (generate_glossary_html.py). The value lists --
XAS_edges_SKOS.json, XAS_emissionlines_SKOS.json, XAS_detectionmodes_SKOS.json
-- are rendered with the iSamples vocabulary tooling instead, the same writer
CDIF uses for the provenance activity types: vocab2mdCacheV2.describeVocabulary
turns an rdflib graph into Quarto markdown, and Quarto renders that to HTML.

Output, per vocabulary, beside the published JSON in build/docs/:
  XAS_<name>_SKOS.html  (+ XAS_<name>_SKOS_files/, Quarto's assets)

w3id sends a browser asking for a value-list concept
(https://w3id.org/cdif/xas/edge/k) to <page>#<localname>, so every concept
must have an anchor named for the last segment of its URI. The writer emits
one per concept; this script fails if any is missing.

Needs rdflib, a checkout of isamplesorg/vocabularies (its tools/ directory,
plus tools/requirements.txt installed), and quarto on PATH.

    python tools/render_value_list_pages.py --isamples path/to/isamplesorg-vocabularies/tools
"""
from __future__ import annotations
import argparse
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

VALUE_LISTS = (
    'XAS_edges_SKOS.json',
    'XAS_emissionlines_SKOS.json',
    'XAS_detectionmodes_SKOS.json',
)
GLOSSARY_NS = 'https://w3id.org/cdif/xas/'


def render(source: Path, out_dir: Path, writer, rdflib) -> str:
    """Write <stem>.md with the iSamples writer, render it, return the HTML path."""
    g = rdflib.Graph()
    g.parse(source, format='json-ld')
    schemes = list(g.subjects(rdflib.RDF.type, rdflib.SKOS.ConceptScheme))
    if len(schemes) != 1:
        raise SystemExit(f'{source}: expected one skos:ConceptScheme, found {len(schemes)}')
    md = out_dir / f'{source.stem}.md'
    md.write_text('\n'.join(writer.describeVocabulary(g, schemes[0])) + '\n', encoding='utf-8')
    subprocess.run(['quarto', 'render', md.name, '-t', 'html'], cwd=out_dir, check=True,
                   shell=sys.platform == 'win32')
    md.unlink()
    page = out_dir / f'{source.stem}.html'

    ids = set(re.findall(r'id="([^"]+)"', page.read_text(encoding='utf-8')))
    concepts = set(g.subjects(rdflib.RDF.type, rdflib.SKOS.Concept))
    missing = sorted(str(c) for c in concepts if str(c).rstrip('/').rsplit('/', 1)[-1] not in ids)
    if missing:
        raise SystemExit(f'{page}: {len(missing)} concept(s) have no anchor, e.g. {missing[:3]}')

    # Each list hangs off a glossary concept (edges under xas:edgeanalyzed),
    # and the writer links "Child of" as #<name> on this page, where it does
    # not exist. Point those at the glossary page, which has that anchor.
    html = page.read_text(encoding='utf-8')
    for parent in set(g.objects(None, rdflib.SKOS.broader)) - concepts:
        if str(parent).startswith(GLOSSARY_NS):
            name = str(parent)[len(GLOSSARY_NS):]
            html = html.replace(f'href="#{name}"', f'href="index.html#{name}"')
    page.write_text(html, encoding='utf-8')
    return f'{page} -- {len(concepts)} concepts'


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--isamples', required=True, type=Path,
                    help='the tools/ directory of an isamplesorg/vocabularies checkout')
    ap.add_argument('--out', default='build/docs', type=Path,
                    help='output directory (default: build/docs)')
    args = ap.parse_args(argv)

    if shutil.which('quarto') is None:
        raise SystemExit('quarto is not on PATH')
    sys.path.insert(0, str(args.isamples.resolve()))
    import rdflib
    import vocab2mdCacheV2 as writer
    logging.disable(logging.CRITICAL)  # the writer logs every missing optional property

    args.out.mkdir(parents=True, exist_ok=True)
    for name in VALUE_LISTS:
        print('Wrote', render(Path(name), args.out.resolve(), writer, rdflib))
    return 0


if __name__ == '__main__':
    sys.exit(main())
