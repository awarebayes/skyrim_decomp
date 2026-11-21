# Custom-allocator scalar deleting destructors

On the pinned Steam build, twelve C++ templates covering two custom-allocator deleting-destructor backends (TLS-router sized-block deallocation and global-heap virtual deallocation, each with fallback global sized deallocation on bit 2 of the flags parameter) produced 651 candidates totaling 73,775 bytes outside the matched inventory. Each compiled function passed the local comparator, including unwind information (primary and chained entries), static storage references, read-only table addresses and bound direct call targets.

| Template | Function observed | Local passes | Bytes | Shards | Distinct object sizes | Distinct teardown callees | Distinct tables | Already in the published target-hash list |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `RouterCleanupDeallocators` | Calls a cleanup entry, then frees via size-tagged TLS-router block heap or fallback global deallocator on `flags` bits 0 and 2 | 256 | 32,000 | 4 | 44 | 244 | 0 | 5 |
| `RouterTableDeallocators` | Stores a read-only table pointer at offset 0, then frees via size-tagged TLS-router block heap or fallback global deallocator | 32 | 3,968 | 1 | 5 | 0 | 2 | 0 |
| `RouterMemberCleanupDeallocators` | Calls a subobject cleanup entry at a typed offset and a base cleanup entry, then frees via size-tagged TLS-router or fallback global deallocator | 29 | 3,973 | 1 | 14 | 2 | 0 | 0 |
| `RouterMemberTableDeallocators` | Calls a subobject cleanup entry at a typed offset and stores a read-only table pointer at offset 0, then frees via size-tagged TLS-router or fallback global deallocator | 13 | 1,807 | 1 | 6 | 3 | 1 | 0 |
| `RouterFixedTableDeallocators` | Stores a read-only table pointer at offset 0, then frees with a fixed size via TLS-router block heap or fallback global deallocator | 29 | 2,552 | 1 | 9 | 0 | 18 | 0 |
| `RouterRefMemberDeallocators` | Conditionally releases and clears a pointer member, calls subobject and base cleanups, then frees via size-tagged TLS-router or fallback global deallocator | 12 | 1,926 | 1 | 9 | 3 | 0 | 0 |
| `HeapCleanupDeallocators` | Calls a cleanup entry, then frees via a global heap virtual method or fallback global deallocator on `flags` bits 0 and 2 | 193 | 17,177 | 3 | 31 | 37 | 0 | 0 |
| `HeapTableDeallocators` | Stores a read-only table pointer at offset 0, then frees via global heap virtual method or fallback global deallocator | 15 | 1,095 | 1 | 4 | 0 | 5 | 0 |
| `HeapTableCleanupDeallocators` | Stores a read-only table pointer at offset 0 and calls a cleanup entry, then frees via global heap virtual method or fallback global deallocator | 9 | 891 | 1 | 3 | 1 | 7 | 0 |
| `HeapDualTableDeallocators` | Stores read-only table pointers at offset 0 and a second typed offset and calls a cleanup entry, then frees via global heap or fallback global deallocator | 11 | 1,210 | 1 | 3 | 3 | 18 | 0 |
| `HeapTripleTableDeallocators` | Stores three read-only table pointers, calls subobject and base cleanups, then frees via global heap or fallback global deallocator | 40 | 5,304 | 1 | 6 | 5 | 60 | 0 |
| `HeapFiveTableDeallocators` | Stores three read-only table pointers, calls a subobject cleanup, restores two base table pointers and calls a base cleanup, then frees via global heap or fallback global deallocator | 12 | 1,872 | 1 | 1 | 3 | 30 | 0 |

## Reproduce

With Python, `iced-x86==1.21.0`, and the configured contributor toolchain, run the following with a fresh output directory. Omit `--out` and `--compare` for candidate counts without compiling.

```sh
python3 tools/custom_dealloc_generate.py --exe "$SKYRIM_EXE"
python3 tools/custom_dealloc_generate.py --exe "$SKYRIM_EXE" --out .local/custom-dealloc --compare
```

The snapshot contains the sharded C++ units (at most 75 functions per unit, 17 units total) under `reconstruction/leaves/` and, under `tasks/<family>/`, the task, symbol map and per-RVA comparator reports. The command returns a non-zero exit status if any comparison fails.

## Evidence and limits

- Target `sse-steam-1-7-104`, image SHA-256 `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`. Input inventory, target-hash manifest, recipe and community boundary shards came from repository revision `521df5ee2e9e1e9d674ddafa702e4bf5bdb74068`. Boundary source `CRASHLOGGER_PDB(59818@2026.10.24)`.
- The 651 candidates are disjoint from the matched inventory, from the 143 static-data candidates (`findings/static-data-families.md`), from the 37 fixed-argument tail wrappers (`findings/fixed-argument-wrappers.md`), from the 102 argument-returning call wrappers (`findings/return-argument-wrappers.md`), from the 511 conditional deallocator candidates (`findings/conditional-deallocators.md`), and from the open generator branches for polymorphic table-reset, range-copy, guarded-callback and lazy-static wrappers.
- Validation partitioned the 651 discovered candidates into a development split (348 functions, 39,817 bytes, containing all inspected exemplars) and an untouched held-out validation split (303 functions, 33,958 bytes). Both splits passed 100% locally (`348/348` dev, `303/303` held-out) without per-function edits, followed by `651/651` on the full end-to-end snapshot run.
- Scope covers complete, unambiguous indexed non-EH extents of 73 to 165 bytes (including both `disp8` and `disp32` member/table offsets) matching the default MSVC `/O2` code generation. Every candidate verifies indexed executable direct callees outside its own extent, non-overlapping member-to-member references within each base family, read-only non-executable `.rdata` table and indirect-getter targets, and properly aligned writable non-executable `.data` TLS-slot and global-heap pointers.
- Verification used the pinned MSVC 19.16.27054 x64 recipe under Wine and the ordinary project comparator. Confidence is high in the compiled code, primary and chained unwind information, static storage references, object size arguments and bound direct call targets on this host. Original class ownership, inheritance hierarchies, member layouts, destructor identities and names remain unknown; all emitted names are `GUESS(low) STANDIN`.
- Exposure was mixed, from local binary analysis and the committed `CRASHLOGGER_PDB(59818@2026.10.24)` boundary metadata. Original templates and analysis by Antigravity (Gemini 4 Neon), 2026-11-21. These runs supply one-host evidence only; second-host comparison and admitted review are pending.
