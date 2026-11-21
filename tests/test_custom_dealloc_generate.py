"""Custom-allocator deleting destructors in an original synthetic PE image."""
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_code_rules
import contrib_screen
import custom_dealloc_generate as generator
import lint_reconstruction
from pecoff import PeImage
from synthetic_pecoff import assemble_pe


def _rel32(pos, length, target):
    return struct.pack('<i', target - (pos + length))


def _lea_rax_rip(pos, target):
    return bytes.fromhex('48 8d 05') + _rel32(pos, 7, target)


def _call_rel32(pos, target):
    return bytes([0xe8]) + _rel32(pos, 5, target)


def _add_rcx(off):
    if off < 0x80:
        return bytes.fromhex('48 83 c1') + struct.pack('<b', off)
    return bytes.fromhex('48 81 c1') + struct.pack('<i', off)


def _mov_mem_rcx_rax(off):
    if off == 0:
        return bytes.fromhex('48 89 01')
    if off < 0x80:
        return bytes.fromhex('48 89 41') + struct.pack('<b', off)
    return bytes.fromhex('48 89 81') + struct.pack('<i', off)


def _mov_mem_rbx_rax(off):
    if off == 0:
        return bytes.fromhex('48 89 03')
    if off < 0x80:
        return bytes.fromhex('48 89 43') + struct.pack('<b', off)
    return bytes.fromhex('48 89 83') + struct.pack('<i', off)


def _router_dil_tail(pos, obj_size, tls_slot, tls_getter, dealloc, *, dealloc_size=None):
    if dealloc_size is None:
        dealloc_size = obj_size
    b = bytearray()
    b += bytes.fromhex('40 f6 c7 01 74 55 40 f6 c7 04 75 42')
    b += bytes.fromhex('0f b7 43 08 b9 ff ff 00 00 66 3b c1 75 07 bf')
    b += struct.pack('<I', obj_size)
    b += bytes.fromhex('eb 03 0f b7 f8')
    b += bytes.fromhex('8b 0d') + _rel32(pos + len(b), 6, tls_slot)
    b += bytes.fromhex('ff 15') + _rel32(pos + len(b), 6, tls_getter)
    b += bytes.fromhex('44 8b c7 48 8b d3 48 8b 48 58 48 8b 01 ff 50 10')
    b += bytes.fromhex('48 8b c3 48 8b 5c 24 30 48 83 c4 20 5f c3')
    b += bytes([0xba]) + struct.pack('<I', dealloc_size)
    b += bytes.fromhex('48 8b cb')
    b += _call_rel32(pos + len(b), dealloc)
    b += bytes.fromhex('48 8b c3 48 8b 5c 24 30 48 83 c4 20 5f c3')
    return bytes(b)


def _heap_dil_tail(pos, obj_size, global_heap, dealloc):
    b = bytearray()
    b += bytes.fromhex('40 f6 c7 01 74 31 40 f6 c7 04 75 1e')
    b += bytes.fromhex('48 8b 0d') + _rel32(pos + len(b), 7, global_heap)
    b += bytes.fromhex('48 8b d3 48 8b 01 ff 50 60')
    b += bytes.fromhex('48 8b c3 48 8b 5c 24 30 48 83 c4 20 5f c3')
    b += bytes([0xba]) + struct.pack('<I', obj_size)
    b += bytes.fromhex('48 8b cb')
    b += _call_rel32(pos + len(b), dealloc)
    b += bytes.fromhex('48 8b c3 48 8b 5c 24 30 48 83 c4 20 5f c3')
    return bytes(b)


PROLOG_RBX_RDI = bytes.fromhex('48 89 5c 24 08 57 48 83 ec 20')


def mk_router_cleanup(rva, cleanup, obj_size, tls_slot, tls_getter, dealloc, *, dealloc_size=None):
    b = bytearray(PROLOG_RBX_RDI + bytes.fromhex('8b fa 48 8b d9'))
    b += _call_rel32(rva + len(b), cleanup)
    b += _router_dil_tail(rva + len(b), obj_size, tls_slot, tls_getter, dealloc, dealloc_size=dealloc_size)
    return bytes(b)


def mk_router_table(rva, table, obj_size, tls_slot, tls_getter, dealloc):
    b = bytearray(bytes.fromhex('40 53 48 83 ec 20'))
    b += _lea_rax_rip(rva + len(b), table)
    b += bytes.fromhex('48 8b d9 48 89 01 f6 c2 01 74 5b 48 89 7c 24 30 f6 c2 04 75 42')
    b += bytes.fromhex('0f b7 41 08 b9 ff ff 00 00 66 3b c1 75 07 bf')
    b += struct.pack('<I', obj_size)
    b += bytes.fromhex('eb 03 0f b7 f8')
    b += bytes.fromhex('8b 0d') + _rel32(rva + len(b), 6, tls_slot)
    b += bytes.fromhex('ff 15') + _rel32(rva + len(b), 6, tls_getter)
    b += bytes.fromhex('44 8b c7 48 8b d3 48 8b 48 58 48 8b 01 ff 50 10')
    b += bytes.fromhex('48 8b 7c 24 30 48 8b c3 48 83 c4 20 5b c3')
    b += bytes([0xba]) + struct.pack('<I', obj_size)
    b += _call_rel32(rva + len(b), dealloc)
    b += bytes.fromhex('48 8b 7c 24 30 48 8b c3 48 83 c4 20 5b c3')
    return bytes(b)


def mk_router_member_cleanup(rva, mem_off, mem_cleanup, base_cleanup, obj_size, tls_slot, tls_getter, dealloc):
    b = bytearray(PROLOG_RBX_RDI + bytes.fromhex('48 8b d9 8b fa') + _add_rcx(mem_off))
    b += _call_rel32(rva + len(b), mem_cleanup)
    b += bytes.fromhex('48 8b cb')
    b += _call_rel32(rva + len(b), base_cleanup)
    b += _router_dil_tail(rva + len(b), obj_size, tls_slot, tls_getter, dealloc)
    return bytes(b)


def mk_router_member_table(rva, mem_off, mem_cleanup, table, obj_size, tls_slot, tls_getter, dealloc):
    b = bytearray(PROLOG_RBX_RDI + bytes.fromhex('48 8b d9 8b fa') + _add_rcx(mem_off))
    b += _call_rel32(rva + len(b), mem_cleanup)
    b += _lea_rax_rip(rva + len(b), table)
    b += bytes.fromhex('48 89 03')
    b += _router_dil_tail(rva + len(b), obj_size, tls_slot, tls_getter, dealloc)
    return bytes(b)


def mk_router_fixed_table(rva, table, obj_size, tls_slot, tls_getter, dealloc):
    b = bytearray(bytes.fromhex('40 53 48 83 ec 20'))
    b += _lea_rax_rip(rva + len(b), table)
    b += bytes.fromhex('48 8b d9 48 89 01 f6 c2 01 74 37 f6 c2 04 75 28')
    b += bytes.fromhex('8b 0d') + _rel32(rva + len(b), 6, tls_slot)
    b += bytes.fromhex('ff 15') + _rel32(rva + len(b), 6, tls_getter)
    b += bytes.fromhex('41 b8') + struct.pack('<I', obj_size)
    b += bytes.fromhex('48 8b d3 48 8b 48 58 48 8b 01 ff 50 10')
    b += bytes.fromhex('48 8b c3 48 83 c4 20 5b c3')
    b += bytes([0xba]) + struct.pack('<I', obj_size)
    b += _call_rel32(rva + len(b), dealloc)
    b += bytes.fromhex('48 8b c3 48 83 c4 20 5b c3')
    return bytes(b)


def mk_router_ref_member(rva, mem_off, ref_off, release_fn, mem_cleanup, base_cleanup,
                         obj_size, tls_slot, tls_getter, dealloc):
    b = bytearray(PROLOG_RBX_RDI + bytes.fromhex('48 8b d9 8b fa'))
    if ref_off < 0x80:
        b += bytes.fromhex('48 8b 49') + struct.pack('<b', ref_off)
    else:
        b += bytes.fromhex('48 8b 89') + struct.pack('<i', ref_off)
    b += bytes.fromhex('48 85 c9 74 05')
    b += _call_rel32(rva + len(b), release_fn)
    if mem_off < 0x80:
        b += bytes.fromhex('48 8d 4b') + struct.pack('<b', mem_off)
    else:
        b += bytes.fromhex('48 8d 8b') + struct.pack('<i', mem_off)
    if ref_off < 0x80:
        b += bytes.fromhex('48 c7 43') + struct.pack('<b', ref_off) + struct.pack('<i', 0)
    else:
        b += bytes.fromhex('48 c7 83') + struct.pack('<i', ref_off) + struct.pack('<i', 0)
    b += _call_rel32(rva + len(b), mem_cleanup)
    b += bytes.fromhex('48 8b cb')
    b += _call_rel32(rva + len(b), base_cleanup)
    b += _router_dil_tail(rva + len(b), obj_size, tls_slot, tls_getter, dealloc)
    return bytes(b)


def mk_heap_cleanup(rva, cleanup, obj_size, global_heap, dealloc):
    b = bytearray(PROLOG_RBX_RDI + bytes.fromhex('8b fa 48 8b d9'))
    b += _call_rel32(rva + len(b), cleanup)
    b += _heap_dil_tail(rva + len(b), obj_size, global_heap, dealloc)
    return bytes(b)


def mk_heap_table(rva, table, obj_size, global_heap, dealloc):
    b = bytearray(bytes.fromhex('40 53 48 83 ec 20'))
    b += _lea_rax_rip(rva + len(b), table)
    b += bytes.fromhex('48 8b d9 48 89 01 f6 c2 01 74 28 f6 c2 04 75 19')
    b += bytes.fromhex('48 8b 0d') + _rel32(rva + len(b), 7, global_heap)
    b += bytes.fromhex('48 8b d3 48 8b 01 ff 50 60')
    b += bytes.fromhex('48 8b c3 48 83 c4 20 5b c3')
    b += bytes([0xba]) + struct.pack('<I', obj_size)
    b += _call_rel32(rva + len(b), dealloc)
    b += bytes.fromhex('48 8b c3 48 83 c4 20 5b c3')
    return bytes(b)


def mk_heap_table_cleanup(rva, table, cleanup, obj_size, global_heap, dealloc):
    b = bytearray(PROLOG_RBX_RDI)
    b += _lea_rax_rip(rva + len(b), table)
    b += bytes.fromhex('8b fa 48 89 01 48 8b d9')
    b += _call_rel32(rva + len(b), cleanup)
    b += _heap_dil_tail(rva + len(b), obj_size, global_heap, dealloc)
    return bytes(b)


def mk_heap_dual_table(rva, t0, t1, off1, cleanup, obj_size, global_heap, dealloc):
    b = bytearray(PROLOG_RBX_RDI)
    b += _lea_rax_rip(rva + len(b), t0)
    b += bytes.fromhex('8b fa 48 89 01 48 8b d9')
    b += _lea_rax_rip(rva + len(b), t1)
    b += _mov_mem_rcx_rax(off1)
    b += _call_rel32(rva + len(b), cleanup)
    b += _heap_dil_tail(rva + len(b), obj_size, global_heap, dealloc)
    return bytes(b)


def mk_heap_triple_table(rva, t0, t1, off1, t2, off2, sub_cleanup, base_cleanup,
                         obj_size, global_heap, dealloc):
    b = bytearray(PROLOG_RBX_RDI)
    b += _lea_rax_rip(rva + len(b), t0)
    b += bytes.fromhex('48 8b d9 48 89 01 8b fa')
    b += _lea_rax_rip(rva + len(b), t1)
    b += _mov_mem_rcx_rax(off1)
    b += _add_rcx(off2)
    b += _lea_rax_rip(rva + len(b), t2)
    b += bytes.fromhex('48 89 01')
    b += _call_rel32(rva + len(b), sub_cleanup)
    b += bytes.fromhex('48 8b cb')
    b += _call_rel32(rva + len(b), base_cleanup)
    b += _heap_dil_tail(rva + len(b), obj_size, global_heap, dealloc)
    return bytes(b)


def mk_heap_five_table(rva, t0, t1, off1, t2, off2, sub_cleanup, t3, t4, base_cleanup,
                       obj_size, global_heap, dealloc):
    b = bytearray(PROLOG_RBX_RDI)
    b += _lea_rax_rip(rva + len(b), t0)
    b += bytes.fromhex('48 8b d9 48 89 01 8b fa')
    b += _lea_rax_rip(rva + len(b), t1)
    b += _mov_mem_rcx_rax(off1)
    b += _add_rcx(off2)
    b += _lea_rax_rip(rva + len(b), t2)
    b += bytes.fromhex('48 89 01')
    b += _call_rel32(rva + len(b), sub_cleanup)
    b += _lea_rax_rip(rva + len(b), t3)
    b += bytes.fromhex('48 8b cb 48 89 03')
    b += _lea_rax_rip(rva + len(b), t4)
    b += _mov_mem_rbx_rax(off1)
    b += _call_rel32(rva + len(b), base_cleanup)
    b += _heap_dil_tail(rva + len(b), obj_size, global_heap, dealloc)
    return bytes(b)


class CustomDeallocTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('iced_x86'), 'local generator requires iced-x86==1.21.0')
    def test_discover_validates_all_twelve_shapes_and_rejects_invalid(self):
        text = bytearray(0x2000)
        rdata = bytearray(0x200)
        data = bytearray(0x200)
        extents = {}

        def place(rva, code):
            extents[rva] = len(code)
            text[rva - 0x1000:rva - 0x1000 + len(code)] = code

        # Indexed callees
        dealloc = 0x1000
        cleanup = 0x1010
        mem_cleanup = 0x1020
        release_fn = 0x1030
        for c in (dealloc, cleanup, mem_cleanup, release_fn):
            place(c, bytes([0xc3]))

        # Static storage in .rdata (0x3000) and .data (0x4000)
        tls_getter = 0x3000
        t0, t1, t2, t3, t4 = 0x3010, 0x3020, 0x3030, 0x3040, 0x3050
        tls_slot = 0x4004
        global_heap = 0x4010

        # Positive cases: all 12 templates (including disp32 offsets >= 0x80)
        place(0x1100, mk_router_cleanup(0x1100, cleanup, 24, tls_slot, tls_getter, dealloc))
        place(0x1200, mk_router_table(0x1200, t0, 32, tls_slot, tls_getter, dealloc))
        place(0x1300, mk_router_member_cleanup(0x1300, 0x38, mem_cleanup, cleanup, 72, tls_slot, tls_getter, dealloc))
        place(0x1400, mk_router_member_table(0x1400, 0x10, mem_cleanup, t0, 24, tls_slot, tls_getter, dealloc))
        place(0x1500, mk_router_fixed_table(0x1500, t0, 16, tls_slot, tls_getter, dealloc))
        place(0x1600, mk_router_ref_member(0x1600, 0x38, 0x90, release_fn, mem_cleanup, cleanup, 160, tls_slot, tls_getter, dealloc))
        place(0x1700, mk_heap_cleanup(0x1700, cleanup, 16, global_heap, dealloc))
        place(0x1800, mk_heap_table(0x1800, t0, 32, global_heap, dealloc))
        place(0x1900, mk_heap_table_cleanup(0x1900, t0, cleanup, 24, global_heap, dealloc))
        place(0x1a00, mk_heap_dual_table(0x1a00, t0, t1, 0x20, cleanup, 112, global_heap, dealloc))
        place(0x1b00, mk_heap_triple_table(0x1b00, t0, t1, 0x20, t2, 0x98, mem_cleanup, cleanup, 168, global_heap, dealloc))
        place(0x1c00, mk_heap_five_table(0x1c00, t0, t1, 0x20, t2, 0x108, mem_cleanup, t3, t4, cleanup, 328, global_heap, dealloc))

        # Negative cases (all must be rejected):
        place(0x1d00, mk_router_cleanup(0x1d00, cleanup, 0, tls_slot, tls_getter, dealloc))                  # zero size
        place(0x1e00, mk_router_cleanup(0x1e00, cleanup, 24, tls_slot, tls_getter, dealloc, dealloc_size=32))  # size mismatch
        place(0x1f00, mk_router_cleanup(0x1f00, 0x1011, 24, tls_slot, tls_getter, dealloc))                  # unindexed cleanup
        place(0x2000, mk_router_cleanup(0x2000, dealloc, 24, tls_slot, tls_getter, dealloc))                 # cleanup == dealloc
        place(0x2100, mk_router_cleanup(0x2100, cleanup, 24, 0x3004, tls_getter, dealloc))                   # tls_slot in .rdata
        place(0x2200, mk_router_cleanup(0x2200, cleanup, 24, 0x4002, tls_getter, dealloc))                   # unaligned tls_slot
        place(0x2300, mk_router_cleanup(0x2300, cleanup, 24, tls_slot, 0x4010, dealloc))                     # tls_getter in .data
        place(0x2400, mk_heap_table(0x2400, 0x4020, 32, global_heap, dealloc))                               # table in .data
        place(0x2500, mk_heap_cleanup(0x2500, cleanup, 16, 0x3008, dealloc))                                 # heap in .rdata
        place(0x2600, mk_heap_cleanup(0x2600, cleanup, 16, 0x4014, dealloc))                                 # unaligned heap
        place(0x2700, mk_router_member_cleanup(0x2700, 0x0c, mem_cleanup, cleanup, 24, tls_slot, tls_getter, dealloc))  # unaligned offset
        place(0x2800, mk_heap_cleanup(0x2800, cleanup, 16, global_heap, dealloc))                            # overlaps matched
        place(0x2900, mk_heap_cleanup(0x2900, cleanup, 16, global_heap, dealloc))                            # EH handler in .pdata

        # Add a .pdata + unwind entry with EHANDLER flag (0x09) for 0x2900
        rdata[0x100:0x104] = bytes([0x09, 0x00, 0x00, 0x00])
        pdata = struct.pack('<III', 0x2900, 0x2900 + extents[0x2900], 0x3100)

        image = PeImage(assemble_pe([
            ('.rdata', 0x3000, rdata, 0x40000040),
            ('.data', 0x4000, data, 0xc0000040),
            ('.pdata', 0x5000, pdata, 0x40000040),
            ('.text', 0x1000, text, 0x60000020),
        ], (0x5000, len(pdata))))
        inventory = {0x2802: dict(size=4, status='matched')}
        found = generator.discover(image, extents, inventory)
        self.assertEqual(
            [(m.rva, m.family, m.object_size) for m in found],
            [
                (0x1100, generator.ROUTER_CLEANUP, 24),
                (0x1200, generator.ROUTER_TABLE, 32),
                (0x1300, generator.ROUTER_MEMBER_CLEANUP, 72),
                (0x1400, generator.ROUTER_MEMBER_TABLE, 24),
                (0x1500, generator.ROUTER_FIXED_TABLE, 16),
                (0x1600, generator.ROUTER_REF_MEMBER, 160),
                (0x1700, generator.HEAP_CLEANUP, 16),
                (0x1800, generator.HEAP_TABLE, 32),
                (0x1900, generator.HEAP_TABLE_CLEANUP, 24),
                (0x1a00, generator.HEAP_DUAL_TABLE, 112),
                (0x1b00, generator.HEAP_TRIPLE_TABLE, 168),
                (0x1c00, generator.HEAP_FIVE_TABLE, 328),
            ],
        )

    @unittest.skipUnless(importlib.util.find_spec('iced_x86'), 'local generator requires iced-x86==1.21.0')
    def test_discover_shards_large_families(self):
        count = generator.SHARD_SIZE + 2
        text = bytearray(0x80 * (count + 2))
        extents = {0x1000: 1, 0x1010: 1}
        text[0] = 0xc3
        text[0x10] = 0xc3
        global_heap = 0x5000
        for idx in range(count):
            rva = 0x1080 + idx * 0x80
            code = mk_heap_cleanup(rva, 0x1010, 24, global_heap, 0x1000)
            extents[rva] = len(code)
            text[rva - 0x1000:rva - 0x1000 + len(code)] = code
        image = PeImage(assemble_pe([
            ('.data', 0x5000, bytes(0x20), 0xc0000040),
            ('.text', 0x1000, text, 0x60000020),
        ], (0, 0)))
        members = generator.discover(image, extents, {})
        self.assertEqual(len(members), count)
        self.assertEqual([m.family for m in members[:generator.SHARD_SIZE]],
                         [f'{generator.HEAP_CLEANUP}1'] * generator.SHARD_SIZE)
        self.assertEqual([m.family for m in members[generator.SHARD_SIZE:]],
                         [f'{generator.HEAP_CLEANUP}2'] * 2)

    def test_emit_produces_clean_units_and_bindings(self):
        members = [
            generator.Member(0x1100, 125, generator.ROUTER_CLEANUP, 24, 0x1000, tls_slot=0x4004, tls_getter=0x3000, cleanup=0x1010),
            generator.Member(0x1200, 124, generator.ROUTER_TABLE, 32, 0x1000, tls_slot=0x4004, tls_getter=0x3000, tables=(0x3010,), table_offsets=(0,)),
            generator.Member(0x1300, 137, generator.ROUTER_MEMBER_CLEANUP, 72, 0x1000, tls_slot=0x4004, tls_getter=0x3000, cleanup=0x1010, member_cleanup=0x1020, member_offset=0x38),
            generator.Member(0x1400, 139, generator.ROUTER_MEMBER_TABLE, 24, 0x1000, tls_slot=0x4004, tls_getter=0x3000, member_cleanup=0x1020, tables=(0x3010,), table_offsets=(0,), member_offset=0x10),
            generator.Member(0x1500, 88, generator.ROUTER_FIXED_TABLE, 16, 0x1000, tls_slot=0x4004, tls_getter=0x3000, tables=(0x3010,), table_offsets=(0,)),
            generator.Member(0x1600, 165, generator.ROUTER_REF_MEMBER, 160, 0x1000, tls_slot=0x4004, tls_getter=0x3000, cleanup=0x1010, member_cleanup=0x1020, release_callee=0x1030, member_offset=0x38, ref_offset=0x90),
            generator.Member(0x1700, 89, generator.HEAP_CLEANUP, 16, 0x1000, global_heap=0x4010, cleanup=0x1010),
            generator.Member(0x1800, 73, generator.HEAP_TABLE, 32, 0x1000, global_heap=0x4010, tables=(0x3010,), table_offsets=(0,)),
            generator.Member(0x1900, 99, generator.HEAP_TABLE_CLEANUP, 24, 0x1000, global_heap=0x4010, cleanup=0x1010, tables=(0x3010,), table_offsets=(0,)),
            generator.Member(0x1a00, 110, generator.HEAP_DUAL_TABLE, 112, 0x1000, global_heap=0x4010, cleanup=0x1010, tables=(0x3010, 0x3020), table_offsets=(0, 0x20)),
            generator.Member(0x1b00, 135, generator.HEAP_TRIPLE_TABLE, 168, 0x1000, global_heap=0x4010, cleanup=0x1010, member_cleanup=0x1020, tables=(0x3010, 0x3020, 0x3030), table_offsets=(0, 0x20, 0x98)),
            generator.Member(0x1c00, 156, generator.HEAP_FIVE_TABLE, 328, 0x1000, global_heap=0x4010, cleanup=0x1010, member_cleanup=0x1020, tables=(0x3010, 0x3020, 0x3030, 0x3040, 0x3050), table_offsets=(0, 0x20, 0x108)),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for m in members:
                task, directory = generator.emit(root, m.family, [m], 'synthetic', 'synthetic')
                src = root / task['compiled']
                hdr = src.with_suffix('.h')
                text = src.read_text()
                self.assertIn(f'// 0x{m.rva:x} {m.family}::{m.name}', text)
                self.assertIn(f'GlobalDeallocTarget1000(object, {m.object_size}ull);', text)
                symbols = json.loads((directory / 'symbols.json').read_text())['symbols']
                self.assertEqual(symbols[m.symbol], dict(rva=m.rva, size=m.size))
                self.assertEqual(contrib_screen.screen_tree(root, task['compiled']), [])
                for path in (src, hdr):
                    self.assertEqual(lint_reconstruction.lint_file(
                        root, path.relative_to(root).as_posix(), 'synthetic', compact=True), [])
            units = check_code_rules.analyse(root)
            match_findings = [(name, f) for name, unit in units.items()
                              for f in unit.findings if f[1] in check_code_rules.MATCH_RULES]
            self.assertEqual(match_findings, [])


if __name__ == '__main__':
    unittest.main()
