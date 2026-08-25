# The two intermediates, and how to add an input format

Neither XAS→CDIF converter goes from file to CDIF in one step. Both parse
the source into a **concept-keyed intermediate** and then transform *that*
into CDIF. This document describes both structures, because the
intermediate is the contract a new input format has to meet — adding NeXus
`NXsas`, `NXtomo`, or a lab instrument's own format is a matter of
producing one of these, not of touching the CDIF-emitting code.

Companion to [`xasToCdifWorkflows.md`](xasToCdifWorkflows.md), which covers
running the two pipelines. Current as of 2026-08-25.

---

## Why this is the seam

| | Path A (`cdifnexmetadata`) | Path B (`cdif-xas`) |
|---|---|---|
| intermediate | `ConceptRecord` / `MappingResult` | `resources/cdif_skos.json` |
| keyed on | glossary concept URIs (`cdifxas:facility`) | XDI-flavoured names (`cdi:Facility_name`) |
| form | Python objects, or JSON via `--dump-concepts` | a JSON file on disk |
| produced by | `map/` (`concepts.py`, `xdi.py`) | `/cdif` (`api/cdi.py` + `api/cdif.py`) |
| consumed by | `emit.py` | `rmlmapper`, per `mapping_dds.ttl` |

**What decides how far each can be extended is what the key is.** Path A
keys on the CDIF XAS glossary, so the concept and the format it arrived in
are separate things: a NeXus path and an XDI token that mean the same
thing produce the same key, and the source field travels beside the value.
Path B keys on `cdi:Facility_name` — concept and binding fused into one
name — which works for one input format and is why that path reads XDI
only.

So for a new input format, Path A is the one to extend.

---

## Path A: the `ConceptRecord` intermediate

Dump it for any file:

```bash
uv run cdifnexmetadata scan.nxs --dump-concepts
```

With `-o` pointing at a directory, each input is written as
`<stem>.concepts.json`.

### Shape

```jsonc
{
  "crosswalk_source": ".../xdi-to-cdifxas.sssom.tsv",  // absolute, machine-specific
  "crosswalk_reason": "XDI binding; the file declares its format on line 1",
  "legacy_source": "",
  "record_count": 1,
  "records": [ /* one per NXentry; an XDI file has exactly one */ ],
  "warnings": []
}
```

`crosswalk_reason` is there because a silent choice between vocabularies
cannot be debugged from the output alone. For a NeXus file it names the
application definition that selected the crosswalk, or says that none
matched and only base-class mappings were used.

Each record:

```jsonc
{
  "entry_name": "scan1",
  "entry_path": "/scan1",          // "/" for XDI
  "definition": "NXxas",           // application definition; null for XDI
  "values": { /* concept URI -> list of values, below */ },
  "bibliographic": { /* schema.org-bound values, below */ },
  "publication_fields": { "Publication.journal": "J. Example Chem." },
  "conversion_notes": ["temperature reported as \"room temperature\""],
  "warnings": ["11 header(s)/column(s) had no crosswalk entry: ..."]
}
```

### `values` — the part that matters

Keys are **CDIF XAS glossary concept URIs** as CURIEs. Each maps to a
*list*, because a file may state a concept more than once.

```jsonc
"cdifxas:beamline": [
  {
    "value": "13-BM-D",
    "units": null,
    "source_path": "#Beamline.Name",   // "/entry/instrument/name" for NeXus
    "predicate": "skos:exactMatch",    // from the SSSOM row
    "confidence": 1.0,
    "is_array": false,
    "shape": [],
    "dtype": "",
    "note": "Name of the beamline."
  }
]
```

An array-valued concept — a data column, or an HDF5 dataset that was
described but not read:

```jsonc
"cdifxas:incidentintensity": [
  {
    "value": null,               // deliberately not read; this is data
    "units": null,
    "source_path": "#column:3",
    "predicate": "skos:exactMatch",
    "confidence": 1.0,
    "is_array": true,
    "shape": [469],
    "dtype": "float64",
    "label": "i0",               // what the source called it
    "long_name": "i0",           // NeXus long_name, where the writer set one
    "index": 3,                  // 1-based column, tabular sources only
    "width": [13, 13],           // observed field width, min/max
    "note": "Data column: incident beam intensity."
  }
]
```

| field | meaning |
|---|---|
| `value` | the scalar, or `null` for an array |
| `units` | as the source stated them, or supplied from the XDI dictionary |
| `source_path` | where in the file it came from — an HDF5 path, or `#Header.tag` / `#column:N` |
| `predicate` | the SSSOM predicate that licensed the mapping |
| `confidence` | `1.0` for an `exactMatch`; a `closeMatch` carries less |
| `is_array`, `shape`, `dtype` | set when the concept is an array that was described, not read |
| `label`, `long_name` | names the source gave it; used to name the emitted variable |
| `index`, `width` | position in a tabular source |
| `note` | the crosswalk row's comment, plus any conversion note |
| `convention` | set when the value came from the legacy path table, naming the writer convention that put it there |

Optional fields appear only when set, so a scalar stays short.

Arrays are described and not read on purpose: the shape is what the
data-structure profile needs, and the numbers are data. A new parser
should do the same.

### `bibliographic`

Values the crosswalk bound to a **schema.org property** rather than to a
concept, keyed by the property CURIE. Kept apart from `values` because a
serialization target is not a concept.

```jsonc
"bibliographic": {
  "schema:license":    { "value": "https://creativecommons.org/licenses/by/4.0/" },
  "schema:identifier": { "value": "10.1021/...", "source_path": "#Publication.DOI" },
  "schema:author":     { "value": "Smith, J. and Jones, A.",
                         "predicate": "skos:closeMatch", "confidence": 0.8 }
}
```

Populated only by the XDI binding, from `xdi-to-cdif.sssom.tsv`. A NeXus
file carries no bibliographic fields, so a NeXus parser can ignore this.

---

## Path B: `resources/cdif_skos.json`

Written by `/cdif` (or by `tools/batch_generate_cdif.py`) and read by
`/map`. The RML mapping names the file in its own `rml:logicalSource`, so
`rmlmapper` is invoked with a mapping and an output and **no source
argument** — which is why a stale `cdif_skos.json` makes `/map` silently
reprocess the previous run's data.

### Shape

```jsonc
{
  "@context": { "cdi": "...", "schema": "...", "skos": "...", "cdif": "..." },
  "@graph": [ /* one Dataset node, then one node per XDI namespace */ ],
  "columns": [ /* ... */ ]
}
```

`@graph[0]` is the dataset, carrying schema.org properties and the marker
the RML iterator selects on:

```jsonc
{
  "@id": "http://localhost:8080/citation?persistentId=perma:DV/Se_Na2SeO4_rt_01",
  "@type": "schema:Dataset",
  "schema:name": "...", "schema:author": "...", "schema:license": "...",
  "cdif:isDatasetRecord": "yes"        // rml:iterator matches on this
}
```

Every other node is **one XDI namespace**, not one field:

```jsonc
{
  "@id": "cdi:Beamline",
  "skos:broader": [
    { "@id": "cdi:Beamline_name" },
    { "@id": "cdi:Beamline_xray_source" },
    { "@id": "cdi:Beamline_storage_ring_current" }
  ],
  "skos:prefLabel": [
    "Beamline",              // [0] is the namespace label
    "13-BM-D",               // [1..] are values, in header order
    "bending magnet",
    "101.792"
  ],
  "cdi:Beamline_name": {
    "@id": "_:Nb4b4a3ed...", "skos:definition": "13-BM-D"
  },
  "cdi:Beamline_xray_source": {
    "@id": "_:N0501b21c...", "skos:definition": "bending magnet"
  }
}
```

**Each value is reachable two ways, and only one of them is safe.**

- By name: `$['cdi:Beamline_name']['skos:definition']` — stable.
- By position: `$['skos:prefLabel'][1]` — **not** stable. The array is
  built in header order with no fixed length, so an index means different
  things in different files. A rule reading `$['skos:prefLabel'][2]` for a
  scan start time got the start time in 21 of 55 files, the **end** time
  in 4, and nothing in 12 more that published no acquisition date. Every
  one of those validated.

If you find yourself indexing `skos:prefLabel`, the value you want has a
name. Use the name.

### The other trap in this path

A derivation and the rule that carries it live in different files, and
neither fails without the other. `api/cdi.py` once converted `room
temperature` to `295.0 K` and appended a conversion note, while
`mapping_dds.ttl` had no temperature rule at all — so 15 documents
announced the conversion of a number that appeared nowhere in them, and
all 21 files recording a temperature published none. After adding a
derived key, grep the generated output for its value.

---

## Adding an input format

For Path A, in this order:

1. **Write an inspector** under `inspect/` that reads the format into
   whatever plain structure suits it. It should know nothing about CDIF or
   about concepts.
2. **Write a mapper** under `map/` that turns that into a `ConceptRecord`,
   setting `source_path`, `predicate` and `confidence` on every value.
   This is where the format's vocabulary meets the glossary.
3. **Supply a crosswalk**, not code, for the field-to-concept
   correspondence: an SSSOM TSV whose subjects are your format's field
   names and whose objects are glossary concepts.
4. **Dispatch** in `cli.py` on what the file declares rather than on its
   extension.

`emit.py` should need no change. If it does, the concept being mapped is
probably missing from the glossary — add it there rather than
special-casing the emitter.

### For another NeXus application definition, only step 3 applies

The NeXus inspector and mapper already walk any NXDL tree, and
`select_crosswalk()` picks a crosswalk from the `definition` the file
declares — so a folder of mixed techniques needs no per-file
configuration. A new application definition is therefore a crosswalk TSV
whose objects are NXDL paths, and nothing else.

`cdifsas-to-nexus.sssom.tsv` exists as proof: small-angle scattering
(`NXsas` — a different application definition from `NXxas`, not a
misspelling of it) was added as a crosswalk with no code change at all.
Pass it with `--crosswalk` and an `NXsas` file yields concepts, variables
and a data structure.

#### Writing the crosswalk

Subjects are concept CURIEs, objects are NXDL paths:

```
cdifsas:detectordistance  ->  nxdl:NXsas/ENTRY:NXentry/INSTRUMENT:NXinstrument/DETECTOR:NXdetector/distance
cdifsas:wavelength        ->  nxdl:NXmonochromator/wavelength
```

- The first segment after `nxdl:` is the **application definition**
  (`NXsas`) or a **base class** (`NXmonochromator`).
- Middle segments are `PLACEHOLDER:NXclass`. Matching is on the *class*;
  the placeholder name is the NXDL's own and is a hint, not a
  requirement, because real writers rarely use it.
- The last segment is the field name.

The two row kinds behave differently, and this is the part worth knowing
before writing any:

**An application-definition row** is rooted at the entry, so its path
leads with a `:NXentry` segment. It applies only to files declaring that
definition.

**A base-class row** is relative to an instance of the class and does not
lead with `:NXentry`. It applies to **any** definition — which is why a
file declaring something no crosswalk covers still yields facility,
beamline, probe and source type. That classification is structural, not
by name: testing `startswith("NXxas")` instead would silently class every
non-XAS definition as a base class and apply `NXsas` paths to XAS files.

Map more than one path to the same concept where writers disagree; the
first that resolves wins. `cdifsas:scatteringintensity` has two rows,
one for `DETECTOR:NXdetector/data` and one for `DATA:NXdata/data`.

Map only what the file contains. `Q`, the scattering vector, has no row
because a raw `NXsas` file does not carry it — it is computed from
wavelength, distance and pixel geometry, and a row for it would map
something that does not exist.

If a concept is technique-neutral, **reuse the existing CURIE rather than
re-minting it**. The SAS crosswalk keeps five `cdifxas:` subjects
unchanged — `facility`, `beamline`, `probe`, `xraysourcetype` and
`temperature` — none of which is an XAS concept. SSSOM identifies
concepts rather than namespaces, so re-minting them under `cdifsas:`
would assert that a SAS facility and an XAS facility are different
things. They are not. That they sit in an XAS-flavoured namespace is an
accident of which crosswalk was written first; writing the second one is
what exposed it, and the fix is a technique-neutral namespace in the
glossary rather than a duplicate here.

`docs/NXsas.md` in that repository covers what NXsas is and how real
files depart from the definition.

A file whose definition no crosswalk covers is therefore a thin document
rather than a failure, and `crosswalk_reason` in the dump is the only
place that says which happened.

### Check your work by reading the intermediate

```bash
uv run cdifnexmetadata new_format_file.ext --dump-concepts
```

A concept absent from that dump will be absent from the CDIF document, and
nothing downstream will say so. That is the failure mode this whole
pipeline is arranged around: an unmapped field produces no output and no
error, and a document that is missing half its metadata validates exactly
as well as one that is complete.
