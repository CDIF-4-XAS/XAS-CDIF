# Crosswalks

The CDIF XAS glossary (`../XAS_Glossary_SKOS.json`) is the hub. XDI and
NeXus are two bindings to it, and CDIF JSON-LD is where a concept ends up:

```
XDI token  --\                             (2) placement
              >--  cdifxas: concept  ----------------------->  CDIF JSON-LD
NeXus path --/
     (1) SSSOM alignment
```

Step (1) is an alignment between vocabularies, so it is SSSOM. Step (2)
is not: it says which object in a document a concept's value goes on,
and has no object IRI to align to. It is a plain TSV.

## Files

| file | maps | rows | built by |
|---|---|---|---|
| `xdi-to-cdifxas.sssom.tsv` | XDI token → CDIF XAS concept | 31 | `build_crosswalk.py` |
| `cdifxas-to-nexus.sssom.tsv` | CDIF XAS concept → NeXus field path | 52 | `build_crosswalk.py` |
| `xdi-to-schemaorg.sssom.tsv` | XDI extension header → schema.org property | 4 | `build_crosswalk.py` |
| `cdifxas-units.tsv` | CDIF XAS concept → QUDT unit | 12 | `build_crosswalk.py` |
| `cdifxas-placement.tsv` | CDIF XAS concept → place in CDIF JSON-LD | 13 | `build_placement.py` |

**All five are generated. Do not edit the TSVs**; the next build
overwrites them.

### `xdi-to-cdifxas.sssom.tsv`

XDI/1.0 dictionary tags, plus beamline extension headers seen in real
XDI data (`Beamline.flux`, `Beamline.scan_mode`, …), to the glossary
concepts. Transmission-mode only, because XDI defines no tokens for
electron yield, emission-line selection or analyzer geometry; those
concepts reach CDIF through NeXus alone.

### `cdifxas-to-nexus.sssom.tsv`

Glossary concepts to NeXus field paths in the restructured `NXxas`
family, covering all six detection modes. NeXus has no resolvable IRIs,
so objects are minted as `nxdl:` under CDIF w3id; the `CURIE_MAP`
comment in `build_crosswalk.py` explains why.

### `xdi-to-schemaorg.sssom.tsv`

The bibliographic and rights headers (`Publication.DOI`,
`Publication.authors`, `Publication.affiliation`, `Spectrum.license`)
that CDIF models with schema.org rather than with an XAS concept. It is a
separate set because SSSOM declares one `object_source` per set; mixing
schema.org objects into `xdi-to-cdifxas` would make that declaration
false.

### `cdifxas-units.tsv`

Not SSSOM. Read straight from the glossary's `qudt:hasUnit` statements,
since a concept's unit is a fact about the concept, not an alignment.

### `cdifxas-placement.tsv`

**Derived from the mapping implemented in `emit.py`** of
[`CDIF-4-XAS/cdifnexmetadata`](https://github.com/CDIF-4-XAS/cdifnexmetadata)
— specifically its `CONCEPT_SLOTS` table — **not curated here.** To
change where a concept is placed, change `emit.py` and re-run
`build_placement.py`. The header records the `emit.py` commit the table
was built from.

Each row gives the concept, a path from the root Dataset to where its
value goes, and the form the value takes there:

- `PropertyValue`: a `schema:PropertyValue` whose `schema:propertyID` is
  `property_id`, i.e. the concept's own local name. The `xasDocument`
  profile lists the same names, so the spelling has to match the glossary
  exactly.
- `DefinedTerm`: a `schema:DefinedTerm` (element and edge keywords, the
  detection mode).
- `name`: the `schema:name` of the object itself (facility, beamline).

In `jsonld_path`, `[x]` selects the array item whose
`schema:additionalType` is `x`. A concept with no row is not dropped: it
is emitted as a `PropertyValue` on the acquisition activity.

The table shows what `emit.py` emits, which includes four terms the
profile has retired: `xas:beamline`, `xas:xraysourcetype`, `xas:probe`
and `xas:temperature`. Since 2026-09-27 the profile prefers NeXus
base-class terms for these and still accepts the old ones; the list is
in the main README, under "How a concept is placed in the JSON-LD". When
`emit.py` switches, a rebuild picks the change up.

Two limits on what this table covers:

- **Only `cdifnexmetadata`.** The RML converter
  ([`smrgeoinfo/cdif-xas`](https://github.com/smrgeoinfo/cdif-xas),
  `resources/mapping_dds.ttl`) places each property with its own
  hand-written triples map, and nothing here reads or checks it, so
  nothing ensures the two converters place a concept the same way.
- **Only scalar concepts.** Data-array columns (`energy`, `i0`,
  `mutrans`, …) become `schema:variableMeasured` entries by separate code
  in `emit.py`, which this table does not describe.

## Building

```bash
python crosswalk/build_crosswalk.py           # validate, then write the four SSSOM/units files
python crosswalk/build_crosswalk.py --check   # validate only
python crosswalk/build_placement.py           # write cdifxas-placement.tsv
python crosswalk/build_placement.py --check   # validate only
```

The mappings in the three SSSOM sets are curated in Python tables inside
`build_crosswalk.py`. It checks every subject against the glossary, every
NeXus path against the NXDL at a pinned commit, and every XDI key against
the keys the RML mapping actually reads (from a `cdif-xas-UKDS/` or
`cdif-xas/` checkout beside this repository, or `$CDIF_XAS_RML`;
`--no-rml-check` skips this).

`build_placement.py` reads `emit.py` from a `cdifnexmetadata` checkout
beside this repository (or `$CDIFNEXMETADATA`) without importing it. It
fails if a concept is not in the glossary, or if `emit.py` uses a
placement target the script does not yet know how to describe.

## Consumers

`cdifnexmetadata` ships copies of the four `build_crosswalk.py` outputs
under `src/cdifnexmetadata/data/` and refreshes them with
`python -m cdifnexmetadata.map.crosswalk --refresh`. It does not need
`cdifxas-placement.tsv`, which is derived from its own code; the table
exists so the placement can be read, and compared against the RML
converter, without reading Python.
