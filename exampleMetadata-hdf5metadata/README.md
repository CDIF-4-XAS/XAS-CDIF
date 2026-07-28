# exampleMetadata-hdf5metadata

The same 55 XDI files as `exampleData/`, converted by a **different
pipeline** from the one that produced `exampleMetadata/`. Both are kept
so the two can be compared on identical inputs.

| | `exampleMetadata/` | this directory |
|---|---|---|
| Producer | `cdif-xas-UKDS` | `usgin/hdf5metadata` |
| Mapping | RML (`mapping_dds.ttl`) run by rmlmapper | SSSOM crosswalk + Python |
| Runtime | FastAPI + Java + pyld | pure Python |
| Validates against `xasDocument` | 55 / 55 | **55 / 55** |

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

## Sentinels for what the files omit

Two properties the profile requires are missing from parts of the
corpus: the Diamond B18 series (`262875_PtSn_*` and siblings) gives
`Mono.name` and no `Mono.d_spacing` at all, and files such as
`feo_rt1.xdi` write a source type under neither `Facility` nor
`Beamline`.

Both are now emitted as `unknown`, with a description on each saying it
was not recorded in the source file. An omitted property makes the
instrument undescribable and fails validation; a guessed one is
indistinguishable from a reading.

The sentinel is deliberately not the plausible default. `exampleMetadata/`
writes `Synchrotron X-ray Source` for a missing source type -- true of
every file here, and still an assertion none of them made. It also
writes `reflectionplane: 1,1,1` for `Si(311)`, which is not true of
any of them.

## Reading the difference

Both directories now validate 55/55, so the pass rate says nothing. The
difference is in what each says where a file is silent.

Where `Mono.d_spacing` is absent, `exampleMetadata/` and this directory
agree: both write `unknown`. Where `Facility.xray_source` is absent they
do not -- `exampleMetadata/` writes `Synchrotron X-ray Source`, this one
writes `unknown`. The first is true of every file in this corpus and is
still an assertion none of them made; a consumer reading it cannot tell
it from a value the beamline recorded.

The same distinction shows in `reflectionplane`. `exampleMetadata/`
writes `1,1,1` for every file, including the eight whose `Mono.name`
says `Si(311)`. This directory reads the reflection out of `Mono.name`
and writes `3 1 1` for those.

Neither approach is wrong in general -- a catalogue that must not show
blanks wants defaults, and an assessment of source-data quality wants
gaps left visible. But a default that cannot be distinguished from a
reading forecloses the second use, and a wrong default forecloses both.
