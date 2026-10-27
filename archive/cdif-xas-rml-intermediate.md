# The cdif-xas (RML) intermediate — archived

Archived 2026-10-27 from `release/intermediateFormats.md`, where it was
documented as "Path B" beside the `cdifnexmetadata` intermediate. It
describes the original cdif-xas mapping workflow
([`smrgeoinfo/cdif-xas`](https://github.com/smrgeoinfo/cdif-xas), the fork
of [`UKDSResearch/cdif-xas`](https://github.com/UKDSResearch/cdif-xas)):
`/cdif` writes an XDI file's header into `resources/cdif_skos.json`, and
`rmlmapper` turns that file into CDIF per `resources/mapping_dds.ttl`.
That pipeline still generates `exampleMetadata/`, but it is not the path
to extend; for adding an input format see the README section "The
concept-keyed intermediate, and how to add an input format".

| | cdif-xas |
|---|---|
| intermediate | `resources/cdif_skos.json` |
| keyed on | XDI-flavoured names (`cdi:Facility_name`) |
| form | a JSON file on disk |
| produced by | `/cdif` (`api/cdi.py` + `api/cdif.py`) |
| consumed by | `rmlmapper`, per `mapping_dds.ttl` |

Its keys fuse concept and binding into one name (`cdi:Facility_name`),
which works for one input format and is why this path reads XDI only.


## The intermediate: `resources/cdif_skos.json`

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
