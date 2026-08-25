# XAS data to CDIF metadata — the two workflows

How a raw XAS dataset becomes a metadata record conforming to
`cdif/xasDocument/1.0`. There are **two independent implementations**.
They share no code — only the target profile.

They are **not** split by input format. `cdifnexmetadata` reads both
NeXus/HDF5 and XDI; `cdif-xas` reads XDI only. What separates them is
*method*: a Python emitter versus a declarative RML mapping executed by a
Java tool, packaged as a CLI versus an HTTP service.

Written for someone integrating either into a larger system. Current as
of 2026-08-25.

---

## The shape of it

```
  NeXus .nxs ─┐
              ├─▶ cdifnexmetadata ─┐   Python, CLI
  XDI .xdi ─┬─┘   (h5py + numpy)   │
            │                      ├─▶ CDIF JSON-LD ─▶ frame ─▶ validate
            └─▶ cdif-xas ──────────┘   RML + Java, HTTP    │
                (rmlmapper)                                │
                                          JSON Schema + SHACL from
                                             XAS-CDIF/release/
```

XDI has two routes; NeXus has one.

Both emit the same profile, resolve concepts against the same
`https://w3id.org/cdif/xas/` vocabulary, and validate against the same
artifacts in this directory. **Agreement between them is evidence; a
disagreement localises a defect.** Cross-comparing the two over the same
55 XDI files has repeatedly found bugs that each pipeline validated
cleanly on its own.

Because XDI has two routes, the choice for an XDI workflow is a choice of
dependency stack, not of capability — see [Which one to
integrate](#which-one-to-integrate).

---

## Path A — NeXus/HDF5 *and* XDI → CDIF (`cdifnexmetadata`)

**Repo:** <https://github.com/usgin/cdifnexmetadata> · Python package,
CLI · MIT/REUSE-compliant

**Inputs:** NeXus `.nxs` (HDF5, NXxas and relatives), and `.xdi`.

### Install and run

```bash
git clone https://github.com/usgin/cdifnexmetadata
cd cdifnexmetadata
uv sync --all-extras            # --all-extras pulls the validation stack

# one file to stdout
uv run cdifnexmetadata exampleData/cu_metal_rt.nxs

# many files to a directory, validated against the profile
uv run cdifnexmetadata data/*.nxs -o metadata/ \
    --validate --profile-dir ../XAS-CDIF/release
```

**Runtime dependencies are `h5py` and `numpy`.** Validation adds
`jsonschema`, `pyshacl`, `rdflib`, `pyld` as an optional extra. **No
Java, no Docker, no network at runtime.**

### How it works

Four stages inside one process:

| stage | module | what it does |
|---|---|---|
| 1. read | `map/` (`xdi.py`, `crosswalk.py`) | walk the HDF5 tree / parse XDI headers |
| 2. normalise | `map/normalise.py` | ISO datetimes, qualitative temperatures, unit-less energies, header aliases |
| 3. emit | `emit.py` | build the CDIF JSON-LD graph |
| 4. validate | `validate.py` | frame, then JSON Schema + SHACL |

Stage 4 is optional and off by default; the profile artifacts are located
by pattern under `--profile-dir`, or the `HDF5METADATA_PROFILE_DIR`
environment variable (the name predates the `hdf5metadata` →
`cdifnexmetadata` rename).

**Concept resolution** goes through a crosswalk keyed on the CDIF XAS
concept hub, so a NeXus path and an XDI token that mean the same thing
land on the same `https://w3id.org/cdif/xas/{localname}` IRI. Adding a
technique is a crosswalk edit; adding an input format is a parser. See
that repo's `README.md` §"How it works" and `STATUS.md`, which is written
as a cold-start entry point and records decisions that contradict the
obvious assumption.

### Bundled crosswalks

The three crosswalk files under `src/cdifnexmetadata/data/` are *copies*
of the ones in this repository's `crosswalk/`, refreshed with:

```bash
uv run python -m cdifnexmetadata.map.crosswalk --refresh
```

They were resynchronised on 2026-08-25 and are current with this release.
Check before relying on them: a stale copy fails silently, because an XDI
header with no crosswalk row produces no output and no warning. The
refresh immediately before this note recovered nine mappings, two of them
load-bearing — `Sample.formula` (19 of the 55 example files) and
`Sample.reference` (10 of 55) had simply been dropped.

### Bundled corpora

`exampleData/` (20), `exampleMetadata-NEXUS/` (14),
`exampleMetadata-xdi/` (56) — generated output kept for regression
comparison.

---

## Path B — XDI → CDIF (`cdif-xas`, RML)

**Repo:** <https://github.com/smrgeoinfo/cdif-xas> (fork of
<https://github.com/UKDSResearch/cdif-xas>) · FastAPI service ·
originally built for Dataverse

**Inputs:** XDI text files.

### Install and run

```bash
git clone https://github.com/smrgeoinfo/cdif-xas
cd cdif-xas
uv sync                          # Python 3.13, pinned: xdi_validator needs it
git clone https://github.com/CDIF-4-XAS/XAS-CDIF -b cdifxasRelease1.1 ../XAS-CDIF

# convert all 55 example XDI files, then validate
uv run python tools/batch_generate_cdif.py ../XAS-CDIF/exampleData ../XAS-CDIF/exampleMetadata
uv run python tools/batch_validate_cdif.py ../XAS-CDIF/exampleMetadata
```

Expect `55 ok, 0 error(s)` then `55/55 fully valid` — **read both lines**;
the first reports conversion, the second conformance.

**Requires Java** (the `rmlmapper` JAR) as well as Python. Docker and a
Dataverse instance are optional — the batch tools run standalone.

### How it works

The transformation is **declarative**, not procedural: `resources/mapping_dds.ttl`
is a ~1900-line RML mapping executed by `rmlmapper`.

| stage | component | what it does |
|---|---|---|
| 1. parse | `api/cdi.py` | XDI headers → intermediate JSON |
| 2. pre-check | `api/xdi_precheck.py` | surface spec violations before mapping |
| 3. map | `rmlmapper` + `resources/mapping_dds.ttl` | JSON → RDF/JSON-LD |
| 4. frame | `api/FrameAndValidate.py` | graph → the tree the schema describes |
| 5. validate | same | JSON Schema, then SHACL |

Exposed as HTTP endpoints — `/cdif` (end to end), `/map`, `/frame`,
`/validate` — and as the three `tools/batch_*.py` scripts.

**The RML mapping is the specification of this path.** Changing what is
emitted means editing the mapping, not Python. `api/Mapper.py` adds
post-framing repairs that JSON-LD framing alone cannot express (collapsing
reference-only slots, materialising blank-node identifiers, ensuring a
Person carries a name or identifier).

---

## What both paths depend on

Everything in this directory:

| artifact | role |
|---|---|
| `cdifXASDocumentResolvedSchema.json` | JSON Schema (Draft 2020-12), standalone |
| `xasDocumentRules.shacl` | aggregated SHACL, all six composed components |
| `cdifXASDocument-frame.jsonld` | JSON-LD frame — apply **before** schema validation |
| `XAS_Glossary_SKOS_v2.json` + the three value lists | the concept vocabulary |
| `examples/` | seven worked documents, all passing both gates |

**Validate the framed document, not the emitted graph.** The profile is
written against the tree that framing produces. Skipping the frame
produces failures that look like content errors and are not.

Concept IRIs resolve through `https://w3id.org/cdif/xas/{localname}`.
Provenance of the vocabulary itself is in
[`glossaryProvenance.md`](glossaryProvenance.md).

---

## Which one to integrate

For a workflow system — Galaxy, a pipeline runner, a batch harness —
**`cdifnexmetadata` is the easier target**, and it covers both input
formats:

- a plain Python package with a CLI; `uv run cdifnexmetadata FILE`
- runtime dependencies are `h5py` + `numpy`; validation is an optional extra
- **no JVM, no service to stand up, no network calls**
- reads `.nxs` *and* `.xdi`, so one tool covers both inputs
- writes one JSON-LD document per input file, or to a directory

`cdif-xas` suits a service context — it is a FastAPI application designed
to sit beside Dataverse, and it needs Java for `rmlmapper`. Its declarative
mapping is an advantage where the transformation itself must be
inspectable or edited by non-programmers, and a cost where you want a
single self-contained executable step.

Both are usable headlessly; the difference is the shape of the dependency,
not capability.

### Minimal Galaxy-style step

```bash
uv run cdifnexmetadata "$INPUT" -o "$OUTDIR" \
    --validate --profile-dir "$PROFILE_DIR" --report
```

`--report` prints a per-file conformance summary; the exit code reflects
validation. Pin `--profile-dir` to a checkout of this release so the
target profile is explicit and reproducible rather than implicit.

---

## Status and contacts

- The **profile** (`cdif/xasDocument/1.0`) is released; all seven examples
  in `examples/` pass JSON Schema and SHACL.
- The **vocabulary** is 106 concepts plus three value lists (39 edges, 432
  emission lines, 7 detection modes), pinned to a specific NeXus fork
  commit — see `glossaryProvenance.md`.
- **Convergence** between the two paths is documented in the `cdif-xas`
  repo: `CONVERGENCE-PROPOSAL.md` (where they agree and differ) and
  `UPLIFT-INSTRUCTIONS.md` (bringing an implementation up to the profile,
  sixteen tasks with a summary at the top).
- `UKDSResearch/cdif-xas` — the origin of Path B — has not moved since
  2026-07-17. Work since then is in the `smrgeoinfo` fork.
