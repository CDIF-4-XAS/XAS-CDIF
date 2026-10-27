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

Work happens on the **`cdifxasRelease1.1`** branch, which exists in both
[`CDIF-4-XAS/XAS-CDIF`](https://github.com/CDIF-4-XAS/XAS-CDIF) — the
canonical repository — and `smrgeoinfo/XAS-CDIF`, a fork of it. As of
2026-09-27 the two are at the same commit.

This branch is version 1.1, and goes well beyond the 1.0 deliverable: a
`xasDocument/1.0` release profile, a rebuilt glossary, machine-readable
crosswalks, and a 55-file test corpus with generated metadata. The
published 1.0 files are preserved in `archive/XAS-CDIF-1.0_release/`.

The version numbers are separate: 1.1 numbers this repository's release
(the vocabularies carry `schema:version` 1.1 and the crosswalks
`mapping_set_version` 1.1), while the profile it ships keeps its
conformance URI `xasDocument/1.0`. `cdifxasRelease1.1` is **not yet tagged
or released** — the only tag in the repository is `1.0` — so it is a
working branch rather than a published state, pending sign-off from the
XAS team.

### Remotes, and why there are two

```
origin    https://github.com/CDIF-4-XAS/XAS-CDIF.git   (fetch)
origin    https://github.com/smrgeoinfo/XAS-CDIF.git   (push)
origin    https://github.com/CDIF-4-XAS/XAS-CDIF.git   (push)
upstream  https://github.com/CDIF-4-XAS/XAS-CDIF.git   (fetch + push)
```

`origin` **fetches from `CDIF-4-XAS`** and **pushes to both**, so one
`git push origin` keeps the fork and the canonical repository in step.
(Until 2026-09-27 `origin` fetched from the fork instead, which meant a
commit pushed directly to `CDIF-4-XAS` by anyone else was invisible to
`git pull`.)

The fork exists because Pages could not be enabled on the organisation
repository at the time. It no longer publishes: Pages was enabled on
`CDIF-4-XAS/XAS-CDIF` on 2026-09-29, and the site has been served from
there since (see below).

### What publishes the site, and the one thing to know before moving it

`.github/workflows/build-docs.yml` regenerates the glossary HTML and the
per-concept SKOS files, then deploys `build/docs` to `gh-pages` with
`peaceiris/actions-gh-pages`. That action pushes with `GITHUB_TOKEN`, so
it targets **whichever repository the run belongs to** — and because the
source commit reaches both, both repositories used to build and deploy
independently. The published trees were byte-identical (measured
2026-09-27: same tree hash, zero files differing) while the two
`gh-pages` histories shared no ancestry, which looks like a divergence and
is not one. A job guard now names the single publishing repository:
`CDIF-4-XAS/XAS-CDIF`, since 2026-09-30.

The organisation publishes today, and the w3id rules depend on that:
`XAS_PAGES` in `perma-id/w3id.org` `ids/cdif/.htaccess` resolves
`w3id.org/cdif/xas/*` — including the glossary's own scheme URI
`xas/CDIF4XAS_Reference_Concepts` — to
`https://cdif-4-xas.github.io/XAS-CDIF`. It used to point at the fork
(`smrgeoinfo.github.io`), the only one of the 18 bases in that file on a
personal account; `perma-id/w3id.org#6767` moved it, merged 2026-09-29.
All ten XAS identifier families now resolve through the organisation,
which `validation/tools/check_w3id_redirects.py` checks.

The fork's `gh-pages` is frozen at its last build. Nothing resolves to
it, and it will go stale the next time the glossary changes, so do not
treat it as a live mirror.

**If publication ever moves again, in this order:**

1. Enable Pages on the new repository from `gh-pages`.
2. Confirm the files actually serve there.
3. Repoint `XAS_PAGES`, by PR against `perma-id/w3id.org`.
4. *Then* change the one repository name in the `build-docs.yml` job
   guard.

Repointing w3id before the target serves gives a 303 to a 404, which is
worse than a 303 to a slightly stale file; changing the guard first
freezes whichever site w3id is still pointing at.

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

## Relationship to `cdifnexmetadata`

[`CDIF-4-XAS/cdifnexmetadata`](https://github.com/CDIF-4-XAS/cdifnexmetadata)
is a separate repository: the Python converter that reads NeXus/HDF5 and
XDI files and writes CDIF JSON-LD conforming to the `xasDocument/1.0`
profile. The two divide the work as **specification here, implementation
there**. This repository defines the concepts, the field-to-concept
mappings and the profile. `cdifnexmetadata` applies them to files.

**What `cdifnexmetadata` takes from here:**

| from XAS-CDIF | how it gets there |
|---|---|
| the four crosswalk files in `crosswalk/` (the SSSOM sets and `cdifxas-units.tsv`) | copied into `src/cdifnexmetadata/data/`; `python -m cdifnexmetadata.map.crosswalk --refresh` re-downloads them from this repository's `cdifxasRelease1.1` branch |
| the glossary concept URIs | indirectly: they are the objects of the crosswalks, and become the keys of its intermediate (next section) and the `schema:propertyID` values it emits. It does not read the vocabulary files themselves |
| the `release/` profile | its validation target: `cdifnexmetadata ... --validate --profile-dir ../XAS-CDIF/release` |

**What this repository takes from `cdifnexmetadata`:** one file.
`crosswalk/cdifxas-placement.tsv`, which says where each concept goes in
the CDIF JSON-LD, is derived by `crosswalk/build_placement.py` from
`CONCEPT_SLOTS` in its `emit.py`, read from a sibling checkout at
`../cdifnexmetadata`.

**Where a change belongs:**

- a new or renamed concept: `XAS_Glossary_SKOS.json`, here;
- a field-to-concept mapping: the tables in `crosswalk/build_crosswalk.py`,
  here. Re-run it, push, then `--refresh` in `cdifnexmetadata`;
- where a concept is placed in the JSON-LD: `emit.py` in `cdifnexmetadata`,
  then `build_placement.py` here;
- a profile rule: `metadataBuildingBlocks`, then re-sync `release/`;
- a new input format, or reading an existing one better: code in
  `cdifnexmetadata` (next section).

Its generated examples live in that repository (`exampleMetadata-xdi/`,
`exampleMetadata-NEXUS/`). `exampleMetadata/` here comes from the
cdif-xas RML fork, not from `cdifnexmetadata`.

## The concept-keyed intermediate, and how to add an input format

`cdifnexmetadata` does not go from file to CDIF in one step. It parses the
source into a **concept-keyed intermediate**, the `ConceptRecord`, and then
transforms *that* into CDIF. The intermediate is the contract a new input
format has to meet: adding NeXus `NXsas`, `NXtomo`, or a lab instrument's
own format is a matter of producing one of these, not of touching the
CDIF-emitting code. Paths below (`inspect/`, `map/`, `cli.py`, `emit.py`)
are in the `cdifnexmetadata` repository.

The keys are the CDIF XAS glossary concepts in this repository, so the
concept and the format it arrived in are separate things: a NeXus path and
an XDI token that mean the same thing produce the same key, and the source
field travels beside the value.

(The original cdif-xas RML workflow builds a different intermediate, keyed
on XDI names; it is described in
[`archive/cdif-xas-rml-intermediate.md`](archive/cdif-xas-rml-intermediate.md).)

### The `ConceptRecord`

Dump it for any file:

```bash
uv run cdifnexmetadata scan.nxs --dump-concepts
```

With `-o` pointing at a directory, each input is written as
`<stem>.concepts.json`.

#### Shape

```jsonc
{
  "crosswalk_source": ".../xdi-to-cdifxas.sssom.tsv",  // absolute, machine-specific
  "crosswalk_reason": "XDI binding; the file declares its format on line 1",
  "legacy_source": "",
  "record_count": 1,
  "records": [ /* one per NXentry; an XDI file has exactly one */ ],
  "warnings": []
}
```

`crosswalk_reason` is there because a silent choice between vocabularies
cannot be debugged from the output alone. For a NeXus file it names the
application definition that selected the crosswalk, or says that none
matched and only base-class mappings were used.

Each record:

```jsonc
{
  "entry_name": "scan1",
  "entry_path": "/scan1",          // "/" for XDI
  "definition": "NXxas",           // application definition; null for XDI
  "values": { /* concept URI -> list of values, below */ },
  "bibliographic": { /* schema.org-bound values, below */ },
  "publication_fields": { "Publication.journal": "J. Example Chem." },
  "conversion_notes": ["temperature reported as \"room temperature\""],
  "warnings": ["11 header(s)/column(s) had no crosswalk entry: ..."]
}
```

#### `values` — the part that matters

Keys are **CDIF XAS glossary concept URIs** as CURIEs. Each maps to a
*list*, because a file may state a concept more than once.

```jsonc
"cdifxas:beamline": [
  {
    "value": "13-BM-D",
    "units": null,
    "source_path": "#Beamline.Name",   // "/entry/instrument/name" for NeXus
    "predicate": "skos:exactMatch",    // from the SSSOM row
    "confidence": 1.0,
    "is_array": false,
    "shape": [],
    "dtype": "",
    "note": "Name of the beamline."
  }
]
```

An array-valued concept — a data column, or an HDF5 dataset that was
described but not read:

```jsonc
"cdifxas:incidentintensity": [
  {
    "value": null,               // deliberately not read; this is data
    "units": null,
    "source_path": "#column:3",
    "predicate": "skos:exactMatch",
    "confidence": 1.0,
    "is_array": true,
    "shape": [469],
    "dtype": "float64",
    "label": "i0",               // what the source called it
    "long_name": "i0",           // NeXus long_name, where the writer set one
    "index": 3,                  // 1-based column, tabular sources only
    "width": [13, 13],           // observed field width, min/max
    "note": "Data column: incident beam intensity."
  }
]
```

| field | meaning |
|---|---|
| `value` | the scalar, or `null` for an array |
| `units` | as the source stated them, or supplied from the XDI dictionary |
| `source_path` | where in the file it came from — an HDF5 path, or `#Header.tag` / `#column:N` |
| `predicate` | the SSSOM predicate that licensed the mapping |
| `confidence` | `1.0` for an `exactMatch`; a `closeMatch` carries less |
| `is_array`, `shape`, `dtype` | set when the concept is an array that was described, not read |
| `label`, `long_name` | names the source gave it; used to name the emitted variable |
| `index`, `width` | position in a tabular source |
| `note` | the crosswalk row's comment, plus any conversion note |
| `convention` | set when the value came from the legacy path table, naming the writer convention that put it there |

Optional fields appear only when set, so a scalar stays short.

Arrays are described and not read on purpose: the shape is what the
data-structure profile needs, and the numbers are data. A new parser
should do the same.

#### `bibliographic`

Values the crosswalk bound to a **schema.org property** rather than to a
concept, keyed by the property CURIE. Kept apart from `values` because a
serialization target is not a concept.

```jsonc
"bibliographic": {
  "schema:license":    { "value": "https://creativecommons.org/licenses/by/4.0/" },
  "schema:identifier": { "value": "10.1021/...", "source_path": "#Publication.DOI" },
  "schema:author":     { "value": "Smith, J. and Jones, A.",
                         "predicate": "skos:closeMatch", "confidence": 0.8 }
}
```

Populated only by the XDI binding, from `xdi-to-schemaorg.sssom.tsv`. A NeXus
file carries no bibliographic fields, so a NeXus parser can ignore this.

### Adding an input format

In `cdifnexmetadata`, in this order:

1. **Write an inspector** under `inspect/` that reads the format into
   whatever plain structure suits it. It should know nothing about CDIF or
   about concepts.
2. **Write a mapper** under `map/` that turns that into a `ConceptRecord`,
   setting `source_path`, `predicate` and `confidence` on every value.
   This is where the format's vocabulary meets the glossary.
3. **Supply a crosswalk**, not code, for the field-to-concept
   correspondence: an SSSOM TSV whose subjects are your format's field
   names and whose objects are glossary concepts.
4. **Dispatch** in `cli.py` on what the file declares rather than on its
   extension.

`emit.py` should need no change. If it does, the concept being mapped is
probably missing from the glossary — add it there rather than
special-casing the emitter.

#### For another NeXus application definition, only step 3 applies

The NeXus inspector and mapper already walk any NXDL tree, and
`select_crosswalk()` picks a crosswalk from the `definition` the file
declares — so a folder of mixed techniques needs no per-file
configuration. A new application definition is therefore a crosswalk TSV
whose objects are NXDL paths, and nothing else.

`cdifsas-to-nexus.sssom.tsv` (in `cdifnexmetadata`'s `src/cdifnexmetadata/data/`) exists as proof: small-angle scattering
(`NXsas` — a different application definition from `NXxas`, not a
misspelling of it) was added as a crosswalk with no code change at all.
Pass it with `--crosswalk` and an `NXsas` file yields concepts, variables
and a data structure.

##### Writing the crosswalk

Subjects are concept CURIEs, objects are NXDL paths:

```
cdifsas:detectordistance  ->  nxdl:NXsas/ENTRY:NXentry/INSTRUMENT:NXinstrument/DETECTOR:NXdetector/distance
cdifsas:wavelength        ->  nxdl:NXmonochromator/wavelength
```

- The first segment after `nxdl:` is the **application definition**
  (`NXsas`) or a **base class** (`NXmonochromator`).
- Middle segments are `PLACEHOLDER:NXclass`. Matching is on the *class*;
  the placeholder name is the NXDL's own and is a hint, not a
  requirement, because real writers rarely use it.
- The last segment is the field name.

The two row kinds behave differently, and this is the part worth knowing
before writing any:

**An application-definition row** is rooted at the entry, so its path
leads with a `:NXentry` segment. It applies only to files declaring that
definition.

**A base-class row** is relative to an instance of the class and does not
lead with `:NXentry`. It applies to **any** definition — which is why a
file declaring something no crosswalk covers still yields facility,
beamline, probe and source type. That classification is structural, not
by name: testing `startswith("NXxas")` instead would silently class every
non-XAS definition as a base class and apply `NXsas` paths to XAS files.

Map more than one path to the same concept where writers disagree; the
first that resolves wins. `cdifsas:scatteringintensity` has two rows,
one for `DETECTOR:NXdetector/data` and one for `DATA:NXdata/data`.

Map only what the file contains. `Q`, the scattering vector, has no row
because a raw `NXsas` file does not carry it — it is computed from
wavelength, distance and pixel geometry, and a row for it would map
something that does not exist.

If a concept is technique-neutral, **reuse the existing CURIE rather than
re-minting it**. The SAS crosswalk keeps five `cdifxas:` subjects
unchanged — `facility`, `beamline`, `probe`, `xraysourcetype` and
`temperature` — none of which is an XAS concept. SSSOM identifies
concepts rather than namespaces, so re-minting them under `cdifsas:`
would assert that a SAS facility and an XAS facility are different
things. They are not. That they sit in an XAS-flavoured namespace is an
accident of which crosswalk was written first; writing the second one is
what exposed it, and the fix is a technique-neutral term rather than a
duplicate here.

That fix has since been made for four of the five. On 2026-09-27
`beamline`, `probe`, `xraysourcetype` and `temperature` were deprecated
in the glossary in favour of NeXus base-class terms
(`dcterms:isReplacedBy`, e.g. `NXinstrument.html` for `beamline`), and
the xasDocument profile accepts either spelling. `facility` was kept.
The crosswalks still key these values on the `cdifxas:` subjects, which
remain valid CURIEs for the deprecated concepts.

`docs/NXsas.md` in `cdifnexmetadata` covers what NXsas is and how real
files depart from the definition.

A file whose definition no crosswalk covers is therefore a thin document
rather than a failure, and `crosswalk_reason` in the dump is the only
place that says which happened.

#### Check your work by reading the intermediate

```bash
uv run cdifnexmetadata new_format_file.ext --dump-concepts
```

A concept absent from that dump will be absent from the CDIF document, and
nothing downstream will say so. That is the failure mode this whole
pipeline is arranged around: an unmapped field produces no output and no
error, and a document that is missing half its metadata validates exactly
as well as one that is complete.

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
| `xdi-to-schemaorg.sssom.tsv` | XDI extension header → schema.org property | `cdifnexmetadata`, which keeps a copy |
| `cdifxas-units.tsv` | CDIF XAS concept → QUDT unit | `cdifnexmetadata`, which keeps a copy |
| `cdifxas-placement.tsv` | CDIF XAS concept → place in CDIF JSON-LD | readers; derived from `cdifnexmetadata`'s `emit.py` |
| `build_crosswalk.py` | builds the first four, and validates them | — |
| `build_placement.py` | builds `cdifxas-placement.tsv` from `emit.py` | — |

[`crosswalk/README.md`](crosswalk/README.md) describes each file, its
columns, and how to rebuild it.

`xdi-to-schemaorg.sssom.tsv` holds the bibliographic and rights headers seen in
XDI data that CDIF models with schema.org rather than with an XAS concept.
It is kept apart from `xdi-to-cdifxas` so each set has a single
`object_source`.

**These files are the master copies.** `cdifnexmetadata` does not read them
from here at run time — it ships duplicates under
`src/cdifnexmetadata/data/`, so that it works offline and so a given
release is pinned to a known crosswalk revision. The cost is that the
copies can fall behind; `python -m cdifnexmetadata.map.crosswalk --refresh`
re-downloads all four.

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
  `cdi:locator`. Used for NeXus, where the path is only actionable
  through a reader such as h5py.

The two lengths are the field width **including the padding in front of
the value**, because that is what a fixed-width reader slices on: in
`       12508.00` the value is 8 characters and the field is 15. Where
minimum and maximum are equal the file really is fixed-width; where they
differ it is whitespace-separated and a reader must tokenise.

That distinction is not decorative. **20 of the 55 files in
`exampleData/` are fixed-width and 35 are not**, so neither claim holds
for the corpus as a whole and the widths have to be measured per file.
The two implementations derive them independently and agree —
`se_na2so4_rt.xdi` comes out at 15 characters for every column in both.

See "Which physical-mapping subclass, and what goes in it" in
`release/CDIFXASDocumentImplementationGuide.md`.

### How a concept is placed in the JSON-LD, in both sets

Getting from a source field to a document takes two steps, and only the
first is a crosswalk:

```
XDI token / NeXus path  --SSSOM-->  cdifxas: concept  --code-->  place in CDIF JSON-LD
```

The second step — which object a concept's value goes on — is **not
curated in any table**. The profile defines the places, and each
converter writes its own rules for filling them in code.
`crosswalk/cdifxas-placement.tsv` records one converter's rules as a
table, but it is derived from that code, not a source for it.

**What the profile requires.** The XAS-specific sections of
`release/CDIFXASDocumentImplementationGuide.md` say what each entity
carries. Most concepts become a `schema:PropertyValue` whose
`schema:propertyID` is the concept itself, e.g.
`{"@id": "xas:edgeenergy"}`, on one of these objects:

| JSON-LD object | concepts placed there (examples) |
|---|---|
| acquisition activity in `prov:wasGeneratedBy`, `schema:additionalProperty` | `edgeenergy`, `calibrationmethod` |
| `prov:used` wrapper with additionalType `xas:source` | `xraysourcetype`, `probe` |
| `prov:used` wrapper with additionalType `xas:xraymonochromator` | `dspacing`, `monochromatortype`, `reflectionplane` |
| `prov:used` wrapper with additionalType `xas:beamline` | the beamline name; optionally `flux`, `spotsize`, `scanmode`, … |
| the sample, as the activity's `schema:object` | `temperature`, `samplepreparation`, … |
| root `schema:keywords` | `elementanalyzed`, `edgeanalyzed`, as `DefinedTerm`s |
| root `schema:measurementTechnique` | `xasmeasurementmode` |
| `schema:variableMeasured` | data-array columns: `energy`, `i0`, `mutrans`, … |

Because the propertyID *is* the concept's local name, both converters
must spell it exactly as the glossary does. The profile lists the same
names in its own enumerations, so a tidier spelling yields a document
that cannot validate.

**Four of these terms are retired.** On 2026-09-27 the profile moved
four technique-neutral concepts onto NeXus base classes
(`nxs:` = `https://manual.nexusformat.org/classes/`):

| retired | preferred |
|---|---|
| `xas:beamline` | `nxs:base_classes/NXinstrument.html` |
| `xas:xraysourcetype` | `nxs:base_classes/NXsource.html#nxsource-type-field` |
| `xas:probe` | `nxs:base_classes/NXsource.html#nxsource-probe-field` |
| `xas:temperature` | `nxs:base_classes/NXsample.html#nxsample-temperature-field` |

Both spellings validate, and both converters still emit the retired
ones, so the table above and `crosswalk/cdifxas-placement.tsv` show
them. The `xas:` forms can be dropped from the profile only once both
converters emit the NeXus terms. `xas:facility` was deliberately not
retired. The record is in `metadataBuildingBlocks`,
`_sources/profiles/cdifCompositeProfile/xasDocument/CHANGES-from-UKDS.md`.

**Where each converter encodes it:**

- **RML** — `resources/mapping_dds.ttl` in `smrgeoinfo/cdif-xas`. It
  does not read the SSSOM files. Each output property is its own
  triples map with the concept typed in as a constant: for instance
  `TriplesMap_scan_edge_energy` builds a `PropertyValue` with
  `rr:constant xas:edgeenergy` as its propertyID, and reads the value
  from the intermediate key `cdi:Scan_edge_energy`.
  `xdi-to-cdifxas.sssom.tsv` *describes* this mapping rather than
  driving it, and `build_crosswalk.py` keeps the two consistent by
  checking every XDI key in the SSSOM against the keys this mapping
  reads.
- **`cdifnexmetadata`** — the SSSOM files take a field to a concept
  (`map/xdi.py`, `map/concepts.py`). Then the `CONCEPT_SLOTS` table in
  `emit.py` takes each concept to a place in the document.
  A concept missing from that table is still emitted, as an
  `additionalProperty` on the acquisition activity, with a warning.
  `crosswalk/build_placement.py` reads `CONCEPT_SLOTS` and writes it out
  as `crosswalk/cdifxas-placement.tsv`.

So the placement is written down twice, in two forms, and nothing checks
that the two agree. Validating against `release/` catches a value placed
where the profile forbids it, but not a value placed in a different
permitted spot by each converter.

### `exampleMetadata/` — generated CDIF-XAS

55 JSON-LD documents plus batch generation and validation reports.
**Output, not source**: regenerate with the commands above rather than
editing. 55/55 validate against `release/` as of 2026-10-26: the
resolved schema and frame via `release/FrameAndValidate.py`, and
`xasDocumentRules.shacl` with no violations via pyshacl with
`advanced=True`. Run SHACL that way: several shapes (the sample and
instrument checks among them) select their targets with SPARQL, and
without advanced mode they are skipped. That is why the fork's own
`batch_validate_cdif.py`, which does not enable it, reported 55/55 on
2026-10-08 while 9 documents had a sample name shorter than the
3 characters the profile requires.

That claim goes stale whenever `release/` is re-synced from
`metadataBuildingBlocks`. When checked on 2026-10-08, the documents
generated on 2026-08-03 all failed, against both the freshly synced
schema and the one before it: the profile required every instrument to carry `prov:Entity` in
`@type` and `wd:Q3099911` ("scientific instrument") in
`schema:additionalType`, and the RML mapping emitted neither. Revalidate
after a sync, not just after a regeneration.

The same 55 files converted by the *other* pipeline live in
[`cdifnexmetadata/exampleMetadata-xdi`](https://github.com/CDIF-4-XAS/cdifnexmetadata),
not here. Both sets validate 55/55, checked the same way on the same
date (2026-10-26); the two are kept so the
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
| `cdif-xas-rml-intermediate.md` | the cdif-xas RML workflow's intermediate, `resources/cdif_skos.json`; moved here from `release/intermediateFormats.md` on 2026-10-27 |
| `XDISpec-FieldsCDIF-Schema.orgMapping.docx` | XDI spec fields against schema.org |
| `CDIF4XAS_Mappings_Intro.pdf` | introduction to the mappings |
| `Ravel_2016_*.pdf` | reference paper |
| `PhysicalDataset.png` | diagram |

### `tools/` — vocabulary maintenance

| script | what it does |
|---|---|
| `generate_concept_files.py` | per-concept files from the glossary |
| `generate_glossary_html.py` | the browsable glossary |
| `render_value_list_pages.py` | HTML pages for the three value lists, with the [iSamples vocabulary tooling](https://github.com/isamplesorg/vocabularies) and Quarto |
| `add_detection_mode_concepts.py` | detection-mode concepts |
| `import_nexus_enumerations.py` | pulls enumerated values from NXDL into the three value-list vocabularies (not the glossary) |

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
build publishes under that same `_v2` name because the w3id rule for
`https://w3id.org/cdif/xas/` (requested as JSON-LD) redirects to it. Renaming the working file therefore does not move any
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

The 106 concepts in `XAS_Glossary_SKOS.json` are **minted for
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
| `references` | 91 of 106 | 99 `doi.org` links (11 distinct DOIs), the XDI dictionary and other GitHub sources, the IUCr dictionary, `docs.xrayabsorption.org`, Wikipedia |
| `seeAlso` | 51 | `manual.nexusformat.org` — the resolvable NeXus documentation |
| `foaf:focus` | 36 | NeXusOntology PURLs under `purl.org/nexusformat/definitions/` |
| `notation` | 28 | the short token (`i0`, `mutrans`) the formats actually use |

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

Published at <https://cdif-4-xas.github.io/XAS-CDIF/> by
`.github/workflows/build-docs.yml`:

- `index.html`, the glossary, from `tools/generate_glossary_html.py`;
- `XAS_edges_SKOS.html`, `XAS_emissionlines_SKOS.html` and
  `XAS_detectionmodes_SKOS.html`, the value lists, rendered by
  `tools/render_value_list_pages.py` with the iSamples vocabulary writer
  (`vocab2mdCacheV2.py` in
  [isamplesorg/vocabularies](https://github.com/isamplesorg/vocabularies),
  pinned in the workflow) and Quarto, as the CDIF provenance activity
  types are. Every concept has an anchor named for the last segment of
  its URI, so `<page>#<localname>` reaches it;
- the vocabulary JSON-LD files and one JSON-LD file per glossary concept
  under `concepts/`.

To build the value-list pages locally, install the iSamples
`tools/requirements.txt` and Quarto, then
`python tools/render_value_list_pages.py --isamples <checkout>/tools`.

## Copyright and License

See `LICENSE`, `LICENSES/`, and `REUSE.toml` for per-file licensing.
