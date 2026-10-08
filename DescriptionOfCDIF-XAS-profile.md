# Implementing the CDIF XAS profile

Review and minor updates SMR 2026-07-17; revised 2026-10-08 against the
`xasDocument/1.0` release in `release/`.

This is an overview in prose. The normative statement is the resolved JSON
Schema and SHACL rules in `release/`, and the class-by-class detail is in
`release/CDIFXASDocumentImplementationGuide.md`. The JSON snippets below are
taken from documents that validate against `release/`:
`release/examples/example_dds_framed.jsonld`, `exampleMetadata/` (the RML
converter) and `cdifnexmetadata` (the NeXus converter).

The "[Dictionary of XAS Data Interchange Metadata](https://github.com/XraySpectroscopy/XAS-Data-Interchange/blob/master/specification/dictionary.md#defined-items-in-the-element-namespace)" specifies that these fields are required:

* Element.symbol: The element of the absorbing atom.
* Element.edge: The absorption edge measured.
* Mono.d\_spacing: The d-spacing of the monochromator.

Element symbol and element edge are considered properties of the analysis event because a given instrument in a given configuration can analyze for different elements and edges. They are implemented as keywords (see section 4); a `schema:about` property on each keyword identifies the XDI field it carries, and the profile requires it.

Mono.d\_spacing is a property of the monochromator component in the XAS analysis instrument. It is implemented as an additionalProperty (`xas:dspacing`) of the monochromator, which is one of the instruments listed in the `prov:wasGeneratedBy/prov:used` list.

## Namespaces

| prefix | IRI |
|---|---|
| `schema:` | `http://schema.org/` |
| `prov:` | `http://www.w3.org/ns/prov#` |
| `dcterms:` | `http://purl.org/dc/terms/` |
| `dcat:` | `http://www.w3.org/ns/dcat#` |
| `cdi:` | `http://ddialliance.org/Specification/DDI-CDI/1.0/RDF/` |
| `cdif:` | `https://w3id.org/cdif/` |
| `xas:` | `https://w3id.org/cdif/xas/` (the CDIF XAS glossary) |
| `nxs:` | `https://manual.nexusformat.org/classes/` |
| `wd:` | `https://www.wikidata.org/entity/` |
| `xsd:` | `http://www.w3.org/2001/XMLSchema#` |

Every `xas:` term is a concept in the published glossary at
`https://w3id.org/cdif/xas/` (106 concepts; source `XAS_Glossary_SKOS.json`).
A propertyID is the concept's local name, spelled exactly as the glossary
does: `xas:edgeenergy`, `xas:spotsize`, not `edge_energy` or `spot_size`.

## Conformance

The root Dataset carries a `schema:subjectOf` catalog record that declares
the profiles the document conforms to:

```json
"schema:subjectOf": {
    "@type": ["schema:Dataset"],
    "schema:additionalType": [{"@id": "dcat:CatalogRecord"}],
    "schema:about": {"@id": "<the root Dataset @id>"},
    "dcterms:conformsTo": [
        {"@id": "https://w3id.org/cdif/core/1.1"},
        {"@id": "https://w3id.org/cdif/discovery/1.1"},
        {"@id": "https://w3id.org/cdif/data_description/1.1"},
        {"@id": "https://w3id.org/cdif/data_structure/1.1"},
        {"@id": "https://w3id.org/cdif/xasCore/1.0"}
    ]
}
```

`xasOptional/1.0` is not declared: that module adds no required content, so a
claim to conform to it is vacuous and cannot be checked.

## 1\. Define variables

Describe variables that are reported in the dataset. Following the CDIF discovery profile, these are reported in `schema:variableMeasured`. Each is typed both `schema:PropertyValue` and `cdi:InstanceVariable`:

```json
{
    "@id": "ex:DV/BYSPHH/iv/Column_1",
    "@type": ["cdi:InstanceVariable", "schema:PropertyValue"],
    "schema:name": "energy",
    "schema:alternateName": ["mono energy"],
    "schema:description": "mono energy",
    "schema:propertyID": [{"@id": "xas:monochromatorenergy"}],
    "schema:unitText": "eV",
    "cdif:uses": ["https://example.org/struct/DV/BYSPHH/rv/Column_1"]
}
```

* `schema:name`: the label for the variable as it appears in the dataset, e.g. an XDI column name.
* `schema:alternateName` (an array): a human-intelligible label.
* `schema:propertyID` (an array of `{"@id": …}`): the concept that defines the semantics of the variable, a glossary concept such as `xas:monochromatorenergy`, `xas:incidentintensity` or `xas:transmittedintensity`. Where the file gives nothing to identify the concept, the converters use the OGC nil IRI `http://www.opengis.net/def/nil/OGC/0/missing` rather than omit it.
* `schema:unitText`: the unit as the file records it.
* `cdif:uses` (an array): links the instance variable to the represented variable that the data structure defines (section 3).

The physical data type of the values is stated on the physical mapping (section 3), not on the variable.

## 2\. Analysis Event

Describe the data acquisition event. In this version, we are focused on the acquisition of data at synchrotron beamlines. Data processing to produce final data products is a subsequent provenance step, which would be described in a separate JSON object in the `prov:wasGeneratedBy` array (TBD).

The event is a `schema:Action` that is also a `prov:Activity`, classified with `xas:analysisevent`:

```json
"@type": ["schema:Action", "prov:Activity"],
"schema:additionalType": [{"@id": "xas:analysisevent"}]
```

It has various properties (besides the regular name and description):

* `schema:startTime`, `schema:endTime`: ISO 8601 timestamps of the acquisition. When the scan ran belongs on the activity, not as `schema:temporalCoverage` on the dataset.
* `prov:used`: the instruments used to acquire data. The instrumentation is described as one `prov:used` wrapper per component, each holding its instrument in a `schema:instrument` array. Every instrument has `prov:Entity` in its `@type` and `wd:Q3099911` (Wikidata "scientific instrument") in its `schema:additionalType`, beside a component type:

  ```json
  {
      "@type": ["schema:Thing", "prov:Entity"],
      "schema:instrument": [{
          "@type": ["schema:Thing", "schema:Product", "prov:Entity"],
          "schema:additionalType": [{"@id": "xas:source"}, {"@id": "wd:Q3099911"}],
          "schema:name": "APS bending magnet source",
          "schema:additionalProperty": [
              {"@type": ["schema:PropertyValue"], "schema:name": "X-ray source",
               "schema:propertyID": [{"@id": "nxs:base_classes/NXsource.html#nxsource-type-field"}],
               "schema:value": "Synchrotron X-ray Source"},
              {"@type": ["schema:PropertyValue"], "schema:name": "Probe",
               "schema:propertyID": [{"@id": "nxs:base_classes/NXsource.html#nxsource-probe-field"}],
               "schema:value": "x-ray"}
          ]
      }]
  }
  ```

  The components, and what each must carry:

  | component | additionalType | required additionalProperty |
  |---|---|---|
  | X-ray source | `xas:source` | source type and probe (the probe entry is named "Probe") |
  | monochromator | `xas:xraymonochromator` | `xas:dspacing`, `xas:monochromatortype`, `xas:reflectionplane` |
  | beamline | `nxs:base_classes/NXinstrument.html` | none required; optionally `xas:flux`, `xas:spotsize`, `xas:scanmode`, `xas:energyrange`, `xas:energyresolution`, `xas:collimation`, `xas:focusing`, `xas:harmonicrejection`, `xas:website` |
  | detector / monitor | `xas:xraymonitor` | none required |

* sample. The sample is documented as the `schema:object` of the action; it's what the analysis is all about. It is typed `["schema:Product", "schema:Thing"]` with the iSamples material-sample type in `schema:additionalType`, and carries its own properties as additionalProperty: `xas:samplepreparation`, `xas:samplechemicalcomposition`, temperature, `xas:pressure`, `xas:magneticfield`, `xas:electricfield`, `xas:concentration` and others from the glossary. Environmental conditions such as temperature, pressure and field are properties of the sample, not of the event.
* facility: the facility where the analysis event took place is represented as an organization contributor (`schema:roleName` "Facility") in the root dataset section; both converters emit this. The NeXus converter also records it as the event's `schema:location`, a `schema:Place` classified `xas:facility`; the profile permits this but does not require it. Additional properties specific to the facility (as opposed to the particular experiment) should be specified in the contributor element.
* additionalProperty. Other properties of the analysis event itself: `xas:edgeenergy` (the energy of the measured edge), and `xas:calibrationmethod`, `xas:experimentdocumentation`, `xas:installedoptions`.

**Retired terms.** On 2026-09-27 four technique-neutral terms were retired onto NeXus base classes. Both spellings validate, and the converters still emit the old ones; new documents should use the NeXus form:

| retired | preferred |
|---|---|
| `xas:beamline` | `nxs:base_classes/NXinstrument.html` |
| `xas:xraysourcetype` | `nxs:base_classes/NXsource.html#nxsource-type-field` |
| `xas:probe` | `nxs:base_classes/NXsource.html#nxsource-probe-field` |
| `xas:temperature` | `nxs:base_classes/NXsample.html#nxsample-temperature-field` |

`xas:facility` was deliberately not retired: it covers synchrotron, XFEL and laboratory facilities, where NeXus `NXsource` is the storage ring specifically.

## 3\. Data Structure

The structure of the data in XDI and NeXus files is quite different, even though the target content is closely related. The data structure is defined in the `schema:distribution` (`schema:DataDownload`) section, because it is specific to the particular data delivery file format. The distribution's `dcterms:conformsTo` names the format: the XDI specification, or the NeXus application definition (e.g. `nxs:applications/NXxas.html`).

Each component of the structure is defined by a represented variable, and the distribution's `cdif:hasPhysicalMapping` says where its values are. Each mapping points back to the instance variable it formats with `cdif:formats_InstanceVariable`, and states `cdif:physicalDataType`, the datatype used to represent the values.

* **XDI** files are described using a `cdi:WideDataStructure`, with one component per column in the data section of the XDI file, each a `cdi:MeasureComponent` linked to its variable with `cdif:isDefinedBy_Variable`. The information in the header section of the XDI file is all accounted for in other elements in the JSON-LD document. The free text comments section of the XDI file (between `#////` and `#----`) should be copied to the dataset description (with whitespace removed). Each column is located with a `cdif:TextMapping`:

  ```json
  {
      "@type": ["cdif:TextMapping"],
      "cdif:index": 1,
      "cdi:minimumLength": 15,
      "cdi:maximumLength": 15,
      "cdif:physicalDataType": "decimal",
      "cdif:formats_InstanceVariable": {"@id": "ex:DV/BYSPHH/iv/Column_1"}
  }
  ```

  `cdif:index` is the 1-based column. The two lengths are the field width measured over the data rows, **including** the padding in front of the value. Where they are equal the file is genuinely fixed-width and a reader can slice on the widths: the column with index 3 starts after the widths of columns 1 and 2. Where they differ the file is whitespace-separated and a reader must tokenise. Do not assume either: 21 of the 55 files in `exampleData/` are fixed-width and 34 are not. The distribution also carries `cdi:arrayBase`, `cdi:isFixedWidth`, `cdi:isDelimited`, `cdi:commentPrefix` and `cdi:hasHeader`.

* **NeXus** files use the HDF5 file format. This is a binary format that requires HDF5 software tools to extract information. Python code to use data in this format can be implemented using the h5py package (https://docs.h5py.org/en/stable/), and there are various pre-compiled tools for working with HDF5 files at https://support.hdfgroup.org/documentation/hdf5/latest/\_view\_tools\_command.html. The ability to access and use these tools is a prerequisite for using NeXus data. The content of NeXus files is specified by NeXus application definitions (https://manual.nexusformat.org/classes/applications/). This profile follows the restructured `NXxas` family, which defines transmission, total and partial electron yield, total and partial fluorescence yield, and HERFD detection; the crosswalk in `crosswalk/cdifxas-to-nexus.sssom.tsv` maps each glossary concept to its NeXus field. Spectral data in NeXus files is stored in HDF5 datasets as one-dimensional arrays, one for the incident energy and one for each measured response. The structure is a `cdi:DimensionalDataStructure`, and each component's values are located with a `cdif:LocatorMapping` carrying the HDF5 path:

  ```json
  {
      "@type": ["cdif:LocatorMapping"],
      "cdi:locator": "/FeFoil.001/data/mutrans",
      "cdif:physicalDataType": "xsd:decimal",
      "cdif:formats_InstanceVariable": {"@id": "ex:DV/FeXAS/iv/absorptioncoefficient"}
  }
  ```

  A NeXus file that holds several measurements (several `NXentry` groups) is described with one `schema:hasPart` per entry, each carrying its own structure and its own analysis event; see "A file holding several datasets" in the implementation guide.

* raw data (proposed, not implemented). The NeXus file might include a raw data array, either in a scan or collection HDF5 group. This array will have a row for each incident energy step, and a column for each recorded datum. The labels for columns in this array should be included in a dataset in the group named 'columns'. In the data structure description, this could be documented as a component that is itself a `cdi:WideDataStructure`, with an HDF5 path to the raw data array, with appropriate shape like \[nenergy, ncol] and dimension 2. Each column in this raw data array could be described as a component defined by instance variables, but to keep it simple, the raw data array can be described in text. Neither converter produces this today, and the profile does not constrain it.

## 4\. Other information

* Measurement technique. `schema:measurementTechnique` is required, with two `schema:DefinedTerm` entries: the XAS technique from PaNET, and the detection mode:

  ```json
  "schema:measurementTechnique": [
      {"@type": ["schema:DefinedTerm"], "schema:name": "Transmission",
       "schema:inDefinedTermSet": "nxs:Field/NXxas/ENTRY/DATA/mode"},
      {"@type": ["schema:DefinedTerm"], "schema:name": "X-Ray Absorption Spectroscopy",
       "schema:termCode": "XAS",
       "schema:identifier": "http://purl.org/pan-science/PaNET/PaNET01196",
       "schema:inDefinedTermSet": "http://purl.org/pan-science/PaNET/PaNET.owl"}
  ]
  ```

* Proposal. An identifier for the proposal that initiated the work can be linked using `schema:relatedLink`:

  ```json
  "schema:relatedLink": [{
      "@type": ["schema:LinkRole"],
      "schema:linkRelationship": "projectProposal",
      "schema:target": {
          "@type": ["schema:EntryPoint"],
          "schema:encodingType": "text/html",
          "schema:name": "name of the proposal",
          "schema:url": "https://example.org/locatorForProposalText"
      }
  }]
  ```

  An identifier for the proposal can be added to the target as text or with the `schema:PropertyValue` pattern.

* Keywords. Put the target element and the target edge in keywords, each a `schema:DefinedTerm` tagged with `schema:about` to say which XDI field it carries:

  ```json
  "schema:keywords": [
      {
          "@type": ["schema:DefinedTerm"],
          "schema:name": "K-edge",
          "schema:termCode": "K",
          "schema:inDefinedTermSet": "https://github.com/XraySpectroscopy/XAS-Data-Interchange/blob/master/specification/dictionary.md",
          "schema:about": "element.edge"
      },
      {
          "@type": ["schema:DefinedTerm"],
          "schema:name": "Selenium",
          "schema:termCode": "Se",
          "schema:identifier": "http://sweetontology.net/matrElement/Selenium",
          "schema:inDefinedTermSet": "http://sweetontology.net/matrElement",
          "schema:about": "element.symbol"
      }
  ]
  ```

  The SWEET ontology is a handy resource for URIs for elements, but ChEBI URIs could be used as well. Other keywords, such as a subject classification, can be added alongside.

* AdditionalProperty. The schema.org additionalProperty element is used to assign values for various metadata elements that have no schema.org equivalent. Each is a `schema:PropertyValue`:

  ```json
  {
      "@type": ["schema:PropertyValue"],
      "schema:propertyID": [{"@id": "nxs:base_classes/NXsource.html#nxsource-probe-field"}],
      "schema:name": "Probe",
      "schema:value": "x-ray"
  }
  ```

  The propertyID is an IRI reference (`{"@id": …}`, in an array) that identifies the semantics of the property. It is either a CDIF XAS glossary concept, which dereferences to a SKOS concept definition at `https://w3id.org/cdif/xas/<localname>`, or, for the retired terms above, the NeXus base-class field. The schema:name should be a human-intelligible label for the property; a schema:description is recommended if something is available. The schema:value contains the value. If the value has units of measure, give the unit as the file recorded it in `schema:unitText`; `schema:unitCode` may add a QUDT unit IRI, and `crosswalk/cdifxas-units.tsv` lists the unit for each concept that has one.
