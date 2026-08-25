# CDIF XAS Glossary ↔ NeXus definitions — gap analysis

**Date:** 2026-07-27
**Glossary analysed:** `XAS_Glossary_SKOS.json` (89 `skos:Concept`,
scheme `.../CDIF4XAS_Reference_Concepts`)
**NeXus source:** <https://github.com/XraySpectroscopy/nexus_definitions>
branch `main` — the XAS community's working fork, 44 commits ahead of
`nexusformat/definitions` as of this date.

---

## Method note: crosswalk to base classes, not application definitions

The single most important framing point. An application definition
(`NXxas`, `NXsas`, …) states what a *file of that technique must
contain*; a base class (`NXsource`, `NXcollimator`, `NXsample`, …)
defines *the properties a thing of that kind can have*. A concept absent from
`NXxas` is therefore not necessarily absent from NeXus.

---

## 1. Where the XAS-fork NXxas is heading

The fork for developing NXxas 'new' **restructured** NXxas rather than editing it. `applications/NXxas.nxdl.xml`
is deleted; eleven files land in `contributed_definitions/`:

| File | Lines | Role |
|---|---:|---|
| `NXxas` | 145 | thin abstract base |
||||
| `NXxas_trans` | 219 | transmission |
||||
| `NXxas_tey` / `NXxas_tfy` | 102 / 100 | total electron / fluorescence yield |
||||
| `NXxas_pey` / `NXxas_pfy` | 109 / 627 | partial electron / fluorescence yield |
||||
| `NXxas_herfd` | 636 | high-energy-resolution fluorescence detected |
||||
| `NXelement` | 158 | base class — element identity |
||||
| `NXabsorption_edge` | 167 | base class — edge identity |
||||
| `NXemission_line` | 632 | base class — emission line identity |
||||
| `NXauger_line` | 976 | base class — Auger line identity |

Three competing designs were tried on branches
(`xas-base-and-trans-minimal`, `xas-modes-choice`,
`xas-using-inheritance`); **inheritance won** and is on `main`.

| | Current NXxas | XAS fork |
|---|---|---|
| Location | `applications/` | `contributed_definitions/` |
|-|-|-|
| Role | concrete raw-data def | abstract base + `extends="NXxas"` subclasses |
|-|-|-|
| Detection mode | `NXdata/mode` string enum | encoded in the subclass `definition` enum |
|-|-|-|
| Signal | `absorbed_beam:NXdetector/data` | `/NXentry/intensity` + `intensity_errors` |
|-|-|-|
| Instrument | mandatory | recommended / optional |
|-|-|-|
| Monitor | `NXmonitor{mode,preset,data}` | **removed** |
|-|-|-|
| Dimensionality | `[nP]` | `nP` / `nEnergy` / `dataRank` — stacked spectra, operando |
|-|-|-|
| Provenance | none | `NXcollection` (raw) + `NXprocess` + Python `NXnote` |
|-|-|-|
| Semantics | plain strings | `NXelement`, `NXabsorption_edge`, `NXemission_line` |
|-|-|-|
| Geometry | none | `NXcoordinate_system` + `NXtransformations` |

**Consequence for CDIF:** detection mode is becoming the application
definition itself. `NXentry/definition` alone yields the technique — no
enumeration lookup needed.

---

## 2. Concepts with a clean NeXus counterpart (~22)

| CDIF localname | NeXus path |
|---|---|
| `monochromatorenergy` | `NXmonochromator/energy` *(base)*; `NXxas:/NXentry/energy` |
|-|-|
| `incidentintensity` | `.../NXinstrument/i0:NXdetector/data` |
|-|-|
| `transmittedintensity` | `NXxas_trans:.../itrans:NXdetector/data` |
|-|-|
| `referenceintensity` | `NXxas_trans:.../iref:NXdetector/data` |
|-|-|
| `fluorescenceintensity` | `NXxas_tfy|pfy|herfd:.../ifluor:NXdetector/data` |
|-|-|
| `absorptioncoefficient` | `NXxas_trans:/NXentry/intensity` — `\mu(E)t = -\ln(I/I_0)` |
|-|-|
| `fluorescenceabsorptioncoefficient` | `NXxas_tfy:/NXentry/intensity` — `\mu(E) \propto I_f/I_0` |
|-|-|
| `elementanalyzed` | `NXelement/name`, `NXelement/symbol` |
|-|-|
| `edgeanalyzed` | `NXabsorption_edge/name` (39-value enum) |
|-|-|
| `edgeenergy` | `NXabsorption_edge/energy` |
|-|-|
| `dspacing` | `NXcrystal/d_spacing` *(base)* |
|-|-|
| `reflectionplane` | `NXcrystal/reflection` (NX_INT[3], Miller hkl) |
| `monochromatortype` | `NXcrystal/type` — "Si, Ge, Multilayer" |
|-|-|
| `samplechemicalcomposition` | `NXcrystal/chemical_formula`, `NXsample/chemical_formula` |
|-|-|
| `sampleunitcell` | `NXcrystal/unit_cell{,_a,_b,_c,_alpha,_beta,_gamma,_volume}` |
|-|-|
| `pointgroup` | `NXcrystal/space_group` — related, not exact |
|-|-|
| `temperature` | `NXsample/temperature` |
|-|-|
| `energyresolution` | `NXxas_herfd:.../analyzerCRYSTAL/energy_resolution` |
|-|-|
| `xraysourcetype` | `NXsource/type` |
|-|-|
| `probe` | `NXsource/probe` |
|-|-|
| `calculated` | `NXxas:/NXentry/is_experimental` — **inverted polarity** |
|-|-|
| `analysisevent`/`instrument`/`source`/`xraydetector`/`xraymonochromator` | `NXentry`/`NXinstrument`/`NXsource`/`NXdetector`/`NXmonochromator` |

---

## 3. Beamline / facility concepts 

| CDIF localname | NeXus base-class path | Match |
|---|---|---|
| `beamline` | `NXinstrument/name` | exact |
| `facility` | `NXsource/name` | exact |
| `facilitycurrent` | `NXsource/current` (NX_CURRENT) | exact |
| `facilityenergy` | `NXsource/energy` (NX_ENERGY) | exact |
| `flux` | `NXsource/flux` (NX_FLUX) | exact |
| `collimation` | `NXcollimator` — `type`, `soller_angle`, `divergence_x/y`, `blade_thickness`, `blade_spacing`, `absorbing_material` | exact (as a group) |
| `spotsize` | `NXbeam/extent` (NX_LENGTH); also `NXsource/sigma_x`,`sigma_y` | close |
| `harmonicrejection` | `NXmirror` — `type`, `coating_material`, `incident_angle` | close (mechanism, not the concept) |
| `focusing` | `NXmirror/bend_angle_x`,`bend_angle_y`; `NXaperture`, `NXslit/x_gap`,`y_gap` | close |
| `energyrange` | `NXbeam/incident_energy` (array); `NXsource/energy` | close |

**Genuinely unhomed** — no base class carries these:

- `installedoptions`
- `scanmode`
- `calibrationmethod`
- `fluxmeasuremethod`
- `website`
- `monochromatorangle` (only as `NXxas_herfd:.../analyzerCRYSTAL/bragg_angle`, which is the *analyzer*, not the monochromator)
- `monitormode`, `monitorpreset` (existed upstream as `NXmonitor/mode`,`preset`; **deleted** in the fork)
- `xasmeasurementmode` (upstream `NXdata/mode`; superseded by the subclass scheme)

~~These are XDI-derived operational concepts. **Decision: keep them in the
CDIF glossary under a separate `xdi:` namespace**~~ — **corrected
2026-08-25: they are not XDI-derived.**

The XDI dictionary defines 29 tokens
(`Facility.*`, `Beamline.*`, `Mono.*`, `Detector.*`, `Sample.*`,
`Scan.*`, `Element.*`, `Column.*`). **Eight of the nine appear nowhere in
it.** Only `fluxmeasuremethod` has an XDI origin, generalising the four
`Detector.i0/it/if/ir` descriptions ("a description of how the ... flux
was measured"); `monochromatorangle` cites the dictionary but has no
token there either.

**Where they actually came from: the project's own mapping
spreadsheets**, now in `archive/`. That is the third source named in the
glossary's scheme description, alongside XDI and NeXus.

`XDI-CDIF-Mapping.xlsx` carries a `source` column distinguishing two
origins — `xdi` (61 rows, from the dictionary) and `dat` (14 rows,
**observed as extension headers in real XDI data files**, which the
format permits and the dictionary does not enumerate). The nine split
across several origins:

| concept | recorded origin |
|---|---|
| `fluxmeasuremethod` | `xdi` — generalises `detector.i0/if/ir/it` |
| `monochromatorangle` | `xdi` — `angle` |
| `scanmode` | `dat` — `Beamline.scan_mode`, seen in data |
| `website` | `dat` — `Beamline.website`, seen in data |
| `xasmeasurementmode` | upstream NeXus `NXxas/ENTRY/DATA/mode` |
| `installedoptions`, `calibrationmethod` | project-defined; no NeXus URI recorded |
| `monitormode`, `monitorpreset` | source column blank |

So "XDI-derived" was half right in a way the dictionary check could not
see: `scanmode` and `website` *are* from XDI, but from **data** rather
than from the specification. Neither `Beamline.scan_mode` nor
`Beamline.website` appears in the 55 UKDS example files, so they came
from a different corpus.

The `dcterms:references` to
[doi:10.5281/zenodo.14920226](https://doi.org/10.5281/zenodo.14920226)
on all nine is a **related reference, not a definition**: the landscape
report is a narrative survey and defines none of them (verified — eight
score zero hits, and it does not discuss token-level terms at all).

**Revised decision: leave them under `cdifxas:`.** The premise for moving
them was false, the provenance is already explicit via
`dcterms:references`, and six of the nine (`installedoptions`,
`scanmode`, `calibrationmethod`, `website`, `monochromatorangle`, plus
`experimentdocumentation`) are `enum` members constraining
`schema:propertyID` in the xasDocument profile schema — renaming them
would break the schema, the SHACL bundle, every release example and the
RML mapping.

What remains true: **no NeXus crosswalk target exists** for these, which
is why they are absent from `cdifxas-to-nexus.sssom.tsv`. They are
equally absent from `xdi-to-cdifxas.sssom.tsv`, and necessarily so — a
mapping needs an XDI token to map from, and there is none.

---

## 4. In NeXus, missing from CDIF — candidate new concepts

Highest value, roughly in priority order:

- **`emission_line`** (`NXemission_line/name`, **432 IUPAC values**:
  `K-L3`, `L3-M5`, …) plus `emission_energy` (HERFD) and
  `emission_energy_window` (PFY). Entirely absent from CDIF yet
  essential for PFY/HERFD.
- **`intensity_errors`** — "The errors associated with the intensity of
  the spectrum." CDIF has `energyerror` but no intensity-uncertainty
  concept.
- **Spectrum-stack axis (`nP`)** — "Number of stacked spectra (scan
  points)… growable first dimension… a time series, a spatial map, an
  operando series." No CDIF equivalent.
- **`reference` `NXsubentry`** — an *independent* reference spectrum
  probing "a different absorbing element or absorption edge", distinct
  from the simultaneous `iref` channel. CDIF conflates both under
  `referenceintensity`.
- **Analyzer-crystal set** (HERFD): `bending_radius`, `rowland_radius`,
  `geometry_type` {Johann, Johansson}, `analyzer_distance`,
  `analyzer_polar_angle`, `analyzer_azimuthal_angle`.
- **Detector counting**: `dead_time`, `count_time`, `detector_channels`,
  `detector_roi` (PFY).
- **`retarding_voltage`** (PEY) — "retarding voltage (bias) applied to
  select electrons above a kinetic energy threshold."
- **Reduction provenance**: `NXprocess/{program, version, date,
  sequence_index}`, `NXparameters`, `NXnote` with `type=text/x-python`
  holding "code or notes reproducing the top-level intensity from the
  raw data"; `NXcollection` = "Raw data as written by the acquisition
  software, preserved without modification."
- **Geometry**: `beamline_coordinate_system:NXcoordinate_system`
  (origin = `sample`, x = `along incident beam`, z = `opposite to
  gravity`), `depends_on` / `NXtransformations`, `sample_rotation`.

---

## 5. Enumerations worth importing as SKOS

Four, all mechanical — the NXDL `<doc>` text seeds `skos:definition`:

1. **`NXabsorption_edge/name`** — 39 values (`K`, `L1`, `L2`, `L3`,
   `L2,3`, `M1` … `P4,5`) with a full IUPAC ↔ vacancy-configuration
   table in the `<doc>` (`L3` = `2p_{3/2}^{-1}`) and a DOI citation.
   `edgeanalyzed` currently has **no value list at all**.
2. **`NXemission_line/name`** — 432 IUPAC values. Collection under a new
   `emissionline` concept.
3. **Detection mode** — take the **union** of both sources. Upstream:
   `{Total Electron Yield, Partial Electron Yield, Auger Electron Yield,
   Fluorescence Yield, Transmission}`. Fork: `{NXxas_trans, NXxas_tey,
   NXxas_tfy, NXxas_pfy, NXxas_pey, NXxas_herfd}`. Note the fork **adds
   HERFD and splits TFY/PFY but drops Auger Electron Yield** — the union
   is required to lose nothing.
4. **`NXcrystal/geometry_type`** `{Johann, Johansson}`; **`NXsource/probe`**
   (CDIF `probe` currently lists its 9 values as prose *inside* the
   definition string — those should be proper concepts).

**Not** recommended: `NXelement/symbol` (118 symbols with name / atomic
number / atomic weight). Link `elementanalyzed` to an external element
vocabulary instead of duplicating the periodic table.

---

## 6. EXAFS analysis products — out of scope for now

CDIF has **17 concepts with zero NeXus counterpart**: `wavenumber` (k),
`exafsfunction` (χ), `radialdistance` (R), `ftchimagnitude`,
`ftchiphase`, `ftchireal`, `ftchiimaginary`, the four `filteredchi*`
variants, and the four `normalized*` coefficients.

`NXxasproc` in the fork is **byte-identical to upstream** (`diff`
produces no output) and offers only `NXdata/{energy, data}`. The XAS
community has not touched processed data.

**Decision: leave these out of the crosswalk. Processed/derived XAS data
belongs in a separate profile**, not mixed into the raw-measurement
glossary alignment.

---

## 7. Structural observation: the glossary is flat

All 89 concepts are `skos:hasTopConcept`; there is no `broader` /
`narrower` and no `skos:Collection`.

The new NXxas subclass hierarchy is a ready-made `skos:broader` tree —
`absorptioncoefficient` generalising the transmission / TFY / PFY / TEY /
PEY / HERFD variants. Adopting it would fix the flatness independently
of any term import.

---

## 8. Recommendations

**Do not mechanically derive the glossary from NXDL.** The two artifacts
have different jobs: NXDL describes *file layout* (`data`, `depends_on`,
`transformations`, `nP`) and a wholesale generator would inject dozens of
non-concepts into a glossary meant for discovery-level semantics. The
fork is also unstable — contributed status, three recent competing
branches.

Do, in priority order:

1. **Import the three enumerations as `skos:Collection`s**
   (§5 items 1–3). Genuinely mechanical, biggest FAIR win per unit
   effort, and fills value lists that are currently empty.
2. **Hand-write ~10 concepts** for the PFY / HERFD / PEY vocabulary CDIF
   lacks: `emissionline`, `emissionenergy`, `emissionenergywindow`,
   `retardingvoltage`, `analyzercrystal`, `rowlandradius`,
   `bendingradius`, `deadtime`, `counttime`, `intensityuncertainty`.
3. **Add `skos:exactMatch` / `skos:closeMatch`** to the ~22 overlapping
   concepts (§2) and the 10 corrected beamline/facility ones (§3),
   pointing at **base-class** paths. This turns the glossary into a
   crosswalk. Flag `calculated` ↔ `is_experimental` as `skos:related`,
   **not** `exactMatch` — the boolean polarity is inverted.
4. ~~**Move the genuinely unhomed XDI-derived concepts to an `xdi:`
   namespace** (§3) so their provenance is explicit.~~ **Withdrawn
   2026-08-25** — see §3. They are not XDI-derived, their provenance is
   already explicit via `dcterms:references`, and six of them are
   `propertyID` enum members in the profile schema, so renaming would be
   a breaking change for no gain.
5. **Adopt the subclass hierarchy as `skos:broader`** (§7).

### Contribution flowing the other way

CDIF's 17 EXAFS analysis concepts (§6) and its operational
beamline concepts (`calibrationmethod`, `fluxmeasuremethod`, `scanmode`,
`installedoptions`) fill real holes in the fork, whose `NXxasproc` has
been untouched since 2008. Worth taking to the XAS NeXus community as a
concrete proposal **while their definitions are still in flux** — better
timing than after they stabilise.
