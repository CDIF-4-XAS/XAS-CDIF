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
| Python / SSSOM | [`usgin/hdf5metadata`](https://github.com/usgin/hdf5metadata) | reads NeXus **and** XDI; vendors the crosswalks from here |

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
| `cdifXASDocumentStructuredSchema.json` | the same with `$ref`s preserved |
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
| `cdifxas-to-nexus.sssom.tsv` | CDIF XAS concept → NeXus path | `hdf5metadata` (vendored copy) |
| `xdi-to-cdifxas.sssom.tsv` | XDI key → CDIF XAS concept | `hdf5metadata` (vendored copy) |
| `build_crosswalk.py` | builds both, and validates them | — |

`build_crosswalk.py` is the authority: the mappings are curated in
Python tables inside it and the TSVs are output. It checks every subject
against the glossary, every NeXus path against the live NXDL, and every
XDI key against the concept keys the RML mapping actually reads — so a
typo fails the build rather than producing a row that silently never
matches.

**Editing a crosswalk means editing `build_crosswalk.py` and
re-running it**, then re-vendoring into `hdf5metadata/src/hdf5metadata/data/`.

### `exampleData/` — 55 XDI test files

The PtSn catalysis series from Diamond B18, single spectra, and 18
`xdl_*` files selected from the
[XAS Data Library](https://github.com/XraySpectroscopy/XASDataLibrary)
by greedy set cover over edge, beamline, facility, detection mode,
monochromator, temperature regime and absorber Z — so they add variety
the corpus lacked rather than repeating it. See `exampleData/README.md`.

### `exampleMetadata/` — generated CDIF-XAS

55 JSON-LD documents plus batch generation and validation reports.
**Output, not source**: regenerate with the commands above rather than
editing. 55/55 validate against `release/`.

The same 55 files converted by the *other* pipeline live in
[`hdf5metadata/exampleMetadata-xdi`](https://github.com/usgin/hdf5metadata),
not here. Both sets validate 55/55; the two are kept so the
implementations can be compared on identical inputs, which is what
`cdif-xas-UKDS/CONVERGENCE-PROPOSAL.md` argues from.

### `archive/`

| item | what it is |
|---|---|
| `XAS-CDIF-1.0_release/` | the published 1.0 deliverable, from the GitHub tag |
| `XAS_Glossary_SKOS.json` | the v1 glossary, superseded by `XAS_Glossary_SKOS_v2_draft.json` |
| `se_na2so4-testschemaorg-cdiv3.jsonLD` | hand-authored record, does not validate against the current profile |

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
| `XAS_Glossary_SKOS_v2_draft.json` | **the concept hub.** Every crosswalk subject resolves here; `build_crosswalk.py` validates against it |
| `XAS_detectionmodes_SKOS.json` | transmission, fluorescence, electron yield, HERFD … |
| `XAS_edges_SKOS.json` | K, L1, L2, L3 … |
| `XAS_emissionlines_SKOS.json` | emission lines for HERFD and PFY |
| `XAS_Glossary.xlsx` | the spreadsheet the glossary is curated in |

These are the shared dependency. `hdf5metadata` does not read them
directly — it consumes the crosswalks, which `build_crosswalk.py`
validates against the glossary. So a concept renamed here breaks the
crosswalk build, which is the intended failure mode: it surfaces at
build time rather than as silently unmapped data.

### Analysis and mapping documents

| file | content |
|---|---|
| `DescriptionOfCDIF-XAS-profile.md` | the profile in prose |
| `XAS_Glossary_vs_NeXus_analysis.md` | glossary against the NeXus definitions, including where they do not align |
| `XAS-CDIFImplementation-revised.xlsx` | the implementation mapping |
| `XAS-Nexus-CDIFImplementation.xlsx` | NeXus → CDIF working sheet |
| `XAS-XDI-CDIFImplementation.xlsx` | XDI → CDIF working sheet |
| `XDI-CDIF-Mapping.xlsx`, `XDI-CDIF-Mapping_STikhonov.xlsx` | earlier XDI mapping drafts |
| `XDIVariablesInCDIF.txt` | XDI variable inventory |
| `XDISpec-FieldsCDIF-Schema.orgMapping.docx` | XDI spec fields against schema.org |
| `CDIF4XAS_Mappings_Intro.pdf` | introduction to the mappings |
| `Ravel_2016_*.pdf` | reference paper |
| `PhysicalDataset.png` | diagram |

## Dependency summary

```
XAS_Glossary_SKOS_v2_draft.json          (concepts)
        │  validated against
        ▼
crosswalk/build_crosswalk.py  ──────►  crosswalk/*.sssom.tsv
                                              │  vendored into
                                              ▼
                                    hdf5metadata/src/hdf5metadata/data/

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
