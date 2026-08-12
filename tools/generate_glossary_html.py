#!/usr/bin/env python3
"""Generate a browsable HTML page from XAS_Glossary_SKOS_v2_draft.json.

Reads the SKOS JSON-LD glossary and emits a single-file HTML page with an
alphabetized concept index and a per-concept detail block showing:
prefLabel, definition, notation, note, references, seeAlso, broader,
narrower (computed from broader inverse), and foaf:focus.

Output: XAS-CDIF-1.0_release/docs/index.html

No external Python dependencies beyond the standard library.
"""
from __future__ import annotations
import argparse
import html
import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def get_text(v):
    """Extract plain text from JSON-LD literal (string, dict {@value}, or list)."""
    if v is None:
        return ''
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return v.get('@value', '')
    if isinstance(v, list):
        for item in v:
            t = get_text(item)
            if t:
                return t
    return ''


def get_id(v):
    if isinstance(v, dict):
        return v.get('@id', '')
    if isinstance(v, str):
        return v
    return ''


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def load_glossary(path: Path):
    with path.open(encoding='utf-8') as f:
        doc = json.load(f)
    scheme = next(e for e in doc['@graph'] if e.get('@type') == 'skos:ConceptScheme')
    concepts = [e for e in doc['@graph'] if e.get('@type') == 'skos:Concept']
    return doc, scheme, concepts


def build_narrower(concepts):
    """Compute inverse of broader: {parent_uri: [child_uris]}."""
    narrower = {}
    for c in concepts:
        for b in as_list(c.get('broader')):
            parent = get_id(b)
            if parent:
                narrower.setdefault(parent, []).append(c['@id'])
    return narrower


CSS = """
:root {
  color-scheme: light;
  --bg: #ffffff;
  --fg: #1a1a1a;
  --muted: #666;
  --accent: #245a8a;
  --accent-bg: #e8f0f8;
  --border: #d0d7de;
  --code-bg: #f6f8fa;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--fg);
  background: var(--bg);
  line-height: 1.5;
}
header {
  background: var(--accent);
  color: white;
  padding: 1.25rem 2rem;
  border-bottom: 1px solid var(--border);
}
header h1 { margin: 0 0 0.25rem 0; font-size: 1.6rem; }
header .meta { opacity: 0.9; font-size: 0.9rem; }
header a { color: #cfe3f5; }
main {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 0;
  min-height: calc(100vh - 60px);
}
nav.toc {
  background: #fafbfc;
  border-right: 1px solid var(--border);
  padding: 1.25rem 1rem;
  overflow-y: auto;
  max-height: calc(100vh - 100px);
  position: sticky;
  top: 0;
  font-size: 0.9rem;
}
nav.toc h2 { margin: 0 0 0.75rem 0; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }
nav.toc ul { list-style: none; padding: 0; margin: 0; }
nav.toc li { margin: 0.15rem 0; }
nav.toc a { color: var(--fg); text-decoration: none; }
nav.toc a:hover { color: var(--accent); text-decoration: underline; }
.content { padding: 1.5rem 2.5rem; max-width: 900px; }
.intro { border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-bottom: 1.5rem; }
.intro dl { display: grid; grid-template-columns: 130px 1fr; gap: 0.25rem 1rem; margin: 0.5rem 0 0 0; }
.intro dt { color: var(--muted); font-weight: 600; }
section.concept {
  padding: 1.25rem 0 1.5rem 0;
  border-bottom: 1px solid var(--border);
  scroll-margin-top: 60px;
}
section.concept:last-child { border-bottom: none; }
section.concept h3 { margin: 0 0 0.5rem 0; font-size: 1.15rem; color: var(--accent); }
section.concept .uri { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 0.85rem; color: var(--muted); word-break: break-all; }
section.concept dl { display: grid; grid-template-columns: 110px 1fr; gap: 0.35rem 1rem; margin: 0.75rem 0 0 0; }
section.concept dt { color: var(--muted); font-weight: 600; }
section.concept dd { margin: 0; }
section.concept .notation-badge {
  display: inline-block;
  background: var(--accent-bg);
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 0.05rem 0.4rem;
  border-radius: 3px;
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.85rem;
  margin-left: 0.5rem;
}
a.ref { color: var(--accent); text-decoration: none; word-break: break-all; }
a.ref:hover { text-decoration: underline; }
a.concept-link { color: var(--accent); text-decoration: none; }
a.concept-link:hover { text-decoration: underline; }
.filter { margin: 0 0 1rem 0; }
.filter input {
  width: 100%;
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 0.9rem;
}
@media (max-width: 800px) {
  main { grid-template-columns: 1fr; }
  nav.toc { position: static; max-height: none; border-right: none; border-bottom: 1px solid var(--border); }
  .content { padding: 1rem; }
}
"""


JS_FILTER = """
document.getElementById('filter-input').addEventListener('input', (e) => {
  const q = e.target.value.trim().toLowerCase();
  document.querySelectorAll('nav.toc li').forEach(li => {
    const text = li.textContent.toLowerCase();
    li.style.display = !q || text.includes(q) ? '' : 'none';
  });
});
"""


def render_reference(url_or_curie: str) -> str:
    u = html.escape(url_or_curie)
    if url_or_curie.startswith(('http://', 'https://')):
        return f'<a class="ref" href="{u}" target="_blank" rel="noreferrer">{u}</a>'
    return u


def render_concept_link(uri: str, concept_by_uri: dict) -> str:
    """Render a link to another concept in the same glossary if we can, else the raw URI."""
    if uri in concept_by_uri:
        anchor = uri.rsplit('/', 1)[-1]
        label = get_text(concept_by_uri[uri].get('prefLabel')) or anchor
        return f'<a class="concept-link" href="#{html.escape(anchor)}">{html.escape(label)}</a>'
    return f'<a class="ref" href="{html.escape(uri)}" target="_blank" rel="noreferrer">{html.escape(uri)}</a>'


def render_concept(c: dict, concept_by_uri: dict, narrower: dict) -> str:
    uri = c['@id']
    anchor = uri.rsplit('/', 1)[-1]
    label = get_text(c.get('prefLabel')) or anchor
    definition = get_text(c.get('definition'))
    note = get_text(c.get('note'))
    notation = c.get('notation')

    parts = [f'<section id="{html.escape(anchor)}" class="concept">']
    badge = f'<span class="notation-badge">{html.escape(str(notation))}</span>' if notation else ''
    parts.append(f'<h3>{html.escape(label)}{badge}</h3>')
    parts.append(f'<div class="uri">{html.escape(uri)}</div>')
    parts.append('<dl>')
    if definition:
        parts.append(f'<dt>Definition</dt><dd>{html.escape(definition)}</dd>')
    if note:
        parts.append(f'<dt>Note</dt><dd>{html.escape(note)}</dd>')

    focus = get_id(c.get('foaf:focus'))
    if focus:
        parts.append(f'<dt>foaf:focus</dt><dd>{render_reference(focus)}</dd>')

    for parent in as_list(c.get('broader')):
        parts.append(f'<dt>Broader</dt><dd>{render_concept_link(get_id(parent), concept_by_uri)}</dd>')

    for child_uri in narrower.get(uri, []):
        parts.append(f'<dt>Narrower</dt><dd>{render_concept_link(child_uri, concept_by_uri)}</dd>')

    for r in as_list(c.get('references')):
        parts.append(f'<dt>References</dt><dd>{render_reference(str(r))}</dd>')

    for s in as_list(c.get('seeAlso')):
        parts.append(f'<dt>See also</dt><dd>{render_reference(str(s))}</dd>')

    parts.append('</dl></section>')
    return '\n'.join(parts)


def render_toc(concepts_sorted):
    lines = ['<ul>']
    for c in concepts_sorted:
        anchor = c['@id'].rsplit('/', 1)[-1]
        label = get_text(c.get('prefLabel')) or anchor
        notation = c.get('notation')
        suffix = f' <code>[{html.escape(str(notation))}]</code>' if notation else ''
        lines.append(f'<li><a href="#{html.escape(anchor)}">{html.escape(label)}</a>{suffix}</li>')
    lines.append('</ul>')
    return '\n'.join(lines)


def render_html(source_path: Path, doc: dict, scheme: dict, concepts: list) -> str:
    concept_by_uri = {c['@id']: c for c in concepts}
    narrower = build_narrower(concepts)
    concepts_sorted = sorted(
        concepts,
        key=lambda c: (get_text(c.get('prefLabel')) or c['@id'].rsplit('/', 1)[-1]).lower(),
    )

    scheme_uri = scheme.get('@id', '')
    scheme_label = get_text(scheme.get('prefLabel')) or 'Vocabulary'
    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(scheme_label)}</title>
<style>{CSS}</style>
</head>
<body>
<header>
<h1>{html.escape(scheme_label)}</h1>
<div class="meta">
Concept scheme URI: <a href="{html.escape(scheme_uri)}">{html.escape(scheme_uri)}</a> ·
{len(concepts)} concepts ·
Source: <code>{html.escape(source_path.name)}</code> ·
Generated {generated_at}
</div>
</header>
<main>
<nav class="toc">
<h2>Concepts</h2>
<div class="filter"><input id="filter-input" type="search" placeholder="Filter…" autocomplete="off"></div>
{render_toc(concepts_sorted)}
</nav>
<div class="content">
<section class="intro">
<h2 style="margin-top:0">About this vocabulary</h2>
<p>SKOS controlled vocabulary of concepts used in CDIF X-ray Absorption Spectroscopy metadata records.
Concepts that correspond to a class in the
<a class="ref" href="https://github.com/nexusformat/NeXusOntology" target="_blank" rel="noreferrer">NeXus ontology</a>
carry a <code>foaf:focus</code> link for the Nexus class URI; note that these URIs do not resolve but the
identified <code>owl:Class</code> entities are defined in the NeXus ontology. Others (physics concepts,
XDI column definitions, sample properties Nexus doesn't model) exist as XAS-specific extensions.</p>
<dl>
<dt>Namespace</dt><dd><a class="ref" href="{html.escape(scheme_uri)}">{html.escape(scheme_uri)}</a></dd>
<dt>Concepts</dt><dd>{len(concepts)}</dd>
<dt>Source</dt><dd><a class="ref" href="{html.escape(source_path.name)}">{html.escape(source_path.name)}</a></dd>
</dl>
</section>
{chr(10).join(render_concept(c, concept_by_uri, narrower) for c in concepts_sorted)}
</div>
</main>
<script>{JS_FILTER}</script>
</body>
</html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', default='XAS_Glossary_SKOS_v2_draft.json',
                    help='SKOS JSON-LD input (default: XAS_Glossary_SKOS_v2_draft.json — the working copy at repo root)')
    ap.add_argument('--out', default='XAS-CDIF-1.0_release/docs/index.html',
                    help='HTML output path (default: XAS-CDIF-1.0_release/docs/index.html)')
    args = ap.parse_args(argv)

    src = Path(args.source)
    out = Path(args.out)
    doc, scheme, concepts = load_glossary(src)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(src, doc, scheme, concepts), encoding='utf-8')
    print(f'Wrote {out} — {len(concepts)} concepts')
    return 0


if __name__ == '__main__':
    sys.exit(main())
