"""Lazy static initializers and singleton registrations in a synthetic PE image."""
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
import lazy_static_generate as generator
import lint_reconstruction
from pecoff import PeImage
from synthetic_pecoff import assemble_pe


def rel32(opcode, at, target):
    return opcode + struct.pack('<i', target - (at + len(opcode) + 4))


def lazy_init(rva, slot, desc, callee, *, slot2=None):
    slot2 = slot if slot2 is None else slot2
    parts = [bytes.fromhex('48 83 ec 28')]
    pos = rva + 4
    parts.append(rel32(bytes.fromhex('8b 05'), pos, slot))
    pos += 6
    parts.append(bytes.fromhex('85 c0 75 1c 45 33 c0'))
    pos += 7
    parts.append(rel32(bytes.fromhex('48 8d 15'), pos, desc))
    pos += 7
    parts.append(rel32(bytes.fromhex('48 8d 0d'), pos, slot2))
    pos += 7
    parts.append(rel32(bytes([0xe8]), pos, callee))
    pos += 5
    parts.append(rel32(bytes.fromhex('8b 05'), pos, slot))
    parts.append(bytes.fromhex('48 83 c4 28 c3'))
    return b''.join(parts)


def lazy_reg(rva, slot, storage, create, callback, desc, reg, *, slot2=None):
    slot2 = slot if slot2 is None else slot2
    parts = [bytes.fromhex('48 83 ec 28')]
    pos = rva + 4
    parts.append(rel32(bytes.fromhex('48 8b 05'), pos, slot))
    pos += 7
    parts.append(bytes.fromhex('48 85 c0 75 13'))
    pos += 5
    parts.append(rel32(bytes.fromhex('48 8d 0d'), pos, storage))
    pos += 7
    parts.append(rel32(bytes([0xe8]), pos, create))
    pos += 5
    parts.append(rel32(bytes.fromhex('48 89 05'), pos, slot2))
    pos += 7
    parts.append(rel32(bytes.fromhex('4c 8d 05'), pos, callback))
    pos += 7
    parts.append(bytes.fromhex('48 8b c8'))
    pos += 3
    parts.append(rel32(bytes.fromhex('48 8d 15'), pos, desc))
    pos += 7
    parts.append(bytes.fromhex('48 83 c4 28'))
    pos += 4
    parts.append(rel32(bytes([0xe9]), pos, reg))
    return b''.join(parts)


class LazyStaticTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('iced_x86'), 'local generator requires iced-x86==1.21.0')
    def test_discover_validates_both_shapes_storage_and_callees(self):
        text = bytearray(1024)
        extents = {}

        def place(rva, code):
            extents[rva] = len(code)
            text[rva - 0x1000:rva - 0x1000 + len(code)] = code

        place(0x1000, bytes([0xc3]))  # init / create
        place(0x1010, bytes([0xc3]))  # callback
        place(0x1020, bytes([0xc3]))  # register
        place(0x1040, lazy_init(0x1040, 0x2000, 0x3000, 0x1000))
        place(0x1080, lazy_reg(0x1080, 0x2008, 0x2010, 0x1000, 0x1010, 0x2020, 0x1020))
        place(0x10d0, lazy_reg(0x10d0, 0x2008, 0x2010, 0x1000, 0x1010, 0x3010, 0x1020))  # .rdata descriptor ok
        place(0x1120, lazy_init(0x1120, 0x2000, 0x3000, 0x1000, slot2=0x2004))           # mismatched slot
        place(0x1160, lazy_init(0x1160, 0x2002, 0x3000, 0x1000))                         # unaligned 4-byte slot
        place(0x11a0, lazy_init(0x11a0, 0x3000, 0x3008, 0x1000))                         # read-only slot rejected
        place(0x11e0, lazy_init(0x11e0, 0x2000, 0x2004, 0x1000))                         # writable descriptor rejected
        place(0x1220, lazy_reg(0x1220, 0x2008, 0x2010, 0x1000, 0x1011, 0x2020, 0x1020))  # unindexed callback
        place(0x1270, lazy_reg(0x1270, 0x2008, 0x2010, 0x1000, 0x1010, 0x1000, 0x1020))  # executable descriptor
        place(0x12c0, lazy_init(0x12c0, 0x2000, 0x3000, 0x1000))                         # overlaps matched entry

        image = PeImage(assemble_pe([
            ('.text', 0x1000, text, 0x60000020),
            ('.data', 0x2000, bytes(64), 0xc0000040),
            ('.rdata', 0x3000, bytes(64), 0x40000040),
        ], (0, 0)))
        inventory = {0x12bf: dict(size=2, status='matched')}
        self.assertEqual(
            generator.discover(image, extents, inventory),
            [
                generator.Member(0x1040, 47, generator.INIT, 0x2000, 0x3000, 0x1000),
                generator.Member(0x1080, 61, generator.REGISTER, 0x2008, 0x2020, 0x1000, 0x2010, 0x1010, 0x1020),
                generator.Member(0x10d0, 61, generator.REGISTER, 0x2008, 0x3010, 0x1000, 0x2010, 0x1010, 0x1020),
            ],
        )

    def test_emit_produces_clean_units_and_bindings(self):
        members = [
            generator.Member(0x1040, 47, generator.INIT, 0x2000, 0x3000, 0x1000),
            generator.Member(0x1080, 61, generator.REGISTER, 0x2008, 0x2020, 0x1000, 0x2010, 0x1010, 0x1020),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for m in members:
                task, directory = generator.emit(root, m.family, [m], 'synthetic', 'synthetic')
                src = root / task['compiled']
                hdr = src.with_suffix('.h')
                text = src.read_text()
                self.assertIn(f'// 0x{m.rva:x} {m.family}::{m.name}', text)
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
