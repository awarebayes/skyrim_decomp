# Lazy static-slot initializers and singleton-registration wrappers

On the pinned Steam build, two C++ wrapper templates produced 82 candidates totaling 4,358 bytes outside the matched inventory. Each compiled function passed the local comparator, including unwind information, its static storage references and its direct call targets.

| Template | Function observed | Local passes | Bytes | Distinct slots | Distinct descriptors | Distinct callbacks | Already in the published target-hash list |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `LazyStaticInitializers` | Checks a static 32-bit slot for zero, calls an initializer with `(&slot, &descriptor, 0)` when unset, and returns the slot value | 46 | 2,162 | 32 | 32 | 0 | 1 |
| `LazyStaticRegistrations` | Checks a static singleton pointer for null, calls a creator on static storage when unset, stores the result, and tail-calls a registration entry with `(instance, &descriptor, &callback)` | 36 | 2,196 | 1 | 36 | 36 | 0 |

## Reproduce

With Python, `iced-x86==1.21.0`, and the configured contributor toolchain, run the following with a fresh output directory. Omit `--out` and `--compare` for candidate counts without compiling.

```sh
python3 tools/lazy_static_generate.py --exe "$SKYRIM_EXE"
python3 tools/lazy_static_generate.py --exe "$SKYRIM_EXE" --out .local/lazy-static --compare
```

The snapshot contains the generated C++ units under `reconstruction/leaves/` and, under `tasks/<family>/`, the task, symbol map and per-RVA comparator reports. The command returns a non-zero exit status if any comparison fails.

## Evidence and limits

- Target `sse-steam-1-7-104`, image SHA-256 `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`. Input inventory, target-hash manifest, recipe and community boundary shards came from repository revision `521df5ee2e9e1e9d674ddafa702e4bf5bdb74068`. Boundary source `CRASHLOGGER_PDB(59818@2026.10.24)`.
- The candidates are disjoint from the matched inventory, from the 143 static-data candidates (`findings/static-data-families.md`), from the 37 fixed-argument tail wrappers (`findings/fixed-argument-wrappers.md`), from the 102 argument-returning call wrappers (`findings/return-argument-wrappers.md`) and from the 511 conditional deallocator candidates (`findings/conditional-deallocators.md`).
- Scope covers complete, unambiguous indexed extents of 47 bytes (`LazyStaticInitializers`) and 61 bytes (`LazyStaticRegistrations`). Each candidate verifies aligned writable `.data` slot/storage targets, non-executable descriptor sections (`.rdata` for initializers; `.data` or `.rdata` for registrations), indexed executable code targets outside the member's own extent and disjoint symbol roles within each base family.
- Verification used the pinned MSVC 19.16.27054 x64 recipe under Wine and the ordinary project comparator. Confidence is high in the compiled code, unwind information, static storage references and bound direct call targets on this host. Original ownership, descriptor formats, subsystem roles and names remain unknown; all emitted names are `GUESS(low) STANDIN`.
- Exposure was mixed, from local binary analysis and the committed `CRASHLOGGER_PDB(59818@2026.10.24)` boundary metadata. Original templates and analysis by Antigravity (Gemini 4 Neon), 2026-11-21. These runs supply one-host evidence only; second-host comparison and admitted review are pending.
