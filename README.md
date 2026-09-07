[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17421916.svg)](https://doi.org/10.5281/zenodo.17421916)

# Semantic description of XAS community standards using CDIF profile

This repository provides mapping of XAS community standards to the
[Cross-Domain Interoperability Framework
(CDIF)](https://cdif.codata.org/).  Version 1.0 corresponds to the
deliverable “D2: Semantic description of at least two XAS community
standards using a CDIF profile (XAS-CDIF)” of the
[CDIF-4-XAS](https://oscars-project.eu/projects/cdif-4-xas-describing-x-ray-spectroscopy-data-cross-domain-use)
project.

## This working copy

This is `smrgeoinfo/XAS-CDIF`, a fork of
[`CDIF-4-XAS/XAS-CDIF`](https://github.com/CDIF-4-XAS/XAS-CDIF), on the
**`cdifxasRelease`** branch.

**That branch has not been pushed back to `CDIF-4-XAS/XAS-CDIF`.** The
content has moved well beyond the 1.0 deliverable: a `xasDocument/1.0`
release profile, a rebuilt glossary, machine-readable crosswalks, and a
55-file test corpus with generated metadata. The published 1.0 files are
preserved in `archive/XAS-CDIF-1.0_release/`.

## Where the code lives

Nothing in this repository generates `exampleMetadata/`. Two external
pipelines consume what is here and write back into it:

| pipeline | repository | what it does |
|---|---|---|
| RML / Dataverse | [`smrgeoinfo/cdif-xas`](https://github.com/smrgeoinfo/cdif-xas) — **the fork**, not [`UKDSResearch/cdif-xas`](https://github.com/UKDSResearch/cdif-xas) | reads `exampleData/*.xdi`, writes `exampleMetadata/` |
| Python / SSSOM | [`CDIF-4-XAS/cdifnexmetadata`](https://github.com/CDIF-4-XAS/cdifnexmetadata) | reads NeXus **and** XDI; keeps its own copies of the crosswalks from here |

**The fork is what runs, and the distinction matters.** It is ahead of
`UKDSResearch/cdif-xas` by the CDIF 1.1 uplift and by header
normalisations the upstream does not have — ISO datetimes, qualitative
temperatures, unit-less energies — plus fixes to three `rr:constant`
values in the RML mapping that were producing wrong metadata: the
reflection plane, the monochromator crystal, and the detection mode.
Regenerating `exampleMetadata/` from upstream would silently produce
different, worse documents. Those commits have not been submitted
upstream yet; see `CONVERGENCE-PROPOSAL.md` in the fork.

Locally this checkout is `C:\GithubC\CDIF\cdif-xas-UKDS`, whose
`origin` is the fork and `upstream` is `UKDSResearch/cdif-xas` — so the
directory name says UKDS while the code that runs is the fork's.

To regenerate `exampleMetadata/`, from a checkout of the fork:

```bash
PYTHONPATH=. .venv/Scripts/python.exe tools/batch_generate_cdif.py \
    ../XAS-CDIF/exampleData ../XAS-CDIF/exampleMetadata
PYTHONPATH=. .venv/Scripts/python.exe tools/batch_validate_cdif.py \
    ../XAS-CDIF/exampleMetadata
```

The `tools/` and `crosswalk/` scripts **in this repository** build and
maintain the vocabulary artifacts, not the example metadata.

## Directory inventory

### `release/` — the `xasDocument/1.0` profile

The conformance target. Everything a validator needs.

| file | content |
|---|---|
| `cdifXASDocumentResolvedSchema.json` | JSON Schema, all `$ref`s inlined — **the validation target** |
| `cdifXASDocument-frame.jsonld` | JSON-LD frame; validation frames before checking |
| `xasDocumentRules.shacl` | SHACL shapes aggregated from all six composed profiles |
| `CDIFXASDocumentImplementationGuide.md` | classes, properties, XAS-specific requirements |
| `XAS_Glossary_SKOS_v2.json` | the released glossary snapshot |
| `FrameAndValidate.py` | frame + validate a single document |
| `examples/` | worked conforming documents |

Generated from
[`metadataBuildingBlocks`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks)
`_sources/profiles/cdifCompositeProfile/xasDocument/`. Edit there, not
here; the SHACL is regenerated with `tools/validate_shacl.py --emit-shapes`.

### `crosswalk/` — machine-readable mappings

| file | direction | consumed by |
|---|---|---|
| `cdifxas-to-nexus.sssom.tsv` | CDIF XAS concept → NeXus path | `cdifnexmetadata`, which keeps a copy |
| `xdi-to-cdifxas.sssom.tsv` | XDI key → CDIF XAS concept | `cdifnexmetadata`, which keeps a copy |
| `cdifxas-units.tsv` | CDIF XAS concept → QUDT unit | `cdifnexmetadata`, which keeps a copy |
| `build_crosswalk.py` | builds all three, and validates them | — |

**These files are the master copies.** `cdifnexmetadata` does not read them
from here at run time — it ships duplicates under
`src/cdifnexmetadata/data/`, so that it works offline and so a given
release is pinned to a known crosswalk revision. The cost is that the
copies can fall behind; `python -m cdifnexmetadata.map.crosswalk --refresh`
re-downloads all three.

`cdifxas-units.tsv` is the odd one out: not SSSOM, and not curated in
the script. It is read straight from the glossary's `qudt:hasUnit`
statements, because "this concept is dimensionless" is a fact about the
concept rather than an alignment between two vocabularies. Twelve
concepts carry one; `absorptioncoefficient` deliberately does not, since
its definition divides by sample thickness while every file stores the
dimensionless product.

`build_crosswalk.py` is the authority: the mappings are curated in
Python tables inside it and the TSVs are output. It checks every subject
against the glossary, every NeXus path against the live NXDL, and every
XDI key against the concept keys the RML mapping actually reads — so a
typo fails the build rather than producing a row that silently never
matches.

**Editing a crosswalk means editing `build_crosswalk.py` and
re-running it** — the TSVs are its output, so an edit made directly to a
TSV is overwritten by the next build. Then copy the regenerated files
into `cdifnexmetadata/src/cdifnexmetadata/data/`, or run `--refresh` there.

### `exampleData/` — 55 XDI test files

The PtSn catalysis series from Diamond B18, single spectra, and 18
`xdl_*` files selected from the
[XAS Data Library](https://github.com/XraySpectroscopy/XASDataLibrary)
by greedy set cover over edge, beamline, facility, detection mode,
monochromator, temperature regime and absorber Z — so they add variety
the corpus lacked rather than repeating it. See `exampleData/README.md`.

### How a column is located, in both sets

Both pipelines describe where a variable's values sit, and the two
example sets agree on the convention:

- **`cdif:TextMapping`** for a column in a text file, carrying
  `cdif:index` — the 1-based column — plus `cdi:minimumLength` and
  `cdi:maximumLength` measured over the data rows.
- **`cdif:LocatorMapping`** for a path into a container, carrying
  `cdif:locator`. Used for NeXus, where the path is only actionable
  through a reader such as h5py.

The two lengths are the field width **including the padding in front of
the value**, because that is what a fixed-width reader slices on: in
`       12508.00` the value is 8 characters and the field is 15. Where
minimum and maximum are equal the file really is fixed-width; where they
differ it is whitespace-separated and a reader must tokenise.

That distinction is not decorative. **21 of the 55 files in
`exampleData/` are fixed-width and 34 are not**, so neither claim holds
for the corpus as a whole and the widths have to be measured per file.
The two implementations derive them independently and agree —
`se_na2so4_rt.xdi` comes out at 15 characters for every column in both.

See "Which physical-mapping subclass, and what goes in it" in
`release/CDIFXASDocumentImplementationGuide.md`.

### `exampleMetadata/` — generated CDIF-XAS

55 JSON-LD documents plus batch generation and validation reports.
**Output, not source**: regenerate with the commands above rather than
editing. 55/55 validate against `release/`.

The same 55 files converted by the *other* pipeline live in
[`cdifnexmetadata/exampleMetadata-xdi`](https://github.com/CDIF-4-XAS/cdifnexmetadata),
not here. Both sets validate 55/55; the two are kept so the
implementations can be compared on identical inputs, which is what
`cdif-xas-UKDS/CONVERGENCE-PROPOSAL.md` argues from.

### `archive/`

| item | what it is |
|---|---|
| `XAS-CDIF-1.0_release/` | the published 1.0 deliverable, from the GitHub tag |
| `XAS_Glossary_SKOS.json` | the **v1** glossary. Shares a filename with the current glossary at the repository root and is not the same file — this is the superseded one |
| `XAS_Glossary_deprecated.xlsx` | the spreadsheet the glossary was originally curated in. Nothing read it and it fell out of step with the JSON; retired 2026-07-28 |
| `se_na2so4-testschemaorg-cdiv3.jsonLD` | hand-authored record, does not validate against the current profile |
| `XAS-Nexus-CDIFImplementation.xlsx`, `XAS-XDI-CDIFImplementation.xlsx` | per-format mapping sheets, superseded by `XAS-CDIFImplementation-revised.xlsx` |
| `XDI-CDIF-Mapping.xlsx`, `XDI-CDIF-Mapping_STikhonov.xlsx` | earlier XDI mapping drafts |
| `XDIVariablesInCDIF.txt` | XDI variable inventory |
| `XDISpec-FieldsCDIF-Schema.orgMapping.docx` | XDI spec fields against schema.org |
| `CDIF4XAS_Mappings_Intro.pdf` | introduction to the mappings |
| `Ravel_2016_*.pdf` | reference paper |
| `PhysicalDataset.png` | diagram |

### `tools/` — vocabulary maintenance

| script | what it does |
|---|---|
| `generate_concept_files.py` | per-concept files from the glossary |
| `generate_glossary_html.py` | the browsable glossary |
| `add_detection_mode_concepts.py` | detection-mode concepts |
| `import_nexus_enumerations.py` | pulls enumerated values from NXDL into the glossary |

### `tests/`

`cdif_dds_framed-generator-notes.md` and fixtures for the framing step.

## Root files

### Vocabulary — used by both pipelines

| file | role |
|---|---|
| `XAS_Glossary_SKOS.json` | **the concept hub.** Every crosswalk subject resolves here; `build_crosswalk.py` validates against it |
| `XAS_detectionmodes_SKOS.json` | transmission, fluorescence, electron yield, HERFD … |
| `XAS_edges_SKOS.json` | K, L1, L2, L3 … |
| `XAS_emissionlines_SKOS.json` | emission lines for HERFD and PFY |

The glossary filename carries no version on purpose: it is the working
copy. **Snapshots keep their version** —
`release/XAS_Glossary_SKOS_v2.json` is the released one, and the Pages
build publishes under that same `_v2` name because the per-concept
files link to it. Renaming the working file therefore does not move any
published URL.

These are the shared dependency. `cdifnexmetadata` does not read them
directly — it consumes the crosswalks, which `build_crosswalk.py`
validates against the glossary. So a concept renamed here breaks the
crosswalk build, which is the intended failure mode: it surfaces at
build time rather than as silently unmapped data.

All four conform to the **CDIF concept scheme profile**
([`profile-conceptscheme`](https://github.com/Cross-Domain-Interoperability-Framework/profile-conceptscheme)),
and each declares it in a `schema:subjectOf` catalog record with
`dcterms:conformsTo https://w3id.org/cdif/conceptscheme/1.1`. To check:

```bash
python ../profile-conceptscheme/FrameAndValidate.py XAS_Glossary_SKOS.json -v \
    --schema ../metadataBuildingBlocks/_sources/profiles/cdifProfile/cdifConceptScheme/resolvedSchema.json
```

Two things this requires that are easy to undo by accident. The
`@context` declares **prefixes only** — no alias terms like `prefLabel`
or `hasTopConcept` — because the validator compacts the framed graph
with the document's own context, so aliases yield a document that
expands correctly and still fails validation. And each document is
**rooted on its scheme**, concepts inline under `skos:hasTopConcept`
rather than siblings in an `@graph`.

**Prime marks are part of an emission-line name.** `slug()` in
`tools/import_nexus_enumerations.py` used to strip them, so `Kb2'` and
`Kb2''` both minted `…/xas/emissionline/kb2` — and likewise for `kb4`,
`kb5`, `lb7`, `lg4` and `lg8`. Six URIs each carried two distinct lines,
with two same-language `skos:prefLabel` values, which SKOS does not
allow. Primes now become underscores, so those nine concepts are
`kb2_`, `kb2__`, `lb7_` and so on, and all 432 concepts have their own
URI. Nothing outside the file referenced the old forms.

### Where the concepts come from

The 105 concepts in `XAS_Glossary_SKOS.json` are **minted for
this project**, in one scheme,
`https://w3id.org/cdif/xas/CDIF4XAS_Reference_Concepts`. Nothing
upstream is being re-published: they were assembled by reconciling the
XDI dictionary, the NeXus `NXxas` family and the XAS mapping
spreadsheets into a single technique vocabulary that both bindings can
resolve against.

**The definitions are sourced, not invented.** Provenance is carried on
the concepts themselves:

| property | on | pointing at |
|---|---|---|
| `references` | 90 of 105 | 97 DOIs, the XDI dictionary and other GitHub sources, the IUCr dictionary, `docs.xrayabsorption.org`, Wikipedia |
| `seeAlso` | 50 | `manual.nexusformat.org` — the resolvable NeXus documentation |
| `foaf:focus` | 36 | NeXusOntology PURLs under `purl.org/nexusformat/definitions/` |
| `notation` | 27 | the short token (`i0`, `mutrans`) the formats actually use |

15 concepts cite nothing. That is the gap to close first if the
glossary is published.

**`foaf:focus` is a known problem.** Those PURLs do not resolve — the
`purl.org/nexusformat` domain was never registered, and an open PR
renames every IRI besides. `build_crosswalk.py` refuses to use them for
exactly that reason and mints `nxdl:` under CDIF w3id instead, so the
glossary asserts identity against IRIs the crosswalk treats as
unusable. Both cannot be right. Until the NeXus side settles, `seeAlso`
to the manual is the link that works.

The same mint-now-redirect-later reasoning produced all three CDIF
namespaces — `cdifxas:`, `xdi:` and `nxdl:`. XDI defines no IRIs at all
and NeXus has none that resolve, so stable URIs had to come from
somewhere; w3id can be redirected to an official vocabulary later
without breaking anything already deployed. The rationale is written out
in the `CURIE_MAP` comment in `crosswalk/build_crosswalk.py`.

Two additions were made by script rather than by hand:

- `tools/add_detection_mode_concepts.py` added 14 detection-mode
  concepts, with definitions taken from the NXDL `<doc>` text of the
  corresponding fields and a `source` note on each, so the glossary and
  NeXus say the same thing rather than two similar things.
- `tools/import_nexus_enumerations.py` generates the three value-list
  schemes (`XAS_edges_SKOS.json`, `XAS_emissionlines_SKOS.json`,
  `XAS_detectionmodes_SKOS.json`) from NXDL enumerations. It
  deliberately does **not** write into the glossary: ~478 values against
  ~100 properties, and the publishing pipeline emits one file per
  concept. A property glossary and a value list are different artifacts.

`XAS_Glossary_vs_NeXus_analysis.md` is the record of the reconciliation,
including where the two vocabularies do not align.

**Curation happens in the JSON.** The glossary was originally curated in
`XAS_Glossary.xlsx`, but no script ever read that file: it had to be kept
in step by hand, and nothing detected it when the two drifted. It is now
`archive/XAS_Glossary_deprecated.xlsx`, and the JSON is both the master
and the file to edit.

### Analysis and mapping documents

| file | content |
|---|---|
| `DescriptionOfCDIF-XAS-profile.md` | the profile in prose |
| `XAS_Glossary_vs_NeXus_analysis.md` | glossary against the NeXus definitions, including where they do not align |
| `XAS-CDIFImplementation-revised.xlsx` | **the implementation mapping — the one working spreadsheet still maintained.** The earlier per-format sheets it supersedes are in `archive/` |

Everything else that used to sit here — the superseded mapping sheets,
the XDI spec comparison, the introductory and reference PDFs, and the
diagram — moved to `archive/` on 2026-07-28. Nothing in the repository
read any of them.

## Dependency summary

```
XAS_Glossary_SKOS.json          (concepts)
        │  validated against
        ▼
crosswalk/build_crosswalk.py  ──────►  crosswalk/*.sssom.tsv
                                              │  copied into
                                              ▼
                                    cdifnexmetadata/src/cdifnexmetadata/data/

metadataBuildingBlocks/_sources/…/xasDocument  ──►  release/
                                                       │  validation target for
                                                       ▼
                                        exampleMetadata/  ◄── cdif-xas-UKDS
```

Nothing here is generated from `exampleMetadata/`; it is the end of the
chain.

## Browsable glossary

See `tools/generate_glossary_html.py`.

## Copyright and License

See `LICENSE`, `LICENSES/`, and `REUSE.toml` for per-file licensing.
