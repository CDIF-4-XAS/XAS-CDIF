# CDIF XAS Document Profile Implementation Guide

**Version 1.1** — 2026-07-26

**Conformance URI:** `https://w3id.org/cdif/xasDocument/1.0`

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
  - [Measurement technique (`schema:measurementTechnique`)](#measurement-technique-schemameasurementtechnique)
  - [Element and edge keywords (`schema:keywords`)](#element-and-edge-keywords-schemakeywords)
- [XAS-optional content](#xas-optional-content)
  - [Data-array `variableMeasured`](#data-array-variablemeasured)
  - [Beamline-operational additionalProperty](#beamline-operational-additionalproperty)
  - [Sample physico-chemical additionalProperty](#sample-physico-chemical-additionalproperty)
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
| XAS Core | `cdif/xasCore/1.0` | XAS-mandatory instrument, sample, activity, technique, keywords |
| XAS Optional | `cdif/xasOptional/1.0` | XAS-recommended: data-array variables, beamline-operational and sample physico-chemical additionalProperty vocabularies |

Full JSON Schema, SHACL rules, JSON-LD frame, and example documents for
each component are in that component's release repo (see [Related
documents](#related-documents)).


## How to declare conformance

Every valid XAS document places a `schema:subjectOf` catalog record on the
root Dataset, and that record declares conformance to all six URIs:

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
        { "@id": "https://w3id.org/cdif/xasCore/1.0" },
        { "@id": "https://w3id.org/cdif/xasOptional/1.0" }
    ]
}
```

The `xasOptional/1.0` line is present even when the document uses none of
its optional content — the URI declares "these vocabularies are
understood," not "at least one is used."


## Model overview

The information model for the CDIF base profiles is defined in the
[CDIF book](https://cross-domain-interoperability-framework.github.io/cdifbook/).
The XAS extension model is documented in the mBB source at
[`_sources/xasProperties/`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/xasProperties)
and summarized below. Naming, cardinalities, and required-vs-optional
distinctions are the authoritative source of truth in the release-repo
JSON Schema (`cdifXASDocumentStructuredSchema.json`) and SHACL rules
(`xasDocumentRules.shacl`).

An XAS document describes:

1. **A dataset** (`schema:Dataset` root) — discoverable metadata (name,
   identifier, license, access), the same shape any CDIF document uses.
2. **Its measured variables** — `schema:variableMeasured` items describing
   what was recorded (energy, i0, itrans, etc.) with their propertyIDs
   pointing at XAS SKOS concepts.
3. **Its physical structure** — via `cdi:isStructuredBy` and
   `cdif:hasPhysicalMapping` on the distribution, tying each column to a
   RepresentedVariable and InstanceVariable so the file can be parsed
   deterministically.
4. **How it was generated** — a `prov:wasGeneratedBy` activity of type
   `xas:analysisevent` whose `prov:used` array lists the beamline, X-ray
   source, monochromator, and monitor as peer instruments.
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
- `schema:Thing` + `schema:Product` — instruments
- `schema:Thing` + `schema:Product` — samples (with additional
  `MaterialSample` via `schema:additionalType`)
- `schema:PropertyValue` — additional-property carriers
- `schema:DataDownload` + `cdi:PhysicalDataSet` — distributions

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
    { "@id": "xas:beamline" },
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
| `csvw` | `http://www.w3.org/ns/csvw#` | tabular structure detail |
| `xas` | `https://w3id.org/cdif/xas/` | XAS SKOS glossary (concept URIs) |
| `nxs` | `https://manual.nexusformat.org/classes/` | NeXus ontology (NXsource, NXcrystal, NXmonitor) |
| `skos` | `http://www.w3.org/2004/02/skos/core#` | SKOS |
| `geosparql` | `http://www.opengis.net/ont/geosparql#` | spatial |
| `time` | `http://www.w3.org/2006/time#` | temporal |

The full context is served at `https://w3id.org/cdif/xasDocument/1.0/context`
once the `.htaccess` rule is added (see release checklist).


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
- `cdif:hasPhysicalMapping` on each DataStructureComponent: where that
  component's values sit, as a `cdif:LocatorMapping` carrying
  `cdif:locator` and a `cdif:formats_InstanceVariable` back-reference.

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
| a path into a container | `cdif:LocatorMapping` | `cdif:locator` |

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
the CDIF-4-XAS reference corpus, 21 are fixed-width by the test above
and 34 are not. A profile-wide claim either way would be wrong for most
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

The subsections below list the requirements *added* by `xasCore/1.0`. They
are enforced by the SHACL rules in `xasDocumentRules.shacl` and by
targeted JSON Schema constraints; see the mBB source at
[`_sources/xasProperties/xasCore/`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/xasProperties/xasCore).

### Root Dataset requirements

The root `@type` array MUST include `schema:Dataset`. `schema:Product` is
permitted (some XAS documents also describe the dataset-as-product for a
data provider) but is not required.

### XAS analysis activity (`prov:wasGeneratedBy`)

An XAS document MUST carry a `prov:wasGeneratedBy` array with at least one
activity that has:

- `@type`: `["schema:Action", "prov:Activity"]`
- `schema:additionalType`: `[{"@id": "xas:analysisevent"}]`
- `schema:object`: the material sample being analyzed (see [Sample entity](#sample-entity-schemaobject))
- `schema:startDate` (recommended): ISO 8601 timestamp of the acquisition
- `prov:used`: an array of instrument wrappers (see [Instrument entities](#instrument-entities))
- `schema:additionalProperty` (recommended): `xas:edgeenergy` value of the
  measured edge, plus other analysis-scale properties like
  `xas:calibrationmethod`

### Instrument entities

The `prov:used` array on the analysis activity is the **peer prov:used
instrument model**: one wrapper per instrument, each carrying a single
`schema:instrument`. Every wrapper has:

```json
{
    "schema:instrument": {
        "@type": ["schema:Thing", "schema:Product"],
        "schema:additionalType": [ { "@id": "xas:<component-URI>" } ],
        "schema:name": "...",
        "schema:additionalProperty": [ ... ]
    }
}
```

Required component wrappers (`schema:additionalType` `@id` value):

| Component | `xas:` additionalType | Required additionalProperty |
|-----------|-----------------------|-----------------------------|
| X-ray source | `xas:source` | `xas:xraysourcetype`, `xas:probe` |
| Beamline | `xas:beamline` | *(none required at xasCore; xasOptional adds `xas:collimation`, `xas:focusing`, `xas:harmonicrejection`)* |
| Monochromator | `xas:xraymonochromator` | `xas:dspacing`, `xas:monochromatortype`, `xas:reflectionplane` |
| X-ray monitor / detector | `xas:xraymonitor` | *(none required at xasCore; xasOptional adds detector-configuration entries)* |

The exact XAS local names are documented in the
[XAS SKOS glossary](#xas-skos-glossary). NeXus-ontology `nxs:Field/NX*/*`
paths are recognized in the SKOS mappings and may also be used as
`schema:propertyID` values.

### Sample entity (`schema:object`)

The `schema:object` of the analysis activity is a
[`xasSample`](https://github.com/Cross-Domain-Interoperability-Framework/metadataBuildingBlocks/tree/main/_sources/xasProperties/xasSample):

- `@type`: `["schema:Thing", "schema:Product"]`
- `schema:additionalType` MUST include the iSample material-sample URI:
  `[{"@id": "https://w3id.org/isample/vocabulary/materialsampleobjecttype/materialsample"}]`
- `schema:name`: required
- `schema:additionalProperty` (recommended): `xas:samplepreparation`,
  plus any physico-chemical parameters from [xasOptional](#sample-physico-chemical-additionalproperty)

### Distribution (`schema:distribution`)

At least one distribution MUST be typed as `cdi:PhysicalDataSet` and
conform to the XDI specification:

```json
"@type": ["schema:DataDownload", "cdi:PhysicalDataSet"],
"dcterms:conformsTo": [
    { "@id": "https://github.com/XraySpectroscopy/XAS-Data-Interchange/blob/master/specification/spec.md" }
]
```

`cdi:isStructuredBy` on that distribution, with
`cdif:hasPhysicalMapping` on each of its components, supplies the
column-to-variable mapping expected by the Data Structure profile. An
XDI file holds one spectrum, so the structure belongs to the
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

Two DefinedTerm entries are required:

- Acquisition mode (`Transmission`, `Fluorescence`, `Electron yield`, ...)
  with `schema:inDefinedTermSet` pointing at
  `nxs:Field/NXxas/ENTRY/DATA/mode`.
- XAS technique classification with
  `schema:identifier: "http://purl.org/pan-science/PaNET/PaNET01196"` and
  `schema:inDefinedTermSet: "http://purl.org/pan-science/PaNET/PaNET.owl"`,
  `schema:termCode: "XAS"`, `schema:name: "X-Ray Absorption Spectroscopy"`.

### Element and edge keywords (`schema:keywords`)

Two DefinedTerm entries are required:

- Absorption edge (K, L1, L2, L3, ...) with
  `schema:inDefinedTermSet: "https://github.com/XraySpectroscopy/XAS-Data-Interchange/blob/master/specification/dictionary.md"`,
  `schema:termCode` giving the edge code, `schema:about: "element.edge"`.
- Target element with `schema:identifier` pointing at the SWEET matrElement
  entry, `schema:inDefinedTermSet: "http://sweetontology.net/matrElement"`,
  `schema:termCode` giving the two-letter symbol,
  `schema:about: "element.symbol"`.


## XAS-optional content

None of the following is required; use where applicable. Enforced only
by presence-conditional shape constraints in `xasDocumentRules.shacl`.

### Data-array `variableMeasured`

Optional `cdi:InstanceVariable` / `schema:PropertyValue` items describing
the columns of an XDI data array. Documented `xas:` propertyIDs:

`energy`, `i0`, `itrans`, `ifluor`, `irefer`, `mutrans`, `mufluor`,
`murefer`, `normtrans`, `normfluor`, `normrefer`, `chi`, `chi_re`,
`chi_im`, `chi_mag`, `chi_pha`, `k`, `r`, `angle`.

### Beamline-operational additionalProperty

Carried on the beamline instrument entity. Recommended `xas:` propertyIDs:

`flux`, `spot_size`, `website`, `energy_range`, `energy_resolution`,
`scan_mode`, `collimation`, `focusing`, `harmonicrejection`.

### Sample physico-chemical additionalProperty

Carried on the `schema:object` sample. Recommended `xas:` propertyIDs:

`temperature`, `pressure`, `ph`, `eh`, `concentration`, `density`,
`viscosity`, `porosity`, `opacity`, `resistivity`, `magnetic_field`,
`magnetic_moment`, `electric_field`, `electrochemical_potential`,
`volume`.


## XAS SKOS glossary

All `xas:*` propertyID and additionalType values are XAS SKOS concept URIs.
The glossary is served through w3id with content negotiation:

- Browser: `https://w3id.org/cdif/xas/samplepreparation` → HTML fragment
- JSON-LD: same URI with `Accept: application/ld+json`, or the explicit
  `.../jsonld` suffix, → per-concept SKOS JSON-LD file
- Root `https://w3id.org/cdif/xas/` → single-page HTML glossary index
  (or the master SKOS JSON with `Accept: application/ld+json`)

Source: [smrgeoinfo/XAS-CDIF](https://github.com/smrgeoinfo/XAS-CDIF).


## Producer resilience patterns

Real-world XDI (and other-source) inputs commonly diverge from what the
xasDocument profile assumes — headers absent, values in non-canonical
form, blank-node identifiers that JSON validators reject. Producers
generating xasDocument-conforming output benefit from a small set of
defensive patterns that keep the document validation-clean without
faking data. Patterns 1–5 below are extracted from the CDIF-XAS
reference pipeline in [smrgeoinfo/cdif-xas](https://github.com/smrgeoinfo/cdif-xas)
(branch `local-xdi-input`), where each solves a class of failure
observed on a 37-file real-world XDI corpus.

**Sentinel-value conventions used throughout:**

- `"Missing"` — text placeholder for a required `schema:name` /
  identifier-string field when the source is genuinely absent.
- `"unknown"` — text placeholder for a required numeric / enumerated
  field where a domain expert must supply the real value later
  (e.g. `Mono.d_spacing` for a monochromator whose crystal cut is
  known but whose d-spacing value wasn't captured).
- `<http://www.opengis.net/def/nil/OGC/0/missing>` — IRI sentinel
  (from the [OGC Rainbow](http://www.opengis.net/def/nil/OGC/0/missing)
  nil-value vocabulary) for required URI-shape values like an absent
  `schema:identifier` on a `DefinedTerm` or an absent Role
  `schema:contributor`.

### Shape safety nets for name-or-identifier constraints

Several CDIF shapes require one of {name, identifier} to be present:

| Class | Shape | If both absent |
|-------|-------|----------------|
| `schema:Person` | `cdifd:CDIFPersonShape` | inject `schema:name = "Missing"` |
| `schema:Organization` | `cdifd:CDIFOrganizationShape` | inject `schema:name = "Missing"` |
| `schema:DefinedTerm` | `cdifd:CDIFDefinedTermShape` | inject `schema:identifier = <OGC nil missing IRI>` |
| `schema:Role` (must have `schema:contributor`) | `cdifd:CDIFRoleShape` | inject `schema:contributor = {@id: <OGC nil missing IRI>}` |

Implement as post-frame passes that recursively walk the framed document,
identify nodes by `@type`, and inject the sentinel only when both
alternatives are absent. Real data is never overwritten.

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
values pass through unchanged so downstream validation still surfaces
them; recognized-but-non-strict inputs no longer make the profile
output fail SHACL date-format checks.


## Complete examples

The `examples/` directory contains XAS document instances. All are
validated clean against `cdifXASDocumentResolvedSchema.json` and
`xasDocumentRules.shacl` (0 errors, 0 SHACL violations) on release.

- **`example_dds_framed.jsonld`** — profile-canonical reference
  maintained in mBB. Complete xasCore + xasOptional content.
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
  `"unknown"`, placeholder creator, placeholder distribution URL).
- **`Se_Na2SeO4_rt_01.jsonld`** — noncompliant XDI (capital-N
  namespaced keys) demonstrating the case-normalization pattern —
  real `Beamline.Name` and `Facility.Name` content flows through.
- **`valid_angle_dspacing.jsonld`** — angle-abscissa fixture
  demonstrating the conditional `Mono.d_spacing` rule (required only
  when the abscissa is monochromator angle or encoder step count,
  optional otherwise).

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
`cdifXASDocumentStructuredSchema.json`.

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
- XAS SKOS glossary — [smrgeoinfo/XAS-CDIF](https://github.com/smrgeoinfo/XAS-CDIF)
- CDIF book — [cdifbook](https://cross-domain-interoperability-framework.github.io/cdifbook/)


---

**Status.** This is a first-cut draft. Sections marked in the TODO
tracker below need review or expansion before a stable 1.0 release:

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
