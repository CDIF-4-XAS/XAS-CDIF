# exampleData — XDI test corpus

XDI files used to exercise the XDI → CDIF conversion. Two groups, kept
apart by filename.

## `xdl_*.xdi` — 18 files from the XAS Data Library

Selected from the 272 files in
[XraySpectroscopy/XASDataLibrary](https://github.com/XraySpectroscopy/XASDataLibrary),
which is dedicated to the **public domain**, so there is no
redistribution constraint. Copied unmodified; the `xdl_` prefix marks
their origin and avoids a collision with the existing `co_metal_rt.xdi`,
which has different content.

Chosen by greedy set cover over the features that make one XDI file
different from another for metadata purposes — edge, beamline, facility,
detection mode as the column set implies it, monochromator, temperature
regime and absorber Z. Picking by hand over-samples whatever is
plentiful; this picks whatever the corpus did not already have. Eighteen
files cover every feature value the library offers and the corpus
lacked.

| File | Element | Edge | Beamline | Columns |
|------|---------|------|----------|---------|
| `xdl_SrO_rt_01.xdi` | Sr | K | SSRL 4-3 | energy, mutrans, mufluor, murefer, i0 |
| `xdl_pyrite2_rt_01.xdi` | S | K | 13-ID-E | energy, ifluor, i0 |
| `xdl_as2o3_roomt_scan1.xdi` | As | K | SSRL 4-1 | energy, i0, itrans, irefer |
| `xdl_CeO2.xdi` | Ce | L3 | APS 13-ID-E | energy, i0, itrans |
| `xdl_Sr_slawsonite_15K_01.xdi` | Sr | K | SSRL 4-3 (?) | energy, mutrans, murefer, i0 |
| `xdl_Pb_Foil_L2_rt_2016Foils.xdi` | Pb | **L2** | 13-ID-E | energy, itrans, i0 |
| `xdl_Au_Foil_L1_rt_2016Foils.xdi` | Au | **L1** | 13-ID-E | energy, itrans, i0 |
| `xdl_k2cro4_rt_003.xdi` | Cr | K | SSRL 2-3 | energy, i0, itrans, irefer |
| `xdl_V_foil.xdi` | V | K | 13-BM-D | energy, counttime, i0, itrans |
| `xdl_Zn_foil.xdi` | Zn | K | 13-ID-E | energy, energy_readback, counttime, i0, itrans |
| `xdl_Mn3O4_rt_01.xdi` | Mn | K | SSRL 4-3 | energy, i0, itrans, irefer |
| `xdl_Fe3O4_rt_01.xdi` | Fe | K | APS 13-BM-D | energy, i0, itrans |
| `xdl_EuSe_eu_l3_001.xdi` | Eu | L3 | 13-BM-D | energy, itrans, i0 |
| `xdl_Fe_metal_rt_02.xdi` | Fe | K | APS 20-BM-B | energy, i0, itrans |
| `xdl_co_metal_rt.xdi` | Co | K | APS 13-ID-C | energy, i0, itrans |
| `xdl_FeO_rt_01.xdi` | Fe | K | APS 20-BM | energy, i0, itrans |
| `xdl_WO2_rt_01.xdi` | W | L3 | 13-BM-D | energy, itrans, i0 |
| `xdl_CdS_10K_03.xdi` | Cd | K | SSRL 4-3 | energy, i0, itrans, irefer |

### What this adds that the corpus did not have

- **L1 and L2 edges.** The corpus had only K and L3. Au L1 and Pb L2 are
  the only such files in the whole library — two each out of 272.
- **SSRL.** Every previous file came from APS, Diamond or NSLS. Five
  SSRL beamlines now appear, including one whose name is literally
  `SSRL 4-3 (?)`, question mark included.
- **A missing `Facility.name`.** 147 of the 272 library files omit it
  entirely, which the converter has to survive.
- **Pre-computed μ columns.** `mutrans`, `mufluor`, `murefer` — the
  absorption coefficient stored directly rather than as raw intensities.
- **Extra columns the spec does not define**: `counttime`,
  `energy_readback`.
- **Z from 16 to 82** — S at the low end, W, Au and Pb at the high.
- **Cryogenic temperatures** (10K, 15K) alongside room temperature.

## Everything else

The pre-existing corpus: PtSn catalysis series from Diamond B18, and
single spectra whose names are lower-case (`cu_metal_rt.xdi`,
`fe2o3_rt.xdi`, …). Also `nonxafs_1d.xdi` / `nonxafs_2d.xdi`, and
`valid*.xdi` as validator fixtures.

## Two validator findings, recorded rather than worked around

Running the XDI validator over the 18 new files rejects all 18. Neither
cause is a defect in the files, and neither was fixed by editing them.

**1. The header-end regex is stricter than the specification.** The
validator uses `^#\s+---(-*)$`, which *requires* whitespace between the
comment token and the dashes. The specification defines the header-end
line as "comment token + header-end token", where the header-end token
is "three or more dash characters" — no whitespace token between them:

```
 * **Header-end line:** comment token + header-end token + end-of-line token

        # -------------
```

The example shows a space; the grammar does not require one. **258 of
the 272 files in the XDI authors' own reference library use `#-----`
with no space.** A validator that rejects the reference library is the
thing that is wrong.

This bears on earlier work: 18 files already in this corpus were edited
to insert that space, and carry a provenance comment saying so. Those
edits were harmless — both forms parse under the corrected regex — but
they were not necessary, and the note they carry overstates the problem.

**2. `Sample.temperature` is rejected for non-numeric values.** With the
header-end regex corrected, every remaining error is
`sample.temperature` failing a numeric-plus-unit pattern. The library
writes `room temperature` (163 files), `Room Temperature`, `10K`, `15K`.
Whether XDI requires a numeric temperature is a specification question;
what is certain is that the reference library does not supply one.

Both belong in the validator fork, alongside the conditional
`mono.d_spacing` fix already open upstream as PR #6 — not in the data.
