# CDIF XAS Document Profile — 1.0 Release

Document-level CDIF profile for X-ray Absorption Spectroscopy datasets. This
directory contains the release artifacts for the `cdif/xasDocument/1.0`
conformance URI.

## Conformance URI

`https://w3id.org/cdif/xasDocument/1.0`

## What this profile composes

| Component | Conformance URI | Role |
|-----------|-----------------|------|
| [CDIF Core](https://w3id.org/cdif/core/1.1) | `cdif/core/1.1` | Mandatory dataset discovery content |
| [CDIF Discovery](https://w3id.org/cdif/discovery/1.1) | `cdif/discovery/1.1` | Optional discovery content (spatial, temporal, etc.) |
| [CDIF Data Description](https://w3id.org/cdif/data_description/1.1) | `cdif/data_description/1.1` | Measured variables and their semantics |
| [CDIF Data Structure](https://w3id.org/cdif/data_structure/1.1) | `cdif/data_structure/1.1` | Physical / logical / tabular data structure |
| [XAS Core](https://w3id.org/cdif/xasCore/1.0) | `cdif/xasCore/1.0` | XAS-mandatory instrument + sample metadata |
| [XAS Optional](https://w3id.org/cdif/xasOptional/1.0) | `cdif/xasOptional/1.0` | XAS-recommended metadata (calibration, edge, etc.) |

A conforming XAS document declares all six URIs in
`schema:subjectOf.dcterms:conformsTo`.

## Files

- **[CDIFXASDocumentImplementationGuide.md](CDIFXASDocumentImplementationGuide.md)** — full implementation guide (classes, properties, XAS-specific requirements).
- **[cdifXASDocumentStructuredSchema.json](cdifXASDocumentStructuredSchema.json)** — JSON Schema (Draft 2020-12) with `$ref`s preserved. Regenerable from the mBB source.
- **[cdifXASDocumentResolvedSchema.json](cdifXASDocumentResolvedSchema.json)** — JSON Schema with all `$ref`s inlined for standalone use.
- **[xasDocumentRules.shacl](xasDocumentRules.shacl)** — aggregated SHACL shapes from all six composed components (~2000 triples). Aggregated by `metadataBuildingBlocks/tools/validate_shacl.py --emit-shapes`.
- **[cdifXASDocument-frame.jsonld](cdifXASDocument-frame.jsonld)** — JSON-LD frame for extracting the Dataset node from a graph before JSON Schema validation.
- **[FrameAndValidate.py](FrameAndValidate.py)** — utility script: frame + validate against the schema in one pass.
- **[examples/](examples/)** — validated XAS document instances.

## Examples

The `examples/` directory contains XAS document instances that conform to
the profile:

- **`exampleCDIFxas.json`** — the reference XAS example from mBB. Passes JSON
  Schema and SHACL cleanly.
- **`cdif_dds_framed.jsonld`** — the UKDS/Dataverse-derived example (originally
  from [UKDSResearch/cdif-xas](https://github.com/UKDSResearch/cdif-xas)),
  adapted to conform (see the change log kept alongside the file in mBB).

## Framing + JSON Schema validation

```bash
# Frame a document, then validate against the schema
python FrameAndValidate.py examples/exampleCDIFxas.json --validate

# Just frame and save output
python FrameAndValidate.py examples/exampleCDIFxas.json -o framed.json

# Override the schema
python FrameAndValidate.py input.jsonld --validate \
    --schema cdifXASDocumentStructuredSchema.json
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
Regenerate them with:

```bash
# In the metadataBuildingBlocks repo:
python tools/resolve_schema.py --file _sources/profiles/cdifCompositeProfile/xasDocument/schema.yaml \
    -o _sources/profiles/cdifCompositeProfile/xasDocument/resolvedSchema.json
python tools/regenerate_schema_json.py
python tools/validate_shacl.py _sources/profiles/cdifCompositeProfile/xasDocument \
    --emit-shapes _sources/profiles/cdifCompositeProfile/xasDocument/rules.shacl
```

## Status

**Draft.** The Implementation Guide is a scaffold — sections marked
"[TODO — XAS-specific content]" need domain-expert content before this is
ready for a 1.0 release tag.
