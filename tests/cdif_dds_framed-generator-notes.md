# `cdif_dds_framed.jsonld` — CDIF XAS generator notes (for Deirdre)

Tracks changes to the framed CDIF XAS instance so the **generator code** can be updated.
Target: validate against the **xasCore/1.0** mandatory tier and the **XASdata** composite profile
(schemas live in `metadataBuildingBlocks/_sources/xasProperties/xasCore/` and
`.../profiles/cdifCompositeProfile/XASdata/`).

Status (2026-07-17): `conformsTo` now declares `https://w3id.org/cdif/xasCore/1.0`.
Validation: **6 errors vs xasCore/1.0**, **7 vs XASdata** (the extra is the `xas:` namespace).

---

## Already correct (keep generating these)
- `@context` `cdif` → `https://w3id.org/cdif/` (was `https://cdif.org/0.1/`)
- `@context` `nxs` → `https://manual.nexusformat.org/classes/`
- `schema:subjectOf.@id` is a real IRI (`ex:dataset/DV/BYSPHH/metadata`), **not** a blank node `_:b25`
- `schema:subjectOf.schema:about.@id` points at the root dataset `@id`
- Instruments carry a `schema:name` (≥3 chars)
- Root `@type: ["schema:Dataset"]` is now **accepted** — xasCore was relaxed so `schema:Product` is optional (no longer required on the root)
- Distribution is XDI-conformant (`dcterms:conformsTo` → `.../XAS-Data-Interchange/.../spec.md`); `cdif:hasPhysicalMapping`, variableMeasured InstanceVariables — all fine

### Generator conventions added 2026-07-17 (valid open-world extras)
- **`schema:about` on keyword DefinedTerms** — tags which XDI dictionary field the keyword
  represents, e.g. `"schema:about": "Element.edge"` on the edge term and
  `"schema:about": "Element.symbol"` on the element term. A soft-typing/traceability hint;
  permitted (keyword items allow additional properties). *Does not by itself satisfy gap #3* —
  the element term still needs `schema:name` + `schema:inDefinedTermSet`.
- **`schema:description` on the `edge_energy` additionalProperty** — human-readable explanation
  of the edge-energy value; permitted, no schema impact.

## Generator changes still needed

### 1. Provenance activity `@type` + `schema:additionalType`  ·  *root cause of 1 error*
```
current:  "@type": ["schema:Event", "prov:Activity"]
needed:   "@type": ["schema:Action", "prov:Activity"],
          "schema:additionalType": ["xas:AnalysisEvent"]
```
Use `schema:Action` (not `Event`). The XAS domain type `xas:AnalysisEvent` now goes
in **`schema:additionalType`** (a list), **not** in `@type` — `@type` holds only the
standard schema.org / PROV types. As of 2026-07-17 xasCore composes the `xasGeneratedBy`
building block, which **requires** the activity to carry `schema:additionalType`
containing `xas:AnalysisEvent`.

### 2. Instrument wrapper — NXsource + NXmonochromator in `schema:hasPart`  ·  *1 error*
Current `prov:used[0].schema:instrument` is a **list** of instrument entities whose
`schema:additionalProperty` carry beamline props (`xas:collimation`, `xas:focusing`, …), with
**no `schema:hasPart`**. xasCore requires:
```
prov:used: [
  { "schema:instrument": {                          # object, not a list
      "@type": ["schema:Thing","schema:Product"],
      "schema:name": "...",
      "schema:hasPart": [
        { "@type": ["schema:Thing","schema:Product"],
          "schema:additionalType": "nxs:BaseClass/NXsource",
          "schema:additionalProperty": [
            { "@type":"schema:PropertyValue","schema:propertyID":["nxs:Field/NXsource/type"], "schema:value":"..." },
            { "@type":"schema:PropertyValue","schema:propertyID":["nxs:Field/NXsource/probe"], "schema:name":"Probe","schema:value":"x-ray" }
          ] },
        { "@type": ["schema:Thing","schema:Product"],
          "schema:additionalType": "nxs:BaseClass/NXmonochromator",
          "schema:additionalProperty": [
            { "...":"nxs:Field/NXcrystal/type ..." },
            { "...":"nxs:Field/NXcrystal/d_spacing (+ schema:unitText) ..." },
            { "...":"nxs:Field/NXcrystal/reflection ..." }
          ] }
      ] } }
]
```
Required: `schema:instrument` is an **object** with `schema:hasPart` (≥2 items) containing an
**NXsource** component (`type` + `probe`) and an **NXmonochromator** component
(`type` + `d_spacing` + `reflection`). Beamline props can be an additional hasPart component
(`schema:additionalType: xas:Beamline`).

### 3. Keywords — element + edge as full DefinedTerms, no plain strings  ·  *4 errors*
xasCore requires **every** `schema:keywords` item to be a `DefinedTerm` object with
`schema:name` + `schema:inDefinedTermSet`, and the set must contain an **element** term
(SWEET) and an **edge** term (XDI dictionary).
- `K-edge` term — OK (has name + XDI-dictionary `inDefinedTermSet`).
- `Se` element term — **add** `schema:name` (e.g. `"Se"`) **and** `schema:inDefinedTermSet: "http://sweetontology.net/matrElement"`.
- `"Earth and Environmental Sciences"` — **plain string, not allowed** under xasCore. Emit subject
  keywords as `DefinedTerm` objects (with name + inDefinedTermSet) or omit them from `schema:keywords`.

### 4. `xas:` namespace binding  ·  *XASdata-only error*
```
current:  "xas": "https://ada.astromat.org/metadata/xas/"
needed:   "xas": "https://xas.org/dictionary/"
```

### 5. (Optional) declare the optional tier
The record carries optional XAS content (data-array variables, beamline/sample additional
properties), so it may also declare `https://w3id.org/cdif/xasOptional/1.0` in `conformsTo`.

---

## Reference
- xasCore instrument/keyword/measurementTechnique constraints: `xasProperties/xasCore/schema.yaml`
- Validated example to model against: `.../profiles/cdifCompositeProfile/XASdata/exampleCDIFxas.json`
- w3id resolution: `https://w3id.org/cdif/xasCore/1.0` (schema / shacl / context sub-paths available)
