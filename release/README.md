# CDIF XAS Document Profile — XAS-CDIF release 1.1

Document-level CDIF profile for X-ray Absorption Spectroscopy datasets. This
directory contains the release artifacts for the `cdif/xasDocument/1.1`
conformance URI, released in XAS-CDIF 1.1. The profile and its XAS tiers
were 1.0 before this release; a document now declares `xasCore/1.1`, and
one declaring `xasCore/1.0` does not validate.

## Conformance URI

`https://w3id.org/cdif/xasDocument/1.1`

## What this profile composes

| Component | Conformance URI | Role |
|-----------|-----------------|------|
| [CDIF Core](https://w3id.org/cdif/core/1.1) | `cdif/core/1.1` | Mandatory dataset discovery content |
| [CDIF Discovery](https://w3id.org/cdif/discovery/1.1) | `cdif/discovery/1.1` | Optional discovery content (spatial, temporal, etc.) |
| [CDIF Data Description](https://w3id.org/cdif/data_description/1.1) | `cdif/data_description/1.1` | Measured variables and their semantics |
| [CDIF Data Structure](https://w3id.org/cdif/data_structure/1.1) | `cdif/data_structure/1.1` | Physical / logical / tabular data structure |
| [XAS Core](https://w3id.org/cdif/xasCore/1.1) | `cdif/xasCore/1.1` | XAS-mandatory analysis activity, instruments and measurement technique; sample shape |
| [XAS Optional](https://w3id.org/cdif/xasOptional/1.1) | `cdif/xasOptional/1.1` | XAS-recommended propertyIDs for data columns, beamline, sample and analysis activity; no requirements |

A conforming XAS document declares five of these URIs in
`schema:subjectOf.dcterms:conformsTo` — all but `xasOptional/1.1`, which
adds no requirements and so is not declared. A document whose
distribution has `schema:hasPart` entries also declares
`https://w3id.org/cdif/manifest/1.1`.

## Files

- **[CDIFXASDocumentImplementationGuide.md](CDIFXASDocumentImplementationGuide.md)** — full implementation guide (classes, properties, XAS-specific requirements).
- **[cdifXASDocumentResolvedSchema.json](cdifXASDocumentResolvedSchema.json)** — JSON Schema (Draft 2020-12) with all `$ref`s inlined for standalone use. This is the validation target. (The structured form, with `$ref`s preserved, is kept in the [mBB source](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/profiles/cdifCompositeProfile/xasDocument) as `xasDocumentSchema.json`; it is not shipped here because its relative `$ref`s resolve only inside the building-blocks tree.)
- **[xasDocumentRules.shacl](xasDocumentRules.shacl)** — aggregated SHACL shapes from all six composed components (~2000 triples). Aggregated by `metadataBuildingBlocks/tools/validate_shacl.py --emit-shapes`.
- **[cdifXASDocument-frame.jsonld](cdifXASDocument-frame.jsonld)** — JSON-LD frame for extracting the Dataset node from a graph before JSON Schema validation.
- **[xasToCdifWorkflows.md](xasToCdifWorkflows.md)** — the two implementations
  that produce conforming documents (NeXus/HDF5 and XDI), how to run each,
  and which to integrate into a workflow system.
- The concept-keyed intermediate `cdifnexmetadata` builds before emitting
  CDIF, and what a new input format (another NeXus application definition,
  say) has to produce, are described in the
  [repository README](https://github.com/CDIF-4-XAS/XAS-CDIF/blob/main/README.md#the-concept-keyed-intermediate-and-how-to-add-an-input-format).
- **[crosswalk/](crosswalk/)** — the machine-readable mappings: XDI keys
  and NeXus paths to CDIF XAS concepts (SSSOM), XDI headers to schema.org,
  concept units, and where each concept is placed in a CDIF document. Its
  README describes each file. Copies of the repository's `crosswalk/*.tsv`,
  written by the same build.
- **[vocabularies/](vocabularies/)** — the three value-list vocabularies
  (absorption edges, emission lines, detection modes), SKOS concept schemes
  generated from the NeXus definitions. Copies of the repository's
  `XAS_*_SKOS.json`, written by the same build.
- **[XAS_Glossary_SKOS_v2.json](XAS_Glossary_SKOS_v2.json)** — the released
  snapshot of the CDIF XAS glossary (SKOS concept scheme
  `https://w3id.org/cdif/xas/CDIF4XAS_Reference_Concepts`, version 1.1),
  copied from the working `XAS_Glossary_SKOS.json` at the repository root.
  Documents use its concept URIs as `schema:propertyID` values.
- **[glossaryProvenance.md](glossaryProvenance.md)** — where the XAS
  vocabularies come from, how they were built, what is generated versus
  curated, the SSSOM crosswalks, and open items.
- **[FrameAndValidate.py](FrameAndValidate.py)** — utility script: frame + validate against the schema in one pass.
- **[examples/](examples/)** — validated XAS document instances.
- **[LICENSE](LICENSE)**, **[LICENSES/](LICENSES/)** and
  **[REUSE.toml](REUSE.toml)** — licensing for this folder on its own,
  REUSE-compliant: the profile, guides, crosswalks and value lists
  CC-BY-4.0 (World Fair CDIF working group); the examples, the glossary
  snapshot and this README CC0-1.0; `FrameAndValidate.py` Apache-2.0, as in
  the CDIF validation repository it is copied from.

## Examples

The `examples/` directory contains 14 XAS document instances. All pass
the JSON Schema and have no SHACL violations:

- **`exampleCDIFxas.json`** and **`example_dds_framed.jsonld`** — the
  reference examples from mBB, copied by the release sync.
- **`cdif_dds_framed.jsonld`** — the UKDS/Dataverse-derived example (originally
  from [UKDSResearch/cdif-xas](https://github.com/UKDSResearch/cdif-xas)),
  adapted to conform (see the change log kept alongside the file in mBB).
- **`valid.jsonld`**, **`valid_angle_dspacing.jsonld`**,
  **`262875_PtSn_OCO_Abu_1.jsonld`** and **`Se_Na2SeO4_rt_01.jsonld`** —
  output of the reference XDI pipeline.
- **`FeXAS.jsonld`**, **`cu_metal_rt.jsonld`**, **`cu_metal_10K.jsonld`**,
  **`feo_rt1.jsonld`**, **`pt_metal_rt.jsonld`** and
  **`NXxas-manual-sketch.jsonld`** — NeXus/HDF5 (`NXxas`) sources, from
  [`cdifnexmetadata`](https://github.com/CDIF-4-XAS/cdifnexmetadata)
  (`exampleMetadata-NEXUS/`). Columns are located with
  `cdif:LocatorMapping` (an HDF5 path) rather than a column index.
- **`CeO2.jsonld`** — an XDI source converted by `cdifnexmetadata`
  rather than by the RML pipeline.

The implementation guide's "Complete examples" section says what each one
is for.

## Framing + JSON Schema validation

```bash
# Frame a document, then validate against the schema
python FrameAndValidate.py examples/exampleCDIFxas.json --validate

# Just frame and save output
python FrameAndValidate.py examples/exampleCDIFxas.json -o framed.json

# Pass the schema explicitly (auto-detected by default, since it is the
# only *Schema*.json in this directory)
python FrameAndValidate.py input.jsonld --validate \
    --schema cdifXASDocumentResolvedSchema.json
```

The JSON Schema validates one dataset record at a time. If your source is a
multi-record bundle (`{ "@graph": [ ... ] }`), extract each record via
framing before validating — that's what `FrameAndValidate.py` does.

## SHACL validation

Load `xasDocumentRules.shacl` alongside the RDF representation of the
document (e.g., via `pyshacl`) to run the full profile's SHACL checks. The
same rules are already exercised by the mBB `validate_shacl.py` when it
targets the `xasDocument` composite.

## Source

Release artifacts are built from the metadataBuildingBlocks composite at
[`_sources/profiles/cdifCompositeProfile/xasDocument`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/profiles/cdifCompositeProfile/xasDocument).
Refresh them from a metadataBuildingBlocks checkout on `main`, with this
repository checked out beside it:

```bash
# In the metadataBuildingBlocks repo:
python tools/sync_release_repos.py --repo XAS-CDIF/release          # dry run
python tools/sync_release_repos.py --apply --repo XAS-CDIF/release
```

The sync copies the resolved schema and the mBB examples and emits
`xasDocumentRules.shacl`. It does not touch the frame, the implementation
guide or the release-only examples: copy `frame.jsonld` to
`cdifXASDocument-frame.jsonld` by hand when it changes.

## Status

The schema, SHACL and frame match metadataBuildingBlocks `main`, and the
implementation guide was checked against them on 2026-10-26. The guide's
closing status note lists what is still open.
