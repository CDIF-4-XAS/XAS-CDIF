# XAS-CDIF 1.0 release — examples

Validated example XAS metadata records demonstrating the
[`cdif/xasDocument/1.0`](https://w3id.org/cdif/xasDocument/1.0) profile.

## JSON-LD examples

Every JSON / JSON-LD file here passes both JSON Schema validation
(`cdifXASDocumentResolvedSchema.json`) and SHACL validation
(`xasDocumentRules.shacl`) against the release-package artifacts.

| File | Subject | Notes |
|------|---------|-------|
| `exampleCDIFxas.json` | K-edge XAS of Fe metal | Reference example maintained in the mBB `xasDocument` composite. |
| `cdif_dds_framed.jsonld` | K-edge XAS of Na2SeO4 (Se_Na2SeO4_rt_01) | Adapted from the UKDS/Dataverse `cdif-xas` prototype. See [CHANGES-from-UKDS.md](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/blob/main/_sources/profiles/cdifCompositeProfile/xasDocument/CHANGES-from-UKDS.md) for the transformation log. |
| `CDIF-XAS-Full.json` | Full-coverage XAS example | Exercises every additionalType, propertyID, and additionalProperty enum in the xasCore + xasOptional vocabularies. |
| `se_na2so4-testschemaorg-cdiv3.jsonLD` | K-edge XAS of Na2SeO4 (v3-updated) | Modernized from the CDIF v3 draft example: same subject and identifier (`xas:485749`) as the original v3 file, restructured to conform to `xasDocument/1.0` and carry the v3-era sample-chemistry additionalProperty content (sample preparation, porosity, activity pressure). |

## Data payload

`se_na2so4_rt.xdi` is the raw XDI-format data payload described by
`se_na2so4-testschemaorg-cdiv3.jsonLD` above. It is included so the
metadata example and the file it documents can be reviewed together — the
`schema:sameAs` link in the metadata resolves to this file within the
release folder.

## Regenerating from mBB

The three JSON-LD examples other than `se_na2so4-testschemaorg-cdiv3.jsonLD`
are copies of source-of-truth files maintained in the mBB `xasDocument`
composite at
[`_sources/profiles/cdifCompositeProfile/xasDocument`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/profiles/cdifCompositeProfile/xasDocument).
If they drift, mBB is authoritative — re-copy from there:

```bash
SRC=.../metadataBuildingBlocks/_sources/profiles/cdifCompositeProfile/xasDocument
DEST=XAS-CDIF-1.0_release/examples
cp $SRC/exampleCDIFxas.json   $DEST/exampleCDIFxas.json
cp $SRC/CDIF-XAS-Full.json    $DEST/CDIF-XAS-Full.json
cp $SRC/example_dds_framed.json $DEST/cdif_dds_framed.jsonld     # renamed to match user-facing name
```
