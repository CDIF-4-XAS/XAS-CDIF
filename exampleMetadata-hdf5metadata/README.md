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

The interesting comparison is not the pass rate. `exampleMetadata/`
validates completely because the RML pipeline supplies sentinel values
for what the file omits; this one leaves the gap and fails. Which
behaviour is right depends on what the record is for — a catalogue entry
wants a complete document, an assessment of the source data wants to
see what is missing. Neither pipeline is wrong, and the 29 failures here
are a fair inventory of what these 55 XDI files do not say.
