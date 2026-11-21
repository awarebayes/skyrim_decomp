"""Draft lazy static-slot initializers and singleton-registration wrappers.

    python tools/lazy_static_generate.py --exe /path/to/SkyrimSE.exe
    python tools/lazy_static_generate.py --exe /path/to/SkyrimSE.exe --out .local/lazy-static --compare

Requires iced-x86==1.21.0. --compare uses the pinned contributor compiler and
checks the full code, unwind information, static storage references and direct
call targets for every generated member.
"""
from dataclasses import dataclass, replace

import leaf_family_batch
from pecoff import Reject, SCN_MEM_EXECUTE


INIT = 'LazyStaticInitializers'
REGISTER = 'LazyStaticRegistrations'
SHARD_SIZE = 100


@dataclass(frozen=True)
class Member:
    rva: int
    size: int
    family: str
    slot: int
    descriptor: int
    callee: int
    storage: int | None = None
    callback: int | None = None
    register: int | None = None

    @property
    def name(self):
        return f'Resolve{self.rva:x}' if self.register is None else f'Register{self.rva:x}'

    @property
    def symbol(self):
        ret = 'I' if self.register is None else 'X'
        return f'?{self.name}@{self.family}@@SA{ret}XZ'


def _classify_init(insns, rva, size):
    from iced_x86 import Code, Mnemonic, Register

    if (len(insns) != 11
            or insns[0].code != Code.SUB_RM64_IMM8 or insns[0].op0_register != Register.RSP
            or insns[0].immediate8 != 0x28 or insns[0].len != 4
            or insns[1].code != Code.MOV_R32_RM32 or insns[1].op0_register != Register.EAX
            or insns[1].memory_base != Register.RIP or not insns[1].is_ip_rel_memory_operand
            or insns[1].has_segment_prefix or insns[1].len != 6
            or insns[2].code != Code.TEST_RM32_R32 or insns[2].op0_register != Register.EAX
            or insns[2].op1_register != Register.EAX or insns[2].len != 2
            or insns[3].code != Code.JNE_REL8_64 or insns[3].len != 2
            or insns[3].near_branch_target != insns[9].ip
            or insns[4].mnemonic != Mnemonic.XOR or insns[4].op0_register != Register.R8D
            or insns[4].op1_register != Register.R8D or insns[4].len != 3
            or insns[5].code != Code.LEA_R64_M or insns[5].op0_register != Register.RDX
            or insns[5].memory_base != Register.RIP or not insns[5].is_ip_rel_memory_operand
            or insns[5].has_segment_prefix or insns[5].len != 7
            or insns[6].code != Code.LEA_R64_M or insns[6].op0_register != Register.RCX
            or insns[6].memory_base != Register.RIP or not insns[6].is_ip_rel_memory_operand
            or insns[6].has_segment_prefix or insns[6].len != 7
            or insns[7].code != Code.CALL_REL32_64 or insns[7].len != 5
            or insns[8].code != Code.MOV_R32_RM32 or insns[8].op0_register != Register.EAX
            or insns[8].memory_base != Register.RIP or not insns[8].is_ip_rel_memory_operand
            or insns[8].has_segment_prefix or insns[8].len != 6
            or insns[9].code != Code.ADD_RM64_IMM8 or insns[9].op0_register != Register.RSP
            or insns[9].immediate8 != 0x28 or insns[9].len != 4
            or insns[10].code != Code.RETNQ or insns[10].len != 1):
        return None
    slot = insns[1].ip_rel_memory_address
    if insns[6].ip_rel_memory_address != slot or insns[8].ip_rel_memory_address != slot:
        return None
    descriptor = insns[5].ip_rel_memory_address
    if descriptor == slot:
        return None
    return Member(rva, size, INIT, slot, descriptor, insns[7].near_branch_target)


def _classify_register(insns, rva, size):
    from iced_x86 import Code, Register

    if (len(insns) != 12
            or insns[0].code != Code.SUB_RM64_IMM8 or insns[0].op0_register != Register.RSP
            or insns[0].immediate8 != 0x28 or insns[0].len != 4
            or insns[1].code != Code.MOV_R64_RM64 or insns[1].op0_register != Register.RAX
            or insns[1].memory_base != Register.RIP or not insns[1].is_ip_rel_memory_operand
            or insns[1].has_segment_prefix or insns[1].len != 7
            or insns[2].code != Code.TEST_RM64_R64 or insns[2].op0_register != Register.RAX
            or insns[2].op1_register != Register.RAX or insns[2].len != 3
            or insns[3].code != Code.JNE_REL8_64 or insns[3].len != 2
            or insns[3].near_branch_target != insns[7].ip
            or insns[4].code != Code.LEA_R64_M or insns[4].op0_register != Register.RCX
            or insns[4].memory_base != Register.RIP or not insns[4].is_ip_rel_memory_operand
            or insns[4].has_segment_prefix or insns[4].len != 7
            or insns[5].code != Code.CALL_REL32_64 or insns[5].len != 5
            or insns[6].code != Code.MOV_RM64_R64 or insns[6].op1_register != Register.RAX
            or insns[6].memory_base != Register.RIP or not insns[6].is_ip_rel_memory_operand
            or insns[6].has_segment_prefix or insns[6].len != 7
            or insns[7].code != Code.LEA_R64_M or insns[7].op0_register != Register.R8
            or insns[7].memory_base != Register.RIP or not insns[7].is_ip_rel_memory_operand
            or insns[7].has_segment_prefix or insns[7].len != 7
            or insns[8].code != Code.MOV_R64_RM64 or insns[8].op0_register != Register.RCX
            or insns[8].op1_register != Register.RAX or insns[8].len != 3
            or insns[9].code != Code.LEA_R64_M or insns[9].op0_register != Register.RDX
            or insns[9].memory_base != Register.RIP or not insns[9].is_ip_rel_memory_operand
            or insns[9].has_segment_prefix or insns[9].len != 7
            or insns[10].code != Code.ADD_RM64_IMM8 or insns[10].op0_register != Register.RSP
            or insns[10].immediate8 != 0x28 or insns[10].len != 4
            or insns[11].code != Code.JMP_REL32_64 or insns[11].len != 5):
        return None
    slot = insns[1].ip_rel_memory_address
    if insns[6].ip_rel_memory_address != slot:
        return None
    storage = insns[4].ip_rel_memory_address
    descriptor = insns[9].ip_rel_memory_address
    create = insns[5].near_branch_target
    callback = insns[7].ip_rel_memory_address
    register = insns[11].near_branch_target
    if len({slot, storage, descriptor}) != 3 or len({create, callback, register}) != 3:
        return None
    return Member(rva, size, REGISTER, slot, descriptor, create, storage, callback, register)


def classify(code, rva):
    from iced_x86 import Decoder

    insns = list(Decoder(64, code, ip=rva))
    if any(i.is_invalid for i in insns):
        return None
    if len(code) == 47:
        return _classify_init(insns, rva, len(code))
    if len(code) == 61:
        return _classify_register(insns, rva, len(code))
    return None


def _writable_data(image, address, width):
    try:
        section = image.section_for(address)
        return (section.name == '.data'
                and not (section.flags & SCN_MEM_EXECUTE)
                and bool(section.flags & 0x80000000)
                and address % width == 0
                and address + width <= section.vaddr + section.vsize)
    except Reject:
        return False


def _nonexec_data(image, address, allowed_names):
    try:
        section = image.section_for(address)
        return (section.name in allowed_names
                and not (section.flags & SCN_MEM_EXECUTE)
                and address < section.vaddr + section.vsize)
    except Reject:
        return False


def _indexed_target(image, member, target, starts):
    return leaf_family_batch.indexed_callee(image, replace(member, callee=target), starts)


def discover(image, extents, inventory):
    starts = set(extents) | {begin for begin, _, _ in image.runtime_functions()}
    raw = []
    for m in leaf_family_batch.candidates(image, extents, inventory, (47, 61), classify):
        if m.register is None:
            if not (_writable_data(image, m.slot, 4)
                    and _nonexec_data(image, m.descriptor, {'.rdata'})
                    and _indexed_target(image, m, m.callee, starts)):
                continue
        else:
            if not (_writable_data(image, m.slot, 8)
                    and _writable_data(image, m.storage, 1)
                    and _nonexec_data(image, m.descriptor, {'.data', '.rdata'})
                    and _indexed_target(image, m, m.callee, starts)
                    and _indexed_target(image, m, m.callback, starts)
                    and _indexed_target(image, m, m.register, starts)):
                continue
        raw.append(m)
    result = []
    for base in (INIT, REGISTER):
        rows = [m for m in raw if m.family == base]
        member_rvas = {m.rva for m in rows}
        if base == INIT:
            clean = [m for m in rows if m.callee not in member_rvas]
        else:
            slots = {m.slot for m in rows}
            storages = {m.storage for m in rows}
            descriptors = {m.descriptor for m in rows}
            creates = {m.callee for m in rows}
            callbacks = {m.callback for m in rows}
            registers = {m.register for m in rows}
            clean = [m for m in rows
                     if m.slot not in (storages | descriptors)
                     and m.storage not in descriptors
                     and not ({m.callee, m.callback, m.register} & member_rvas)
                     and m.callee not in (callbacks | registers)
                     and m.callback not in registers]
        if len(clean) <= SHARD_SIZE:
            result.extend(clean)
        else:
            for index in range(0, len(clean), SHARD_SIZE):
                shard = f'{base}{index // SHARD_SIZE + 1}'
                result.extend(replace(m, family=shard) for m in clean[index:index + SHARD_SIZE])
    return result


def emit(root, family, members, build_id, label):
    prefix = ['// Source exposure: mixed (pinned image and community function boundaries).',
              f'// Boundary source: {label}',
              '// Code origin: original lazy static-initialization wrapper template.',
              f'// {family}, methods and referenced symbols: GUESS(low) STANDIN; original owners and signatures unknown.',
              '// Adapted bodies: none']
    header = prefix + ['#pragma once', '']
    source = prefix + [f'// 0x{m.rva:x} {family}::{m.name}' for m in members] + [f'#include "{family}.h"']
    symbols = {}
    if family.startswith(INIT):
        for slot in sorted({m.slot for m in members}):
            name = f'CachedValue{slot:x}'
            header.append(f'extern "C" unsigned int {name};')
            symbols[name] = dict(rva=slot, size=None)
        for desc in sorted({m.descriptor for m in members}):
            name = f'DescriptorTarget{desc:x}'
            header.append(f'extern "C" const unsigned char {name};')
            symbols[name] = dict(rva=desc, size=None)
        for callee in sorted({m.callee for m in members}):
            name = f'InitTarget{callee:x}'
            header.append(f'extern "C" void {name}(unsigned int* slot, const void* descriptor, unsigned int flags);')
            symbols[name] = dict(rva=callee, size=None)
    else:
        header.append('struct StaticStorage;')
        for slot in sorted({m.slot for m in members}):
            name = f'SingletonSlot{slot:x}'
            header.append(f'extern "C" void* {name};')
            symbols[name] = dict(rva=slot, size=None)
        for stor in sorted({m.storage for m in members}):
            name = f'StorageSlot{stor:x}'
            header.append(f'extern "C" StaticStorage {name};')
            symbols[name] = dict(rva=stor, size=None)
        for desc in sorted({m.descriptor for m in members}):
            name = f'DescriptorSlot{desc:x}'
            header.append(f'extern "C" const unsigned char {name};')
            symbols[name] = dict(rva=desc, size=None)
        for cb in sorted({m.callback for m in members}):
            name = f'CallbackTarget{cb:x}'
            header.append(f'extern "C" void {name}();')
            symbols[name] = dict(rva=cb, size=None)
        for create in sorted({m.callee for m in members}):
            name = f'CreateTarget{create:x}'
            header.append(f'extern "C" void* {name}(StaticStorage* storage);')
            symbols[name] = dict(rva=create, size=None)
        for reg in sorted({m.register for m in members}):
            name = f'RegisterTarget{reg:x}'
            header.append(f'extern "C" void {name}(void* instance, const void* descriptor, void (*callback)());')
            symbols[name] = dict(rva=reg, size=None)
    header.extend(['', f'struct {family}', '{'])
    functions = []
    for m in members:
        if m.register is None:
            header.append(f'    static unsigned int {m.name}();')
            body = [
                '',
                f'unsigned int {family}::{m.name}()',
                '{',
                f'    if (CachedValue{m.slot:x} == 0u)',
                '    {',
                f'        InitTarget{m.callee:x}(&CachedValue{m.slot:x}, &DescriptorTarget{m.descriptor:x}, 0u);',
                '    }',
                f'    return CachedValue{m.slot:x};',
                '}',
            ]
        else:
            header.append(f'    static void {m.name}();')
            body = [
                '',
                f'void {family}::{m.name}()',
                '{',
                f'    if (SingletonSlot{m.slot:x} == nullptr)',
                '    {',
                f'        SingletonSlot{m.slot:x} = CreateTarget{m.callee:x}(&StorageSlot{m.storage:x});',
                '    }',
                f'    RegisterTarget{m.register:x}(SingletonSlot{m.slot:x}, &DescriptorSlot{m.descriptor:x}, &CallbackTarget{m.callback:x});',
                '}',
            ]
        source.extend(body)
        symbols[m.symbol] = dict(rva=m.rva, size=m.size)
        functions.append(dict(rva=m.rva, size=m.size, symbol=m.symbol))
    header.append('};')
    return leaf_family_batch.write_unit(root, family, build_id, header, source, symbols, functions)


if __name__ == '__main__':
    raise SystemExit(leaf_family_batch.run(__doc__, discover, emit))
