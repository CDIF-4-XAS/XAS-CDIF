# exampleMetadata-hdf5metadata

The same 55 XDI files as `exampleData/`, converted by a **different
pipeline** from the one that produced `exampleMetadata/`. Both are kept
so the two can be compared on identical inputs.

| | `exampleMetadata/` | this directory |
|---|---|---|
| Producer | `cdif-xas-UKDS` | `usgin/hdf5metadata` |
| Mapping | RML (`mapping_dds.ttl`) run by rmlmapper | SSSOM crosswalk + Python |
| Runtime | FastAPI + Java + pyld | pure Python |
| Validates against `xasDocument` | 55 / 55 | **26 / 55** |

**`exampleMetadata/` remains the reference output.** It is the
production pipeline, it is reviewed, and it validates completely. This
directory exists to show what the second implementation currently
produces from the same bytes, not to replace it.

## Why this was generated

The SSSOM crosswalk gained four rows (`Column.ifluor`, `Column.mufluor`,
`Column.murefer`, `Beamline.xray_source`) and the XDI binding gained
four derivations (probe, detection mode, reflection plane, d-spacing
units). None of that reaches the RML pipeline, which does not read the
crosswalk — there is no reference to SSSOM anywhere in `cdif-xas-UKDS`.
So regenerating `exampleMetadata/` would have shown no change at all,
and this is where the crosswalk work actually shows up.

## What the 29 failures are

None is a mapping error. All three causes are the profile asking for
something the file does not contain.

**A monochromator peer without a d-spacing (18 files).** The profile
requires the `xas:xraymonochromator` instrument to carry
`xas:dspacing` with a value *and* a unit. The Diamond B18 series
(`262875_PtSn_*` and siblings) gives `Mono.name: Si(311)` and no
`Mono.d_spacing` at all. Nothing can supply it: the d-spacing of a
Si(311) crystal is a known constant, but reading it out of a table
would be asserting a number the file never recorded.

**A source peer without a source type (rest).** The profile requires
`xas:source` to carry both `xas:probe` and `xas:xraysourcetype`. The
probe is derivable — XDI describes X-ray absorption and nothing else —
but the source type has to come from `Facility.xray_source` or
`Beamline.xray_source`, and files such as `feo_rt1.xdi` write neither.

**Sample names shorter than the profile allows.** `cu_metal_10K.xdi`
gives `Sample.name: Cu`, and the profile wants at least three
characters. The emitter now appends the filename rather than discarding
the file's own word.

## Reading the difference

The interesting comparison is not the pass rate. `exampleMetadata/`
validates completely because the RML pipeline supplies sentinel values
for what the file omits; this one leaves the gap and fails. Which
behaviour is right depends on what the record is for — a catalogue entry
wants a complete document, an assessment of the source data wants to
see what is missing. Neither pipeline is wrong, and the 29 failures here
are a fair inventory of what these 55 XDI files do not say.
