# CDIF XAS Document Profile Implementation Guide

**Version 1.1** (XAS-CDIF release 1.1) — 2026-10-26

**Conformance URI:** `https://w3id.org/cdif/xasDocument/1.1` (with the
tiers `xasCore/1.1` and `xasOptional/1.1`; all three were 1.0 before
XAS-CDIF release 1.1)

This document describes the CDIF XAS Document Profile — a document-level
profile for X-ray Absorption Spectroscopy datasets serialized as
schema.org / JSON-LD. It composes four CDIF 1.1 base profiles (Core,
Discovery, Data Description, Data Structure) with two XAS-specific tiers
(xasCore mandatory, xasOptional recommended). A conforming XAS document
therefore describes a dataset that is (a) discoverable at internet scale,
(b) describes its measured variables and their semantics, (c) describes
its physical or tabular structure at the byte level, and (d) carries the
XAS-specific instrument, sample, and analysis metadata required to
interpret the spectrum.

## Table of contents

- [Composition](#composition)
- [How to declare conformance](#how-to-declare-conformance)
- [Model overview](#model-overview)
- [Notes on schema.org implementation](#notes-on-schemaorg-implementation)
  - [JSON-LD @type](#json-ld-type)
  - [Object reference](#object-reference)
  - [URI-shape values in propertyID and additionalType](#uri-shape-values-in-propertyid-and-additionaltype)
  - [Repeating values](#repeating-values)
  - [Namespace prefixes and JSON validation](#namespace-prefixes-and-json-validation)
- [Namespaces](#namespaces)
- [Base classes and properties](#base-classes-and-properties)
- [XAS-specific requirements](#xas-specific-requirements)
  - [Root Dataset requirements](#root-dataset-requirements)
  - [XAS analysis activity (`prov:wasGeneratedBy`)](#xas-analysis-activity-provwasgeneratedby)
  - [Instrument entities](#instrument-entities)
  - [Sample entity (`schema:object`)](#sample-entity-schemaobject)
  - [Distribution (`schema:distribution`)](#distribution-schemadistribution)
  - [Units on a variable (`schema:unitText`, `schema:unitCode`)](#units-on-a-variable-schemaunittext-schemaunitcode)
  - [Measurement technique (`schema:measurementTechnique`)](#measurement-technique-schemameasurementtechnique)
  - [Element and edge keywords (`schema:keywords`)](#element-and-edge-keywords-schemakeywords)
- [XAS-optional content](#xas-optional-content)
  - [Data-array `variableMeasured`](#data-array-variablemeasured)
  - [Beamline-operational additionalProperty](#beamline-operational-additionalproperty)
  - [Sample physico-chemical additionalProperty](#sample-physico-chemical-additionalproperty)
  - [Analysis-activity additionalProperty](#analysis-activity-additionalproperty)
- [XAS SKOS glossary](#xas-skos-glossary)
- [Producer resilience patterns](#producer-resilience-patterns)
  - [Shape safety nets for name-or-identifier constraints](#shape-safety-nets-for-name-or-identifier-constraints)
  - [Blank-node identifier materialization](#blank-node-identifier-materialization)
  - [Array-labels-line column back-fill](#array-labels-line-column-back-fill)
  - [XDI header-key case normalization](#xdi-header-key-case-normalization)
  - [Datetime ISO 8601 normalization](#datetime-iso-8601-normalization)
- [Complete examples](#complete-examples)
- [Framing + JSON Schema validation](#framing--json-schema-validation)
- [SHACL validation](#shacl-validation)
- [Related documents](#related-documents)


## Composition

| Component | Conformance URI | Contribution |
|-----------|-----------------|--------------|
| CDIF Core | `cdif/core/1.1` | Mandatory dataset discovery (identifier, name, license, dateModified, url-or-distribution, catalog record) |
| CDIF Discovery | `cdif/discovery/1.1` | Optional discovery (creator, contributor, spatial/temporal coverage, keywords, etc.) |
| CDIF Data Description | `cdif/data_description/1.1` | `schema:variableMeasured` (measured variables and their semantics) |
| CDIF Data Structure | `cdif/data_structure/1.1` | `cdi:isStructuredBy` (physical / logical / tabular structure) |
| XAS Core | `cdif/xasCore/1.1` | XAS-mandatory analysis activity, instruments, technique; sample shape |
| XAS Optional | `cdif/xasOptional/1.1` | XAS-recommended: data-array variables, beamline-operational and sample physico-chemical additionalProperty vocabularies |

Full JSON Schema, SHACL rules, JSON-LD frame, and example documents for
each component are in that component's release repo (see [Related
documents](#related-documents)).


## How to declare conformance

Every valid XAS document places a `schema:subjectOf` catalog record on the
root Dataset, and that record declares conformance to these five URIs:

```json
"schema:subjectOf": {
    "@id": "urn:uuid:xas-record-...",
    "@type": ["schema:Dataset"],
    "schema:additionalType": [
        { "@id": "dcat:CatalogRecord" }
    ],
    "schema:about": { "@id": "..." },
    "dcterms:conformsTo": [
        { "@id": "https://w3id.org/cdif/core/1.1" },
        { "@id": "https://w3id.org/cdif/discovery/1.1" },
        { "@id": "https://w3id.org/cdif/data_description/1.1" },
        { "@id": "https://w3id.org/cdif/data_structure/1.1" },
        { "@id": "https://w3id.org/cdif/xasCore/1.1" }
    ]
}
```

A document whose distribution has `schema:hasPart` entries (see [Where
`cdi:isStructuredBy` belongs](#where-cdiisstructuredby-belongs)) is a
manifest and MUST also declare `https://w3id.org/cdif/manifest/1.1`; the
schema requires it whenever any distribution has parts.

`xasOptional/1.1` is deliberately **not** declared. The xasOptional module
adds no required content — every property it contributes is optional — so
conformance to it is satisfied vacuously by any document, and
`detect_conformance` has no rule that can check such a claim. Declaring it
asserted something neither meaningful nor verifiable, so the requirement was
removed from the schema and the advisory removed from the shapes. The module
itself remains: it documents and permits the optional XAS fields.


## Model overview

The information model for the CDIF base profiles is defined in the
[CDIF book](https://cross-domain-interoperability-framework.github.io/cdifbook/).
The XAS extension model is documented in the mBB source at
[`_sources/xasProperties/`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/xasProperties)
and summarized below. Naming, cardinalities, and required-vs-optional
distinctions are the authoritative source of truth in the release-repo
JSON Schema (`cdifXASDocumentResolvedSchema.json`) and SHACL rules
(`xasDocumentRules.shacl`).

An XAS document describes:

1. **A dataset** (`schema:Dataset` root) — discoverable metadata (name,
   identifier, license, access), the same shape any CDIF document uses.
2. **Its measured variables** — `schema:variableMeasured` items describing
   what was recorded (monochromator energy, incident intensity,
   transmitted intensity, etc.) with their propertyIDs pointing at XAS
   SKOS concepts.
3. **Its physical structure** — via `cdi:isStructuredBy` and
   `cdif:hasPhysicalMapping` on the distribution, tying each column to a
   RepresentedVariable and InstanceVariable so the file can be parsed
   deterministically.
4. **How it was generated** — a `prov:wasGeneratedBy` activity of type
   `xas:analysisevent` whose `prov:used` array lists the beamline, X-ray
   source and monochromator as peer instruments.
5. **What was analyzed** — a `schema:object` sample entity typed as
   `MaterialSample` with iSample additionalType and (optionally)
   physico-chemical additionalProperty entries.


## Notes on schema.org implementation

Content in this section is common to all CDIF profiles; see the base
[CDIF Core Implementation Guide](https://cross-domain-interoperability-framework.github.io/profile-core/CDIFCoreImplementationGuide.html)
for the full discussion.

### JSON-LD @type

Every graph node has a `@type` that specifies its `rdf:type` and drives
expected properties. `@type` is always serialized as an array to allow
extensions to add typing. The XAS profile uses these primary types:

- `schema:Dataset` — the root
- `schema:Action` + `prov:Activity` — the XAS analysis event
- `schema:Thing` + `schema:Product` + `prov:Entity` — instruments
- `schema:Thing` + `schema:Product` — samples (with additional
  `MaterialSample` via `schema:additionalType`)
- `schema:PropertyValue` — additional-property carriers
- `schema:DataDownload` + `cdi:PhysicalDataSet` (or
  `cdi:TabularTextDataSet` / `cdi:StructuredDataSet`) — distributions

### Object reference

A bare URI string on a property is a *literal*, not a link. Object
references are `{"@id": "..."}` objects:

```json
"schema:funder": { "@id": "https://ror.org/021nxhr62" }
```

### URI-shape values in propertyID and additionalType

`schema:propertyID` and `schema:additionalType` follow a JSON-LD IRI
serialization policy enforced by SHACL: if the value's lexical form
matches a URI or CURIE (`scheme:localname`), it MUST be serialized as
`{"@id": "..."}`, not as a string literal. Free-label strings
(`"temperature"`, `"MaterialSample"`) remain valid as strings.
`schema:DefinedTerm` objects (bare or with `@type: schema:DefinedTerm`)
also satisfy the shape. Purpose: URI-shape strings serialized as literals
do not participate in RDF entailment as resource references, which
defeats interoperability.

Examples:

```json
"schema:additionalType": [
    { "@id": "nxs:base_classes/NXinstrument.html" },
    "instrument-nickname"
]

"schema:propertyID": [
    { "@id": "xas:monochromatorenergy" }
]
```

### Repeating values

Any property with 1..\* or 0..\* cardinality is always an array — clients
never have to special-case a scalar.

### Namespace prefixes and JSON validation

The XAS JSON Schema validates one Dataset record at a time. Multi-record
bundles serialized as `{"@graph": [...]}` fail JSON Schema validation
because `@graph` is not in the schema's property list; use the frame
(`cdifXASDocument-frame.jsonld`) and the accompanying `FrameAndValidate.py`
to extract the Dataset from a graph before validating.


## Namespaces

| Prefix | IRI | Role |
|--------|-----|------|
| `schema` | `http://schema.org/` | primary base vocabulary |
| `dcterms` | `http://purl.org/dc/terms/` | conformsTo |
| `dcat` | `http://www.w3.org/ns/dcat#` | CatalogRecord |
| `prov` | `http://www.w3.org/ns/prov#` | provenance activity |
| `cdi` | `http://ddialliance.org/Specification/DDI-CDI/1.0/RDF/` | DDI-CDI data structure |
| `cdif` | `https://w3id.org/cdif/` | CDIF-specific structural predicates (hasPhysicalMapping, etc.) |
| `spdx` | `http://spdx.org/rdf/terms#` | Checksum |
| `xas` | `https://w3id.org/cdif/xas/` | XAS SKOS glossary (concept URIs) |
| `nxs` | `https://manual.nexusformat.org/classes/` | NeXus ontology (NXsource, NXcrystal, NXmonitor) |
| `wd` | `https://www.wikidata.org/entity/` | Wikidata (`wd:Q3099911`, scientific instrument) |
| `skos` | `http://www.w3.org/2004/02/skos/core#` | SKOS |
| `geosparql` | `http://www.opengis.net/ont/geosparql#` | spatial |
| `time` | `http://www.w3.org/2006/time#` | temporal |

The context is not yet served at a w3id URI
(`https://w3id.org/cdif/xasDocument/1.1/context` returns 404), so
documents declare these prefixes in their own `@context`.


## Base classes and properties

The Dataset, Person, Organization, DataDownload, MonetaryGrant,
DataCatalog, ContactPoint, Contributor, PropertyValue,
dcat:CatalogRecord, DefinedTerm, EntryPoint, Labeled Link, LinkRole,
Identifier PropertyValue, spdx:Checksum, and Web API classes are
inherited unchanged from CDIF Core and Discovery. See:

- [CDIF Core IG](https://cross-domain-interoperability-framework.github.io/profile-core/CDIFCoreImplementationGuide.html)
- [CDIF Discovery IG](https://cross-domain-interoperability-framework.github.io/profile-discovery/CDIFDiscoveryImplementationGuide.html)

The Data Description profile adds:

- `schema:variableMeasured`: `cdi:InstanceVariable` items describing measured
  variables. See the [CDIF Data Description IG](https://cross-domain-interoperability-framework.github.io/profile-datadescription/CDIFDataDescriptionImplementationGuide.html).

The Data Structure profile adds:

- `cdi:isStructuredBy`: a `cdi:DataStructure` (Wide, Long, or Cube) with
  `cdi:has_DataStructureComponent` entries. **Where it goes depends on
  what it describes** — see below.
- `cdif:hasPhysicalMapping` on the `schema:DataDownload`: one mapping per
  variable, saying where its values sit in the file, each with a
  `cdif:formats_InstanceVariable` back-reference. A text column is a
  `cdif:TextMapping` and a path into a container is a
  `cdif:LocatorMapping` — see below.

#### Where `cdi:isStructuredBy` belongs

A structure describes the layout of one set of data, so it is asserted
about exactly that:

- **A distribution holding one dataset** — on the `schema:DataDownload`.
  The distribution is then the whole of the data, and its structure is
  the data's structure. A single-entry NeXus file and any XDI file take
  this form, and they carry no `schema:hasPart` at all: with one dataset
  the distribution's dataset *is* the dataset, so a part would repeat
  its name, identifier, url, description and keywords under a second
  `@id`.
- **A distribution holding several datasets** — on each part, not on the
  distribution. An HDF5 file with 26 `NXentry` groups is 26 datasets in
  one container, and they need not share a layout. Asserting one
  structure of the whole distribution would say something of the file
  that is true of only some of its parts.

Where several parts share a layout, state the structure inline on the
first and reference it by `@id` from the others. An `@id` reference
denotes the same node, so a consumer resolving it still finds the
components, and the layout is stated once.

#### Which physical-mapping subclass, and what goes in it

`cdif:hasPhysicalMapping` says how to find a component's values. Which
subclass is right depends on how the values are addressed in the file,
not on which format it is:

| the values are addressed by | subclass | carries |
|---|---|---|
| a position in a line of text | `cdif:TextMapping` | `cdif:index`, and the field width |
| a path into a container | `cdif:LocatorMapping` | `cdi:locator` |

A text column is a position, so `cdif:index` — the 1-based column —
**always** applies, and a locator does not: a column number is not a
path, and writing one would send a reader looking for something that is
not there. A NeXus location is the other way round: `/entry/data/mutrans`
is only actionable through a reader that can open the container, such as
h5py, and there is no column to index.

**State the field width from what the file shows, not from what the
format allows.** Give `cdi:minimumLength` and `cdi:maximumLength`
measured over the data rows:

- **equal** — every row puts the field in the same character range, so
  the file is genuinely fixed-width and a reader can slice on it.
- **a range** — the field varies, so the file is whitespace-separated
  and a reader must tokenise.

Measure to the **end of the field**, not the length of the token. A
fixed-width layout pads on the left, so in

```
       12508.00       2.000000       121961.4
```

the first value is 8 characters and the first field is 15. 15 is the
number a reader slices on; 8 tells it nothing it can use.

XDI is worth the warning here. The specification describes
whitespace-separated columns, and producers differ: of the 55 files in
the CDIF-4-XAS reference corpus, 20 are fixed-width by the test above
and 35 are not. A profile-wide claim either way would be wrong for most
of the corpus, which is why the rule is to measure per file.

The profile has no start-position property, so index plus width is the
whole of what can be said. `cdi:decimalPositions`, `cdi:nullSequence`
and `cdi:numberPattern` are available on the same node where a producer
knows them.

#### Parts are datasets as well as media objects

A part of a distribution is a `schema:MediaObject` — it is an
addressable chunk of one file. Where that chunk is a dataset in its own
right, with its own variables, acquisition and structure, type it as
**both**:

```json
"@type": ["schema:MediaObject", "schema:Dataset"]
```

Asserting `schema:Dataset` brings the CDIF core Dataset requirements
with it: the part needs its own `schema:identifier`, `schema:url` or
`schema:distribution`, `schema:dateModified`, and licence information.
Those are properties of a dataset, and a part claiming to be one should
carry them — a catalogue harvesting parts as datasets cannot index what
it cannot identify. `schema:description` and `schema:keywords` are
recommended for the same reason, and should describe *that part* rather
than repeat the container's summary.

See the [CDIF Data Structure IG](https://cross-domain-interoperability-framework.github.io/profile-datastructure/CDIFDataStructureImplementationGuide.html).


## XAS-specific requirements

The subsections below list the requirements *added* by `xasCore/1.1`. They
are enforced by the SHACL rules in `xasDocumentRules.shacl` and by
targeted JSON Schema constraints; see the mBB source at
[`_sources/xasProperties/xasCore/`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/xasProperties/xasCore).

### Root Dataset requirements

The root `@type` array MUST include `schema:Dataset`. `schema:Product` is
permitted (some XAS documents also describe the dataset-as-product for a
data provider) but is not required.

### XAS analysis activity (`prov:wasGeneratedBy`)

An XAS document MUST carry a `prov:wasGeneratedBy` array, and at least
one of its activities MUST be an XAS analysis event. Other CDIF
provenance activities, such as a later normalization or fitting step,
may sit beside it in the same array; the XAS requirements below apply
to the analysis event only. The analysis event has:

- `@type`: `["schema:Action", "prov:Activity"]`
- `schema:additionalType`: `[{"@id": "xas:analysisevent"}]`
- `schema:object` (recommended): the material sample being analyzed. The
  schema does not require it, but when present it must be an
  [xasSample](#sample-entity-schemaobject)
- `schema:startTime` (recommended), and `schema:endTime` where the source
  records one: ISO 8601 timestamps of the acquisition
- `prov:used`: an array of instrument wrappers (see [Instrument entities](#instrument-entities))
- `schema:additionalProperty` (recommended): `xas:edgeenergy` value of the
  measured edge, plus other analysis-scale properties like
  `xas:calibrationmethod`

#### When the measurement happened, and where that goes

Use `schema:startTime` and `schema:endTime` on the activity, **not
`schema:startDate`**: schema.org gives `startDate` to `Event` and
`CreativeWork`, and this subject is a `schema:Action`. The
`cdifProvActivity` shape asks for `startTime` and `endTime` by name.

**Do not put the acquisition time in `schema:temporalCoverage` on the
dataset.** `temporalCoverage` says what period the data is *about*, and
a spectrum is not about a period — an absorption edge is a property of a
material. A document that declares its acquisition date as coverage will
be returned by a date-range search for data covering that day, which is
a different question from "what was measured that day". The dataset in
these documents carries no `temporalCoverage` at all; the profile allows
it (`sh:minCount 0`) for the cases where a dataset genuinely does cover
an interval.

`schema:dateModified` on the root dataset is a third distinct thing:
when the dataset was last updated **in the form available through the
distribution**. It is not the acquisition time and not the time the
metadata was generated.

Emit all three in ISO 8601. Only `schema:dateModified` is checked: the
`dateModifiedProperty` SHACL shape gives it an ISO 8601 pattern. For
`schema:startTime` and `schema:endTime`, both the JSON Schema and the
SHACL say "ISO8601 date-time" in prose and require only a string, so a
value like `2020-08-10 09:18:48` (a space, not a `T`) validates cleanly
and still throws in a consumer that parses it as a datetime. NeXus files
commonly write exactly that.

#### A file holding several datasets

Where a distribution has `schema:hasPart` entries — which also requires
the `manifest/1.1` conformance claim (see [How to declare
conformance](#how-to-declare-conformance)) — **each part SHOULD
carry its own `prov:wasGeneratedBy`** with its own `schema:startTime` /
`schema:endTime`. The file-level activity then spans the whole file,
which answers "when did this batch run" — a different question from
"when was this spectrum taken". A NeXus file of 26 entries acquired over
three days needs both.

The part's activity SHOULD name its instruments by `@id` rather than
repeating them. A scan series uses one beamline, so 26 inline copies
would assert 26 beamlines; a reference denotes the one node the
file-level activity describes in full:

```json
"prov:wasGeneratedBy": [{
    "@id": "ex:FeXAS/FeFoil.001/acquisition",
    "@type": ["schema:Action", "prov:Activity"],
    "schema:additionalType": [{"@id": "xas:analysisevent"}],
    "schema:startTime": "2020-08-10T09:18:48",
    "schema:endTime": "2020-08-10T09:22:32",
    "prov:used": [{"@id": "ex:FeXAS/used/beamline"}]
}]
```

`prov:used` is not optional here even when the instruments are stated
elsewhere: the `cdifProvActivity` shape requires at least one on **any**
activity reached through `prov:wasGeneratedBy`, and a part's activity is
reached exactly that way.

Every XDI file holds one spectrum, so an XDI-only producer never meets
this case.

### Instrument entities

The `prov:used` array on the analysis activity is the **peer prov:used
instrument model**: one wrapper per instrument, each carrying its
`schema:instrument` as an array. A wrapper looks like this (the
wrapper's own `@type` is recommended, not required):

```json
{
    "@type": ["schema:Thing", "prov:Entity"],
    "schema:instrument": [ {
        "@type": ["schema:Thing", "schema:Product", "prov:Entity"],
        "schema:additionalType": [
            { "@id": "xas:<component-URI>" },
            { "@id": "wd:Q3099911" }
        ],
        "schema:name": "...",
        "schema:additionalProperty": [ ... ]
    } ]
}
```

Two parts of this are easy to miss, and a document fails without them:

- `prov:Entity` on the instrument's own `@type`, not only on the wrapper,
  because the instrument is what the activity used (`prov:used` has range
  `prov:Entity`).
- `wd:Q3099911` (Wikidata "scientific instrument") in
  `schema:additionalType`, beside the component type. `xasInstrument`
  requires it on every instrument. Declare
  `wd: https://www.wikidata.org/entity/`.

Required component wrappers (`schema:additionalType` `@id` value):

| Component | additionalType | Required on the instrument |
|-----------|----------------|----------------------------|
| X-ray source | `xas:source` | additionalProperty entries for the source type and the probe, each with a `schema:value`; the probe entry's `schema:name` must be `"Probe"` (see below) |
| Beamline | `nxs:base_classes/NXinstrument.html` (retired: `xas:beamline`) | `schema:name` (the beamline name); no additionalProperty is required — see [Beamline-operational additionalProperty](#beamline-operational-additionalproperty) for the recommended ones |
| Monochromator | `xas:xraymonochromator` | `schema:name`, and additionalProperty entries for `xas:monochromatortype`, `xas:dspacing` (with both `schema:value` and `schema:unitText`) and `xas:reflectionplane` |

Other instruments, such as an X-ray monitor or detector, may be added as
further wrappers; the profile places no requirements on them.

**Retired terms.** On 2026-09-27 four technique-neutral terms were
retired onto NeXus base classes (`nxs:` =
`https://manual.nexusformat.org/classes/`). Both spellings validate;
prefer the NeXus form:

| retired | preferred |
|---|---|
| `xas:beamline` | `nxs:base_classes/NXinstrument.html` |
| `xas:xraysourcetype` | `nxs:base_classes/NXsource.html#nxsource-type-field` |
| `xas:probe` | `nxs:base_classes/NXsource.html#nxsource-probe-field` |
| `xas:temperature` | `nxs:base_classes/NXsample.html#nxsample-temperature-field` |

So the X-ray source's required entries are its type and its probe, each
under either propertyID, and the probe entry is named `"Probe"` either
way. `xas:facility` was not retired.

The exact XAS local names are documented in the
[XAS SKOS glossary](#xas-skos-glossary). NeXus-ontology `nxs:Field/NX*/*`
paths are recognized in the SKOS mappings and may also be used as
`schema:propertyID` values.

### Sample entity (`schema:object`)

The `schema:object` of the analysis activity is a
[`xasSample`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/xasProperties/xasSample):

- `@type`: `["schema:Thing", "schema:Product"]`
- `schema:additionalType` MUST include both the string `"MaterialSample"`
  and the iSample material-sample URI:
  `[{"@id": "https://w3id.org/isample/vocabulary/materialsampleobjecttype/materialsample"}, "MaterialSample"]`
- `schema:name`: required, at least 3 characters (SHACL `xasSampleNode`)
- `schema:additionalProperty` (recommended): `xas:samplepreparation`,
  plus any physico-chemical parameters from [xasOptional](#sample-physico-chemical-additionalproperty)

### Distribution (`schema:distribution`)

At least one distribution MUST be typed as a `schema:DataDownload` and
one of `cdi:PhysicalDataSet`, `cdi:TabularTextDataSet` or
`cdi:StructuredDataSet`, and MUST declare the format its bytes follow:
either the XDI specification or a NeXus application definition. For XDI:

```json
"@type": ["schema:DataDownload", "cdi:PhysicalDataSet"],
"dcterms:conformsTo": [
    { "@id": "https://github.com/XraySpectroscopy/XAS-Data-Interchange/blob/master/specification/spec.md" }
]
```

For NeXus, `dcterms:conformsTo` names the application definition, e.g.
`{ "@id": "nxs:applications/NXxas.html" }` (or the full
`https://manual.nexusformat.org/classes/applications/NXxas.html`).

`cdi:isStructuredBy` and `cdif:hasPhysicalMapping` on that distribution
supply the column-to-variable mapping expected by the Data Structure
profile. An XDI file holds one spectrum, so the structure belongs to the
distribution; see "Where `cdi:isStructuredBy` belongs" above for the
multi-dataset case.

### Units on a variable (`schema:unitText`, `schema:unitCode`)

The two are different claims and should not be used interchangeably.

- `schema:unitText` is **what the file recorded** — the string carried by
  a NeXus `units` attribute or an XDI header. Write it only when the
  source actually says so. An empty string asserts that the unit *is*
  the empty string, which a consumer cannot distinguish from a unit
  nobody recorded.
- `schema:unitCode` is **what the concept is**, as an IRI, and is
  appropriate where the file is silent but the quantity's definition is
  not. An absorption coefficient expressed as a ratio is dimensionless
  whatever the file says; no XAS format records that, because to a
  practitioner it goes without saying.

Writing neither is the correct output for a quantity in arbitrary units
— detector intensities are counts, which are neither dimensionless nor
expressible in a unit vocabulary. The three states a consumer must tell
apart are *the file says eV*, *the concept is dimensionless*, and
*nobody knows*; using an empty string collapses the last two.

### Measurement technique (`schema:measurementTechnique`)

Required, with two DefinedTerm entries:

- XAS technique classification with
  `schema:identifier: "http://purl.org/pan-science/PaNET/PaNET01196"` and
  `schema:inDefinedTermSet: "http://purl.org/pan-science/PaNET/PaNET.owl"`,
  `schema:termCode: "XAS"`, `schema:name: "X-Ray Absorption Spectroscopy"`.
  This term is the schema's `default`: it is the same in every XAS
  document, so a producer can always supply it.
- Acquisition mode (`Transmission`, `Fluorescence`, `Electron yield`, ...)
  with `schema:inDefinedTermSet` pointing at
  `nxs:Field/NXxas/ENTRY/DATA/mode`. Where the source does not record
  the mode, give `schema:name: ":unav"` rather than leave the term out
  or guess one from the detectors.

```json
"schema:measurementTechnique": [
    {
        "@type": ["schema:DefinedTerm"],
        "schema:name": "X-Ray Absorption Spectroscopy",
        "schema:termCode": "XAS",
        "schema:identifier": "http://purl.org/pan-science/PaNET/PaNET01196",
        "schema:inDefinedTermSet": "http://purl.org/pan-science/PaNET/PaNET.owl"
    },
    {
        "@type": ["schema:DefinedTerm"],
        "schema:name": "Transmission",
        "schema:inDefinedTermSet": "nxs:Field/NXxas/ENTRY/DATA/mode"
    }
]
```

### Element and edge keywords (`schema:keywords`)

Recommended, not required. xasCore places no requirement on
`schema:keywords`: base CDIF keywords apply, and plain strings are
accepted. For discovery by element and edge, include two DefinedTerm
entries:

- Absorption edge (K, L1, L2, L3, ...) with
  `schema:inDefinedTermSet: "https://github.com/XraySpectroscopy/XAS-Data-Interchange/blob/master/specification/dictionary.md"`,
  `schema:termCode` giving the edge code, `schema:about: "element.edge"`.
- Target element with `schema:identifier` pointing at the SWEET matrElement
  entry, `schema:inDefinedTermSet: "http://sweetontology.net/matrElement"`,
  `schema:termCode` giving the two-letter symbol,
  `schema:about: "element.symbol"`.


## XAS-optional content

The propertyID lists below are recommendations. The JSON Schema lists
each one, but accepts any other propertyID too, so they are documentation
rather than constraints. `schema:variableMeasured` itself is not optional:
the profile requires it at the root (the Data Description component).

### Data-array `variableMeasured`

`cdi:InstanceVariable` / `schema:PropertyValue` items describing the
columns of the data array. Recommended `xas:` propertyIDs, with the XDI
column labels they usually correspond to:

| propertyID | typical XDI column |
|---|---|
| `xas:monochromatorenergy` | `energy` |
| `xas:monochromatorangle` | `angle` |
| `xas:incidentintensity` | `i0` |
| `xas:transmittedintensity` | `itrans` |
| `xas:fluorescenceintensity` | `ifluor` |
| `xas:referenceintensity` | `irefer` |
| `xas:absorptioncoefficient` | `mutrans` |
| `xas:fluorescenceabsorptioncoefficient` | `mufluor` |
| `xas:referenceabsorptioncoefficient` | `murefer` |
| `xas:normalizedtransmissionabsorptioncoefficient` | `normtrans` |
| `xas:normalizedfluorescenceabsorptioncoefficient` | `normfluor` |
| `xas:normalizedreferenceabsorptioncoefficient` | `normrefer` |
| `xas:wavenumber` | `k` |
| `xas:exafsfunction` | `chi` |
| `xas:filteredchimagnitude` | `chi_mag` |
| `xas:filteredchiphase` | `chi_pha` |
| `xas:filteredchireal` | `chi_re` |
| `xas:filteredchiimaginary` | `chi_im` |
| `xas:radialdistance` | `r` |

### Beamline-operational additionalProperty

Carried on the beamline instrument entity. Recommended `xas:` propertyIDs:

`collimation`, `detectortype`, `energyrange`, `energyresolution`,
`flux`, `focusing`, `harmonicrejection`, `scanmode`, `spotsize`,
`website`.

### Sample physico-chemical additionalProperty

Carried on the `schema:object` sample. Recommended propertyIDs:

- the NeXus `NXsample` temperature field,
  `nxs:base_classes/NXsample.html#nxsample-temperature-field` (the
  retired `xas:temperature` is still accepted)
- `xas:` `concentration`, `density`, `eh`, `electricfield`,
  `electrochemicalpotential`, `magneticfield`, `magneticmoment`,
  `opacity`, `parentsample`, `ph`, `porosity`, `pressure`,
  `resistivity`, `samplechemicalcomposition`, `samplecrystalstructure`,
  `samplematerial`, `samplepreparation`, `viscosity`, `volume`
- the NeXus fields `nxs:Field/NXsample/mass`,
  `nxs:Field/NXsample/point_group` and `nxs:Field/NXsample/unit_cell`

### Analysis-activity additionalProperty

Carried on the `xas:analysisevent` activity. Recommended `xas:`
propertyIDs: `edgeenergy`, `calibrationmethod`,
`experimentdocumentation`, `installedoptions`.


## XAS SKOS glossary

All `xas:*` propertyID and additionalType values are XAS SKOS concept URIs.
The glossary is served through w3id with content negotiation:

- Browser: `https://w3id.org/cdif/xas/samplepreparation` → HTML fragment
- JSON-LD: same URI with `Accept: application/ld+json`, or the explicit
  `.../jsonld` suffix, → per-concept SKOS JSON-LD file
- Root `https://w3id.org/cdif/xas/` → single-page HTML glossary index
  (or the master SKOS JSON with `Accept: application/ld+json`)

Source: [CDIF-4-XAS/XAS-CDIF](https://github.com/CDIF-4-XAS/XAS-CDIF).


## Producer resilience patterns

Real-world XDI (and other-source) inputs commonly diverge from what the
xasDocument profile assumes — headers absent, values in non-canonical
form, blank-node identifiers that JSON validators reject. Producers
generating xasDocument-conforming output benefit from a small set of
defensive patterns that keep the document validation-clean without
faking data. Patterns 1–5 below are extracted from the CDIF-XAS
reference pipeline in [smrgeoinfo/cdif-xas](https://github.com/smrgeoinfo/cdif-xas)
(branch `local-xdi-input`), where each solves a class of failure
observed on real-world XDI files (the reference corpus, now 55 files, is
`exampleData/` in CDIF-4-XAS/XAS-CDIF).

**Sentinel-value conventions used throughout:**

- `":unav"` — DataCite's "value unavailable", the text placeholder for
  any required text field the source does not record: a `schema:name`,
  or a value such as `Mono.d_spacing` for a monochromator whose
  d-spacing wasn't captured. Both reference converters write this one
  token (until 2026-10-26 the RML pipeline wrote `"Missing"` and
  `"unknown"`).
- `<http://www.opengis.net/def/nil/OGC/0/missing>` — IRI sentinel
  (from the [OGC Rainbow](http://www.opengis.net/def/nil/OGC/0/missing)
  nil-value vocabulary) for required URI-shape values like an absent
  `schema:identifier` on a `DefinedTerm` or an absent Role
  `schema:contributor`.

### Shape safety nets for name-or-identifier constraints

Several CDIF shapes require one of {name, identifier} to be present:

| Class | Shape | If both absent |
|-------|-------|----------------|
| `schema:Person` | `cdifd:CDIFPersonShape` | inject `schema:name = ":unav"` |
| `schema:Organization` | `cdifd:CDIFOrganizationShape` | inject `schema:name = ":unav"` |
| `schema:DefinedTerm` | `cdifd:CDIFDefinedTermShape` | inject `schema:identifier = <OGC nil missing IRI>` |
| `schema:Role` (must have `schema:contributor`) | `cdifd:CDIFRoleShape` | inject `schema:contributor = {@id: <OGC nil missing IRI>}` |

Implement as post-frame passes that recursively walk the framed document,
identify nodes by `@type`, and inject the sentinel only when both
alternatives are absent. Real data is never overwritten.

A related case is a value that is present but too short for its shape.
The `xasSample` shape requires a sample name of at least 3 characters,
and XDI files often name a foil by its element alone (`Cu`, `Au`, `Pb`
— 9 of the 55 reference files). The reference pipeline appends
" sample" (`Cu sample`) and records what the file said in the dataset
description's conversion notes, so the padding is never mistaken for
the file's own wording.

### Blank-node identifier materialization

JSON-LD framing typically leaves blank-node `@id` values in the `_:xxx`
syntax (e.g. `"@id": "_:b14"`). This is valid RDF but fails plain-JSON
URI-format validators (e.g. Oxygen JSON validation). Rewrite each
unique `_:xxx` to a real IRI under the `ex:` namespace:

```
_:b14  →  ex:blank/b14
```

using the `ex: https://example.org/` prefix already bound in the
context. All references to the same blank node get the same
substitution so subject linkage is preserved.

### Array-labels-line column back-fill

XDI/1.0 specifies both `# Column.N:` compound headers AND a
whitespace-separated array-labels line immediately after `# ---`
(header end). Real files frequently carry only the array-labels line.
Without the `Column.N:` headers, the mapping produces no
`cdi:Column` / `cdi:Column_N` triples, no `cdi:has_DataStructureComponent`,
no `schema:variableMeasured` entries — which breaks the
`cdifDataDescription/1.1` and `cdifDataStructure/1.1` conformance
declarations.

Fix: at parse time, capture the last `#`-prefixed comment line before
the first data row. If the graph has no `cdi:Column` subject after
header parsing, synthesize one `cdi:Column_N` per whitespace-separated
token in that line, each carrying the token as its
`skos:definition`. Downstream mapping produces a complete data
structure from the array-labels alone.

### XDI header-key case normalization

XDI/1.0 canonicalizes header keys as capitalized-namespace +
lowercase-field (`Facility.name`, `Beamline.name`, `Mono.d_spacing`).
Real files often use inconsistent case (`Facility.Name`, `Beamline.Name`,
`Mono.D_Spacing`, `Scan.Start_Time`) which never populates the
canonical `cdi:*_name` / `cdi:Mono_d_spacing` predicates the mapping
looks up.

Fix (one line at parse time):

```python
if '.' in compound_key:
    head, rest = compound_key.split('.', 1)
    compound_key = head + '.' + rest.lower()
```

Keep the first segment as-is (the namespace/class name — `Beamline`,
`Mono`, `Facility` are capitalized in the mapping's RDF vocabulary);
lowercase everything after the first dot.

### Datetime ISO 8601 normalization

`Scan.start_time` and `Scan.end_time` map to schema.org datetime slots
that require strict ISO 8601 with `T` separator. Real files carry
these in space-separated ISO (`2008-04-10 21:58:50`), slash-date
(`2001/06/26 22:27:31`), US m/d/y, date-only, and basic-ISO
(`20080410T215850`) forms. Normalize at parse time (Python 3.11+
`datetime.fromisoformat` handles the space-separated form; the other
forms fall through to explicit `strptime` patterns). Unparseable
values pass through unchanged. Neither the JSON Schema nor the SHACL
checks the format of these two slots (see [When the measurement
happened](#when-the-measurement-happened-and-where-that-goes)), so this
normalization is what keeps them parseable; validation will not catch a
non-strict value.


## Complete examples

The `examples/` directory contains XAS document instances. All are
validated clean against `cdifXASDocumentResolvedSchema.json` and
`xasDocumentRules.shacl` (0 errors, 0 SHACL violations) on release.

- **`example_dds_framed.jsonld`** — profile-canonical reference
  maintained in mBB. It omits the sample (`schema:object`) and the
  wrappers' `@type`, both of which the profile permits.
- **`exampleCDIFxas.json`** — the earlier reference XAS example from
  the mBB xasDocument profile block.
- **`cdif_dds_framed.jsonld`** — a minimal Cu-metal example from the
  reference pipeline. Small; useful for step-by-step reading.
- **`valid.jsonld`** — same minimal Cu-metal file, kept as a
  regression-test fixture (should always be VALID).
- **`262875_PtSn_OCO_Abu_1.jsonld`** — real-world Diamond B18 output.
  Exercises every producer-side resilience pattern (case-normalization,
  case-mismatched Facility/Beamline headers back-filled from
  `Facility.Name`/`Beamline.Name`, `Mono.d_spacing` synthesized as
  `":unav"`, placeholder creator, placeholder distribution URL).
- **`Se_Na2SeO4_rt_01.jsonld`** — noncompliant XDI (capital-N
  namespaced keys) demonstrating the case-normalization pattern —
  real `Beamline.Name` and `Facility.Name` content flows through.
- **`valid_angle_dspacing.jsonld`** — angle-abscissa fixture: the
  abscissa is monochromator angle rather than energy, which is what
  makes the d-spacing necessary to convert it. The profile requires
  `xas:dspacing` in every document regardless of the abscissa.

The following come from `cdifnexmetadata` (its `exampleMetadata-NEXUS/`).
All but `CeO2` describe NeXus/HDF5 files declaring `NXxas`, so their
variables are located with `cdif:LocatorMapping` and an HDF5 path in
`cdif:locator`, not with a column index:

- **`FeXAS.jsonld`** — the fullest NeXus example: one file holding 26
  `NXentry` scans (GSECARS, APS 13-ID-E), described as an archive of
  parts. One `schema:Dataset`, one `schema:DataDownload`, 26
  `schema:MediaObject` parts sharing data structures by `@id`, and
  manifest conformance declared.
- **`cu_metal_rt.jsonld`** — a clean single-spectrum NeXus file; the
  smaller thing to read first.
- **`feo_rt1.jsonld`**, **`pt_metal_rt.jsonld`** — single-spectrum NeXus
  files of measurements also held as XDI in `exampleData/`, so the two
  encodings can be compared on the same data.
- **`cu_metal_10K.jsonld`** — the thinnest: the file declares `NXxas`
  and records almost none of it, so missing required values (detection
  mode among them) are stated as `":unav"`.
- **`NXxas-manual-sketch.jsonld`** — from a file built to the layout the
  NeXus manual sketches for `NXxas`, which no real file uses; shows how
  little maps from it.
- **`CeO2.jsonld`** — an XDI file converted by `cdifnexmetadata` rather
  than by the RML pipeline, for comparison with the XDI examples above.

The transformation from the original UKDS reference to the framing +
schema shape of the profile is logged in the mBB source
([CHANGES-from-UKDS.md](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/blob/main/_sources/profiles/cdifCompositeProfile/xasDocument/CHANGES-from-UKDS.md)).


## Framing + JSON Schema validation

```bash
python FrameAndValidate.py examples/exampleCDIFxas.json --validate
```

The script frames the input against `cdifXASDocument-frame.jsonld` (which
extracts the Dataset node from `@graph` bundles and standardizes the
key ordering) and then runs the JSON Schema check against
`cdifXASDocumentResolvedSchema.json`.

Requirements: `pyld`, `jsonschema` (`pip install pyld jsonschema`).


## SHACL validation

`xasDocumentRules.shacl` is the aggregated shapes graph over all six
composed components (~2000 triples from 41 source rules.shacl files).
Run with pyshacl or your validator of choice against the RDF
representation of the document:

```bash
pyshacl -s xasDocumentRules.shacl -f table \
    -df json-ld examples/exampleCDIFxas.json
```


## Related documents

- Base profile IGs (referenced above) — [Core](https://cross-domain-interoperability-framework.github.io/profile-core/), [Discovery](https://cross-domain-interoperability-framework.github.io/profile-discovery/), [Data Description](https://cross-domain-interoperability-framework.github.io/profile-datadescription/), [Data Structure](https://cross-domain-interoperability-framework.github.io/profile-datastructure/)
- XAS Core BB — [`_sources/xasProperties/xasCore`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/xasProperties/xasCore)
- XAS Optional BB — [`_sources/xasProperties/xasOptional`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/xasProperties/xasOptional)
- XAS SKOS glossary — [CDIF-4-XAS/XAS-CDIF](https://github.com/CDIF-4-XAS/XAS-CDIF)
- CDIF book — [cdifbook](https://cross-domain-interoperability-framework.github.io/cdifbook/)


---

**Status.** Checked against the release schema and SHACL on
2026-10-26, after metadataBuildingBlocks `1e91846` made the analysis
activity and `schema:measurementTechnique` required and
`schema:keywords` optional. Open items:

- Fill in a worked walkthrough of `exampleCDIFxas.json` illustrating each
  required XAS component in-context.
- Expand the "Instrument entities" table with recommended NeXus paths per
  component.
- Confirm the exact PaNET/SWEET URIs for measurementTechnique and element
  keywords are stable and dereferenceable.
- Add UML or block diagrams (see `assets/` in the mBB composite for
  starting material).
- Cross-check every requirement in this document against the SHACL shape
  it corresponds to in `xasDocumentRules.shacl`.
