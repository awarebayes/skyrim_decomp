"""Draft custom-allocator scalar deleting destructors (TLS-router and global-heap forms).

    python tools/custom_dealloc_generate.py --exe /path/to/SkyrimSE.exe
    python tools/custom_dealloc_generate.py --exe /path/to/SkyrimSE.exe --out .local/custom-dealloc --compare

Requires iced-x86==1.21.0. --compare uses the pinned contributor compiler and
checks the full code, unwind information, static storage references and direct
call targets for every generated member.
"""
from dataclasses import dataclass, replace
from types import SimpleNamespace

import leaf_family_batch
from pecoff import Reject, SCN_MEM_EXECUTE

SCN_MEM_WRITE = 0x80000000


ROUTER_CLEANUP = 'RouterCleanupDeallocators'
ROUTER_TABLE = 'RouterTableDeallocators'
ROUTER_MEMBER_CLEANUP = 'RouterMemberCleanupDeallocators'
ROUTER_MEMBER_TABLE = 'RouterMemberTableDeallocators'
ROUTER_FIXED_TABLE = 'RouterFixedTableDeallocators'
ROUTER_REF_MEMBER = 'RouterRefMemberDeallocators'

HEAP_CLEANUP = 'HeapCleanupDeallocators'
HEAP_TABLE = 'HeapTableDeallocators'
HEAP_TABLE_CLEANUP = 'HeapTableCleanupDeallocators'
HEAP_DUAL_TABLE = 'HeapDualTableDeallocators'
HEAP_TRIPLE_TABLE = 'HeapTripleTableDeallocators'
HEAP_FIVE_TABLE = 'HeapFiveTableDeallocators'

BASE_FAMILIES = (
    ROUTER_CLEANUP,
    ROUTER_TABLE,
    ROUTER_MEMBER_CLEANUP,
    ROUTER_MEMBER_TABLE,
    ROUTER_FIXED_TABLE,
    ROUTER_REF_MEMBER,
    HEAP_CLEANUP,
    HEAP_TABLE,
    HEAP_TABLE_CLEANUP,
    HEAP_DUAL_TABLE,
    HEAP_TRIPLE_TABLE,
    HEAP_FIVE_TABLE,
)

SHARD_SIZE = 75
CANDIDATE_SIZES = range(70, 185)


@dataclass(frozen=True)
class Member:
    rva: int
    size: int
    family: str
    object_size: int
    global_dealloc: int
    # Allocator bindings
    tls_slot: int | None = None
    tls_getter: int | None = None
    global_heap: int | None = None
    # Teardown bindings
    cleanup: int | None = None
    member_cleanup: int | None = None
    release_callee: int | None = None
    tables: tuple[int, ...] = ()
    # Typed field offsets
    member_offset: int | None = None
    ref_offset: int | None = None
    table_offsets: tuple[int, ...] = ()

    @property
    def name(self):
        return f'Delete{self.rva:x}'

    @property
    def base_family(self):
        return self.family.rstrip('0123456789')

    @property
    def param_struct(self):
        bf = self.base_family
        if bf == HEAP_CLEANUP:
            return None
        if bf in (ROUTER_CLEANUP, ROUTER_TABLE):
            return f'{self.family}TaggedObject'
        if bf in (ROUTER_FIXED_TABLE, HEAP_TABLE, HEAP_TABLE_CLEANUP):
            return f'{self.family}TableObject'
        if bf in (ROUTER_MEMBER_CLEANUP, ROUTER_MEMBER_TABLE):
            return f'{self.family}MemberObject{self.member_offset:x}'
        if bf == ROUTER_REF_MEMBER:
            return f'{self.family}RefMemberObject{self.member_offset:x}_{self.ref_offset:x}'
        if bf == HEAP_DUAL_TABLE:
            return f'{self.family}DualTableObject{self.table_offsets[1]:x}'
        return f'{self.family}TripleTableObject{self.table_offsets[1]:x}_{self.table_offsets[2]:x}'

    @property
    def symbol(self):
        st = self.param_struct
        param = 'PEAX' if st is None else f'PEAU{st}@@'
        return f'?{self.name}@{self.family}@@SAPEAX{param}I@Z'


def _is_rip_lea(ins, reg):
    from iced_x86 import Code, Register
    return (ins.code == Code.LEA_R64_M and ins.op0_register == reg
            and ins.memory_base == Register.RIP and ins.is_ip_rel_memory_operand
            and not ins.has_segment_prefix and ins.len == 7)


def _is_rip_mov32(ins, reg):
    from iced_x86 import Code, Register
    return (ins.code == Code.MOV_R32_RM32 and ins.op0_register == reg
            and ins.memory_base == Register.RIP and ins.is_ip_rel_memory_operand
            and not ins.has_segment_prefix and ins.len == 6)


def _is_rip_mov64(ins, reg):
    from iced_x86 import Code, Register
    return (ins.code == Code.MOV_R64_RM64 and ins.op0_register == reg
            and ins.memory_base == Register.RIP and ins.is_ip_rel_memory_operand
            and not ins.has_segment_prefix and ins.len == 7)


def _is_rip_call64(ins):
    from iced_x86 import Code, Register
    return (ins.code == Code.CALL_RM64 and ins.memory_base == Register.RIP
            and ins.is_ip_rel_memory_operand and not ins.has_segment_prefix and ins.len == 6)


def _is_mem_store64(ins, base, src, disp=None):
    from iced_x86 import Code, Register
    if (ins.code != Code.MOV_RM64_R64 or ins.memory_base != base
            or ins.memory_index != Register.NONE or ins.op1_register != src):
        return False
    return disp is None or ins.memory_displacement == disp


def _is_mem_load64(ins, dst, base, disp=None):
    from iced_x86 import Code, Register
    if (ins.code != Code.MOV_R64_RM64 or ins.op0_register != dst
            or ins.memory_base != base or ins.memory_index != Register.NONE):
        return False
    return disp is None or ins.memory_displacement == disp


def _is_add_imm(ins, reg):
    from iced_x86 import Code
    if ins.op0_register != reg:
        return None
    if ins.code == Code.ADD_RM64_IMM8 and ins.len == 4:
        return ins.immediate8to64
    if ins.code == Code.ADD_RM64_IMM32 and ins.len == 7:
        return ins.immediate32to64
    return None


def _is_lea_disp(ins, dst, base):
    from iced_x86 import Code, Register
    if (ins.code == Code.LEA_R64_M and ins.op0_register == dst
            and ins.memory_base == base and ins.memory_index == Register.NONE
            and not ins.is_ip_rel_memory_operand and ins.len in (4, 7)):
        return ins.memory_displacement
    return None


def _match_epi_rbx_rdi(insns):
    """Match `mov rax, rbx; mov rbx, [rsp+30h]; add rsp, 20h; pop rdi; ret` (5 insns)."""
    from iced_x86 import Code, Register
    return (len(insns) == 5
            and insns[0].code == Code.MOV_R64_RM64 and insns[0].op0_register == Register.RAX
            and insns[0].op1_register == Register.RBX and insns[0].len == 3
            and _is_mem_load64(insns[1], Register.RBX, Register.RSP, 0x30) and insns[1].len == 5
            and insns[2].code == Code.ADD_RM64_IMM8 and insns[2].op0_register == Register.RSP
            and insns[2].immediate8 == 0x20 and insns[2].len == 4
            and insns[3].code == Code.POP_R64 and insns[3].op0_register == Register.RDI and insns[3].len == 1
            and insns[4].code == Code.RETNQ and insns[4].len == 1)


def _match_epi_rbx(insns):
    """Match `mov rax, rbx; add rsp, 20h; pop rbx; ret` (4 insns)."""
    from iced_x86 import Code, Register
    return (len(insns) == 4
            and insns[0].code == Code.MOV_R64_RM64 and insns[0].op0_register == Register.RAX
            and insns[0].op1_register == Register.RBX and insns[0].len == 3
            and insns[1].code == Code.ADD_RM64_IMM8 and insns[1].op0_register == Register.RSP
            and insns[1].immediate8 == 0x20 and insns[1].len == 4
            and insns[2].code == Code.POP_R64 and insns[2].op0_register == Register.RBX and insns[2].len == 1
            and insns[3].code == Code.RETNQ and insns[3].len == 1)


def _match_router_tail_dil_exact(tail):
    """Match 31-insn Havok size-tagged TLS-router/global-delete tail (flags in dil, this in rbx)."""
    from iced_x86 import Code, Register
    if len(tail) != 31:
        return None
    if not (tail[0].code == Code.TEST_RM8_IMM8 and tail[0].op0_register == Register.DIL
            and tail[0].immediate8 == 1 and tail[0].len == 4
            and tail[1].code == Code.JE_REL8_64 and tail[1].near_branch_target == tail[26].ip
            and tail[2].code == Code.TEST_RM8_IMM8 and tail[2].op0_register == Register.DIL
            and tail[2].immediate8 == 4 and tail[2].len == 4
            and tail[3].code == Code.JNE_REL8_64 and tail[3].near_branch_target == tail[23].ip
            and tail[4].code == Code.MOVZX_R32_RM16 and tail[4].op0_register == Register.EAX
            and tail[4].memory_base == Register.RBX and tail[4].memory_index == Register.NONE
            and tail[4].memory_displacement == 8 and tail[4].len == 4
            and tail[5].code == Code.MOV_R32_IMM32 and tail[5].op0_register == Register.ECX
            and tail[5].immediate32 == 0xffff and tail[5].len == 5
            and tail[6].code == Code.CMP_R16_RM16 and tail[6].op0_register == Register.AX
            and tail[6].op1_register == Register.CX and tail[6].len == 3
            and tail[7].code == Code.JNE_REL8_64 and tail[7].near_branch_target == tail[10].ip
            and tail[8].code == Code.MOV_R32_IMM32 and tail[8].op0_register == Register.EDI
            and tail[8].len == 5 and 0 < tail[8].immediate32 < 0x80000000
            and tail[9].code == Code.JMP_REL8_64 and tail[9].near_branch_target == tail[11].ip
            and tail[10].code == Code.MOVZX_R32_RM16 and tail[10].op0_register == Register.EDI
            and tail[10].op1_register == Register.AX and tail[10].len == 3
            and _is_rip_mov32(tail[11], Register.ECX)
            and _is_rip_call64(tail[12])
            and tail[13].code == Code.MOV_R32_RM32 and tail[13].op0_register == Register.R8D
            and tail[13].op1_register == Register.EDI and tail[13].len == 3
            and tail[14].code == Code.MOV_R64_RM64 and tail[14].op0_register == Register.RDX
            and tail[14].op1_register == Register.RBX and tail[14].len == 3
            and _is_mem_load64(tail[15], Register.RCX, Register.RAX, 0x58) and tail[15].len == 4
            and _is_mem_load64(tail[16], Register.RAX, Register.RCX, 0) and tail[16].len == 3
            and tail[17].code == Code.CALL_RM64 and tail[17].memory_base == Register.RAX
            and tail[17].memory_index == Register.NONE and tail[17].memory_displacement == 0x10
            and tail[17].len == 3
            and _match_epi_rbx_rdi(tail[18:23])
            and tail[23].code == Code.MOV_R32_IMM32 and tail[23].op0_register == Register.EDX
            and tail[23].len == 5 and tail[23].immediate32 == tail[8].immediate32
            and tail[24].code == Code.MOV_R64_RM64 and tail[24].op0_register == Register.RCX
            and tail[24].op1_register == Register.RBX and tail[24].len == 3
            and tail[25].code == Code.CALL_REL32_64 and tail[25].len == 5
            and _match_epi_rbx_rdi(tail[26:31])):
        return None
    return (tail[8].immediate32, tail[11].ip_rel_memory_address,
            tail[12].ip_rel_memory_address, tail[25].near_branch_target)


def _match_heap_tail_dil(tail):
    """Match 21-insn Scaleform global-heap/global-delete tail (flags in dil, this in rbx)."""
    from iced_x86 import Code, Register
    if len(tail) != 21:
        return None
    if not (tail[0].code == Code.TEST_RM8_IMM8 and tail[0].op0_register == Register.DIL
            and tail[0].immediate8 == 1 and tail[0].len == 4
            and tail[1].code == Code.JE_REL8_64 and tail[1].near_branch_target == tail[16].ip
            and tail[2].code == Code.TEST_RM8_IMM8 and tail[2].op0_register == Register.DIL
            and tail[2].immediate8 == 4 and tail[2].len == 4
            and tail[3].code == Code.JNE_REL8_64 and tail[3].near_branch_target == tail[13].ip
            and _is_rip_mov64(tail[4], Register.RCX)
            and tail[5].code == Code.MOV_R64_RM64 and tail[5].op0_register == Register.RDX
            and tail[5].op1_register == Register.RBX and tail[5].len == 3
            and _is_mem_load64(tail[6], Register.RAX, Register.RCX, 0) and tail[6].len == 3
            and tail[7].code == Code.CALL_RM64 and tail[7].memory_base == Register.RAX
            and tail[7].memory_index == Register.NONE and tail[7].memory_displacement == 0x60
            and tail[7].len == 3
            and _match_epi_rbx_rdi(tail[8:13])
            and tail[13].code == Code.MOV_R32_IMM32 and tail[13].op0_register == Register.EDX
            and tail[13].len == 5 and tail[13].immediate32 > 0
            and tail[14].code == Code.MOV_R64_RM64 and tail[14].op0_register == Register.RCX
            and tail[14].op1_register == Register.RBX and tail[14].len == 3
            and tail[15].code == Code.CALL_REL32_64 and tail[15].len == 5
            and _match_epi_rbx_rdi(tail[16:21])):
        return None
    return (tail[13].immediate32, tail[4].ip_rel_memory_address, tail[15].near_branch_target)


def _match_prolog_rbx_rdi(insns):
    """Match `mov [rsp+8], rbx; push rdi; sub rsp, 20h` (3 insns)."""
    from iced_x86 import Code, Register
    return (len(insns) >= 3
            and _is_mem_store64(insns[0], Register.RSP, Register.RBX, 8) and insns[0].len == 5
            and insns[1].code == Code.PUSH_R64 and insns[1].op0_register == Register.RDI and insns[1].len == 1
            and insns[2].code == Code.SUB_RM64_IMM8 and insns[2].op0_register == Register.RSP
            and insns[2].immediate8 == 0x20 and insns[2].len == 4)


def _match_prolog_push_rbx(insns):
    """Match `push rbx; sub rsp, 20h; lea rax, [rip+tbl]; mov rbx, rcx; mov [rcx], rax` (5 insns)."""
    from iced_x86 import Code, Register
    if len(insns) < 5:
        return None
    if not (insns[0].code == Code.PUSH_R64 and insns[0].op0_register == Register.RBX and insns[0].len == 2
            and insns[1].code == Code.SUB_RM64_IMM8 and insns[1].op0_register == Register.RSP
            and insns[1].immediate8 == 0x20 and insns[1].len == 4
            and _is_rip_lea(insns[2], Register.RAX)
            and insns[3].code == Code.MOV_R64_RM64 and insns[3].op0_register == Register.RBX
            and insns[3].op1_register == Register.RCX and insns[3].len == 3
            and _is_mem_store64(insns[4], Register.RCX, Register.RAX, 0) and insns[4].len == 3):
        return None
    return insns[2].ip_rel_memory_address


def _classify_push_rbx_variants(insns, rva, size):
    """Classify 1-reg-prolog (push rbx) table-reset deleting destructors (3 families)."""
    from iced_x86 import Code, Register
    table = _match_prolog_push_rbx(insns)
    if table is None:
        return None
    tail = insns[5:]

    # 1. HeapTableDeallocators (size=73, 23 insns total, tail=18 insns)
    if (len(tail) == 18
            and tail[0].code == Code.TEST_RM8_IMM8 and tail[0].op0_register == Register.DL
            and tail[0].immediate8 == 1 and tail[0].len == 3
            and tail[1].code == Code.JE_REL8_64 and tail[1].near_branch_target == tail[14].ip
            and tail[2].code == Code.TEST_RM8_IMM8 and tail[2].op0_register == Register.DL
            and tail[2].immediate8 == 4 and tail[2].len == 3
            and tail[3].code == Code.JNE_REL8_64 and tail[3].near_branch_target == tail[12].ip
            and _is_rip_mov64(tail[4], Register.RCX)
            and tail[5].code == Code.MOV_R64_RM64 and tail[5].op0_register == Register.RDX
            and tail[5].op1_register == Register.RBX and tail[5].len == 3
            and _is_mem_load64(tail[6], Register.RAX, Register.RCX, 0) and tail[6].len == 3
            and tail[7].code == Code.CALL_RM64 and tail[7].memory_base == Register.RAX
            and tail[7].memory_index == Register.NONE and tail[7].memory_displacement == 0x60
            and tail[7].len == 3
            and _match_epi_rbx(tail[8:12])
            and tail[12].code == Code.MOV_R32_IMM32 and tail[12].op0_register == Register.EDX
            and tail[12].len == 5 and tail[12].immediate32 > 0
            and tail[13].code == Code.CALL_REL32_64 and tail[13].len == 5
            and _match_epi_rbx(tail[14:18])):
        return Member(rva, size, HEAP_TABLE, tail[12].immediate32, tail[13].near_branch_target,
                      global_heap=tail[4].ip_rel_memory_address, tables=(table,), table_offsets=(0,))

    # 2. RouterFixedTableDeallocators (size=88, 26 insns total, tail=21 insns)
    if (len(tail) == 21
            and tail[0].code == Code.TEST_RM8_IMM8 and tail[0].op0_register == Register.DL
            and tail[0].immediate8 == 1 and tail[0].len == 3
            and tail[1].code == Code.JE_REL8_64 and tail[1].near_branch_target == tail[17].ip
            and tail[2].code == Code.TEST_RM8_IMM8 and tail[2].op0_register == Register.DL
            and tail[2].immediate8 == 4 and tail[2].len == 3
            and tail[3].code == Code.JNE_REL8_64 and tail[3].near_branch_target == tail[15].ip
            and _is_rip_mov32(tail[4], Register.ECX)
            and _is_rip_call64(tail[5])
            and tail[6].code == Code.MOV_R32_IMM32 and tail[6].op0_register == Register.R8D
            and tail[6].len == 6 and 0 < tail[6].immediate32 < 0x80000000
            and tail[7].code == Code.MOV_R64_RM64 and tail[7].op0_register == Register.RDX
            and tail[7].op1_register == Register.RBX and tail[7].len == 3
            and _is_mem_load64(tail[8], Register.RCX, Register.RAX, 0x58) and tail[8].len == 4
            and _is_mem_load64(tail[9], Register.RAX, Register.RCX, 0) and tail[9].len == 3
            and tail[10].code == Code.CALL_RM64 and tail[10].memory_base == Register.RAX
            and tail[10].memory_index == Register.NONE and tail[10].memory_displacement == 0x10
            and tail[10].len == 3
            and _match_epi_rbx(tail[11:15])
            and tail[15].code == Code.MOV_R32_IMM32 and tail[15].op0_register == Register.EDX
            and tail[15].len == 5 and tail[15].immediate32 == tail[6].immediate32
            and tail[16].code == Code.CALL_REL32_64 and tail[16].len == 5
            and _match_epi_rbx(tail[17:21])):
        return Member(rva, size, ROUTER_FIXED_TABLE, tail[6].immediate32, tail[16].near_branch_target,
                      tls_slot=tail[4].ip_rel_memory_address, tls_getter=tail[5].ip_rel_memory_address,
                      tables=(table,), table_offsets=(0,))

    # 3. RouterTableDeallocators (size=124, 36 insns total, tail=31 insns)
    if (len(tail) == 31
            and tail[0].code == Code.TEST_RM8_IMM8 and tail[0].op0_register == Register.DL
            and tail[0].immediate8 == 1 and tail[0].len == 3
            and tail[1].code == Code.JE_REL8_64 and tail[1].near_branch_target == tail[27].ip
            and _is_mem_store64(tail[2], Register.RSP, Register.RDI, 0x30) and tail[2].len == 5
            and tail[3].code == Code.TEST_RM8_IMM8 and tail[3].op0_register == Register.DL
            and tail[3].immediate8 == 4 and tail[3].len == 3
            and tail[4].code == Code.JNE_REL8_64 and tail[4].near_branch_target == tail[24].ip
            and tail[5].code == Code.MOVZX_R32_RM16 and tail[5].op0_register == Register.EAX
            and tail[5].memory_base == Register.RCX and tail[5].memory_index == Register.NONE
            and tail[5].memory_displacement == 8 and tail[5].len == 4
            and tail[6].code == Code.MOV_R32_IMM32 and tail[6].op0_register == Register.ECX
            and tail[6].immediate32 == 0xffff and tail[6].len == 5
            and tail[7].code == Code.CMP_R16_RM16 and tail[7].op0_register == Register.AX
            and tail[7].op1_register == Register.CX and tail[7].len == 3
            and tail[8].code == Code.JNE_REL8_64 and tail[8].near_branch_target == tail[11].ip
            and tail[9].code == Code.MOV_R32_IMM32 and tail[9].op0_register == Register.EDI
            and tail[9].len == 5 and 0 < tail[9].immediate32 < 0x80000000
            and tail[10].code == Code.JMP_REL8_64 and tail[10].near_branch_target == tail[12].ip
            and tail[11].code == Code.MOVZX_R32_RM16 and tail[11].op0_register == Register.EDI
            and tail[11].op1_register == Register.AX and tail[11].len == 3
            and _is_rip_mov32(tail[12], Register.ECX)
            and _is_rip_call64(tail[13])
            and tail[14].code == Code.MOV_R32_RM32 and tail[14].op0_register == Register.R8D
            and tail[14].op1_register == Register.EDI and tail[14].len == 3
            and tail[15].code == Code.MOV_R64_RM64 and tail[15].op0_register == Register.RDX
            and tail[15].op1_register == Register.RBX and tail[15].len == 3
            and _is_mem_load64(tail[16], Register.RCX, Register.RAX, 0x58) and tail[16].len == 4
            and _is_mem_load64(tail[17], Register.RAX, Register.RCX, 0) and tail[17].len == 3
            and tail[18].code == Code.CALL_RM64 and tail[18].memory_base == Register.RAX
            and tail[18].memory_index == Register.NONE and tail[18].memory_displacement == 0x10
            and tail[18].len == 3
            and _is_mem_load64(tail[19], Register.RDI, Register.RSP, 0x30) and tail[19].len == 5
            and _match_epi_rbx(tail[20:24])
            and tail[24].code == Code.MOV_R32_IMM32 and tail[24].op0_register == Register.EDX
            and tail[24].len == 5 and tail[24].immediate32 == tail[9].immediate32
            and tail[25].code == Code.CALL_REL32_64 and tail[25].len == 5
            and _is_mem_load64(tail[26], Register.RDI, Register.RSP, 0x30) and tail[26].len == 5
            and _match_epi_rbx(tail[27:31])):
        return Member(rva, size, ROUTER_TABLE, tail[9].immediate32, tail[25].near_branch_target,
                      tls_slot=tail[12].ip_rel_memory_address, tls_getter=tail[13].ip_rel_memory_address,
                      tables=(table,), table_offsets=(0,))
    return None


def _classify_router_dil_prefix(head, rva, size, obj_size, tls_slot, tls_getter, global_dealloc):
    """Classify teardown prefixes preceding the 31-insn Havok size-tagged TLS-router tail."""
    from iced_x86 import Code, Register

    # 1. RouterCleanupDeallocators: mov edi, edx; mov rbx, rcx; call cleanup (3 insns)
    if (len(head) == 3
            and head[0].code == Code.MOV_R32_RM32 and head[0].op0_register == Register.EDI
            and head[0].op1_register == Register.EDX and head[0].len == 2
            and head[1].code == Code.MOV_R64_RM64 and head[1].op0_register == Register.RBX
            and head[1].op1_register == Register.RCX and head[1].len == 3
            and head[2].code == Code.CALL_REL32_64 and head[2].len == 5):
        return Member(rva, size, ROUTER_CLEANUP, obj_size, global_dealloc,
                      tls_slot=tls_slot, tls_getter=tls_getter,
                      cleanup=head[2].near_branch_target)

    # 2. RouterMemberCleanupDeallocators (6 insns):
    #    mov rbx, rcx; mov edi, edx; add rcx, off; call member_cleanup; mov rcx, rbx; call base_cleanup
    if (len(head) == 6
            and head[0].code == Code.MOV_R64_RM64 and head[0].op0_register == Register.RBX
            and head[0].op1_register == Register.RCX and head[0].len == 3
            and head[1].code == Code.MOV_R32_RM32 and head[1].op0_register == Register.EDI
            and head[1].op1_register == Register.EDX and head[1].len == 2
            and head[3].code == Code.CALL_REL32_64 and head[3].len == 5
            and head[4].code == Code.MOV_R64_RM64 and head[4].op0_register == Register.RCX
            and head[4].op1_register == Register.RBX and head[4].len == 3
            and head[5].code == Code.CALL_REL32_64 and head[5].len == 5):
        off = _is_add_imm(head[2], Register.RCX)
        if off is not None and off >= 0x10 and off % 8 == 0:
            return Member(rva, size, ROUTER_MEMBER_CLEANUP, obj_size, global_dealloc,
                          tls_slot=tls_slot, tls_getter=tls_getter,
                          cleanup=head[5].near_branch_target,
                          member_cleanup=head[3].near_branch_target,
                          member_offset=off)

    # 3. RouterMemberTableDeallocators (6 insns):
    #    mov rbx, rcx; mov edi, edx; add rcx, off; call member_cleanup; lea rax, [tbl]; mov [rbx], rax
    if (len(head) == 6
            and head[0].code == Code.MOV_R64_RM64 and head[0].op0_register == Register.RBX
            and head[0].op1_register == Register.RCX and head[0].len == 3
            and head[1].code == Code.MOV_R32_RM32 and head[1].op0_register == Register.EDI
            and head[1].op1_register == Register.EDX and head[1].len == 2
            and head[3].code == Code.CALL_REL32_64 and head[3].len == 5
            and _is_rip_lea(head[4], Register.RAX)
            and _is_mem_store64(head[5], Register.RBX, Register.RAX, 0) and head[5].len == 3):
        off = _is_add_imm(head[2], Register.RCX)
        if off is not None and off >= 0x10 and off % 8 == 0:
            return Member(rva, size, ROUTER_MEMBER_TABLE, obj_size, global_dealloc,
                          tls_slot=tls_slot, tls_getter=tls_getter,
                          member_cleanup=head[3].near_branch_target,
                          tables=(head[4].ip_rel_memory_address,),
                          table_offsets=(0,),
                          member_offset=off)

    # 4. RouterRefMemberDeallocators (11 insns):
    #    mov rbx, rcx; mov edi, edx; mov rcx, [rcx+ref]; test rcx, rcx; je +7; call release;
    #    lea rcx, [rbx+mem]; mov qword [rbx+ref], 0; call member_cleanup; mov rcx, rbx; call base_cleanup
    if (len(head) == 11
            and head[0].code == Code.MOV_R64_RM64 and head[0].op0_register == Register.RBX
            and head[0].op1_register == Register.RCX and head[0].len == 3
            and head[1].code == Code.MOV_R32_RM32 and head[1].op0_register == Register.EDI
            and head[1].op1_register == Register.EDX and head[1].len == 2
            and _is_mem_load64(head[2], Register.RCX, Register.RCX)
            and head[3].code == Code.TEST_RM64_R64 and head[3].op0_register == Register.RCX
            and head[3].op1_register == Register.RCX and head[3].len == 3
            and head[4].code == Code.JE_REL8_64 and head[4].near_branch_target == head[6].ip
            and head[5].code == Code.CALL_REL32_64 and head[5].len == 5
            and head[7].code == Code.MOV_RM64_IMM32 and head[7].memory_base == Register.RBX
            and head[7].memory_index == Register.NONE and head[7].immediate32to64 == 0
            and head[8].code == Code.CALL_REL32_64 and head[8].len == 5
            and head[9].code == Code.MOV_R64_RM64 and head[9].op0_register == Register.RCX
            and head[9].op1_register == Register.RBX and head[9].len == 3
            and head[10].code == Code.CALL_REL32_64 and head[10].len == 5):
        ref_off = head[2].memory_displacement
        mem_off = _is_lea_disp(head[6], Register.RCX, Register.RBX)
        if (mem_off is not None and head[7].memory_displacement == ref_off
                and ref_off >= 0x10 and ref_off % 8 == 0
                and mem_off >= 0x10 and mem_off % 8 == 0
                and (mem_off < ref_off or ref_off + 8 <= mem_off)):
            return Member(rva, size, ROUTER_REF_MEMBER, obj_size, global_dealloc,
                          tls_slot=tls_slot, tls_getter=tls_getter,
                          cleanup=head[10].near_branch_target,
                          member_cleanup=head[8].near_branch_target,
                          release_callee=head[5].near_branch_target,
                          member_offset=mem_off, ref_offset=ref_off)
    return None


def _classify_heap_dil_prefix(head, rva, size, obj_size, global_heap, global_dealloc):
    """Classify teardown prefixes preceding the 21-insn Scaleform global-heap tail."""
    from iced_x86 import Code, Register

    # 1. HeapCleanupDeallocators (3 insns): mov edi, edx; mov rbx, rcx; call cleanup
    if (len(head) == 3
            and head[0].code == Code.MOV_R32_RM32 and head[0].op0_register == Register.EDI
            and head[0].op1_register == Register.EDX and head[0].len == 2
            and head[1].code == Code.MOV_R64_RM64 and head[1].op0_register == Register.RBX
            and head[1].op1_register == Register.RCX and head[1].len == 3
            and head[2].code == Code.CALL_REL32_64 and head[2].len == 5):
        return Member(rva, size, HEAP_CLEANUP, obj_size, global_dealloc,
                      global_heap=global_heap, cleanup=head[2].near_branch_target)

    # 2. HeapTableCleanupDeallocators (5 insns):
    #    lea rax, [tbl]; mov edi, edx; mov [rcx], rax; mov rbx, rcx; call cleanup
    if (len(head) == 5
            and _is_rip_lea(head[0], Register.RAX)
            and head[1].code == Code.MOV_R32_RM32 and head[1].op0_register == Register.EDI
            and head[1].op1_register == Register.EDX and head[1].len == 2
            and _is_mem_store64(head[2], Register.RCX, Register.RAX, 0) and head[2].len == 3
            and head[3].code == Code.MOV_R64_RM64 and head[3].op0_register == Register.RBX
            and head[3].op1_register == Register.RCX and head[3].len == 3
            and head[4].code == Code.CALL_REL32_64 and head[4].len == 5):
        return Member(rva, size, HEAP_TABLE_CLEANUP, obj_size, global_dealloc,
                      global_heap=global_heap, cleanup=head[4].near_branch_target,
                      tables=(head[0].ip_rel_memory_address,), table_offsets=(0,))

    # 3. HeapDualTableDeallocators (7 insns):
    #    lea rax, [t0]; mov edi, edx; mov [rcx], rax; mov rbx, rcx; lea rax, [t1]; mov [rcx+off1], rax; call cleanup
    if (len(head) == 7
            and _is_rip_lea(head[0], Register.RAX)
            and head[1].code == Code.MOV_R32_RM32 and head[1].op0_register == Register.EDI
            and head[1].op1_register == Register.EDX and head[1].len == 2
            and _is_mem_store64(head[2], Register.RCX, Register.RAX, 0) and head[2].len == 3
            and head[3].code == Code.MOV_R64_RM64 and head[3].op0_register == Register.RBX
            and head[3].op1_register == Register.RCX and head[3].len == 3
            and _is_rip_lea(head[4], Register.RAX)
            and _is_mem_store64(head[5], Register.RCX, Register.RAX)
            and head[6].code == Code.CALL_REL32_64 and head[6].len == 5):
        off1 = head[5].memory_displacement
        if off1 >= 8 and off1 % 8 == 0:
            return Member(rva, size, HEAP_DUAL_TABLE, obj_size, global_dealloc,
                          global_heap=global_heap, cleanup=head[6].near_branch_target,
                          tables=(head[0].ip_rel_memory_address, head[4].ip_rel_memory_address),
                          table_offsets=(0, off1))

    # 4. HeapTripleTableDeallocators (12 insns):
    #    lea rax, [t0]; mov rbx, rcx; mov [rcx], rax; mov edi, edx; lea rax, [t1]; mov [rcx+off1], rax;
    #    add rcx, off2; lea rax, [t2]; mov [rcx], rax; call sub_cleanup; mov rcx, rbx; call base_cleanup
    if (len(head) == 12
            and _is_rip_lea(head[0], Register.RAX)
            and head[1].code == Code.MOV_R64_RM64 and head[1].op0_register == Register.RBX
            and head[1].op1_register == Register.RCX and head[1].len == 3
            and _is_mem_store64(head[2], Register.RCX, Register.RAX, 0) and head[2].len == 3
            and head[3].code == Code.MOV_R32_RM32 and head[3].op0_register == Register.EDI
            and head[3].op1_register == Register.EDX and head[3].len == 2
            and _is_rip_lea(head[4], Register.RAX)
            and _is_mem_store64(head[5], Register.RCX, Register.RAX)
            and _is_rip_lea(head[7], Register.RAX)
            and _is_mem_store64(head[8], Register.RCX, Register.RAX, 0) and head[8].len == 3
            and head[9].code == Code.CALL_REL32_64 and head[9].len == 5
            and head[10].code == Code.MOV_R64_RM64 and head[10].op0_register == Register.RCX
            and head[10].op1_register == Register.RBX and head[10].len == 3
            and head[11].code == Code.CALL_REL32_64 and head[11].len == 5):
        off1 = head[5].memory_displacement
        off2 = _is_add_imm(head[6], Register.RCX)
        if off1 >= 8 and off1 % 8 == 0 and off2 is not None and off2 >= off1 + 8 and off2 % 8 == 0:
            return Member(rva, size, HEAP_TRIPLE_TABLE, obj_size, global_dealloc,
                          global_heap=global_heap,
                          cleanup=head[11].near_branch_target,
                          member_cleanup=head[9].near_branch_target,
                          tables=(head[0].ip_rel_memory_address, head[4].ip_rel_memory_address,
                                  head[7].ip_rel_memory_address),
                          table_offsets=(0, off1, off2))

    # 5. HeapFiveTableDeallocators (16 insns):
    #    same 0..9 as Triple, then:
    #    lea rax, [t3]; mov rcx, rbx; mov [rbx], rax; lea rax, [t4]; mov [rbx+off1], rax; call base_cleanup
    if (len(head) == 16
            and _is_rip_lea(head[0], Register.RAX)
            and head[1].code == Code.MOV_R64_RM64 and head[1].op0_register == Register.RBX
            and head[1].op1_register == Register.RCX and head[1].len == 3
            and _is_mem_store64(head[2], Register.RCX, Register.RAX, 0) and head[2].len == 3
            and head[3].code == Code.MOV_R32_RM32 and head[3].op0_register == Register.EDI
            and head[3].op1_register == Register.EDX and head[3].len == 2
            and _is_rip_lea(head[4], Register.RAX)
            and _is_mem_store64(head[5], Register.RCX, Register.RAX)
            and _is_rip_lea(head[7], Register.RAX)
            and _is_mem_store64(head[8], Register.RCX, Register.RAX, 0) and head[8].len == 3
            and head[9].code == Code.CALL_REL32_64 and head[9].len == 5
            and _is_rip_lea(head[10], Register.RAX)
            and head[11].code == Code.MOV_R64_RM64 and head[11].op0_register == Register.RCX
            and head[11].op1_register == Register.RBX and head[11].len == 3
            and _is_mem_store64(head[12], Register.RBX, Register.RAX, 0) and head[12].len == 3
            and _is_rip_lea(head[13], Register.RAX)
            and _is_mem_store64(head[14], Register.RBX, Register.RAX)
            and head[15].code == Code.CALL_REL32_64 and head[15].len == 5):
        off1 = head[5].memory_displacement
        off2 = _is_add_imm(head[6], Register.RCX)
        if (off1 >= 8 and off1 % 8 == 0 and head[14].memory_displacement == off1
                and off2 is not None and off2 >= off1 + 8 and off2 % 8 == 0):
            return Member(rva, size, HEAP_FIVE_TABLE, obj_size, global_dealloc,
                          global_heap=global_heap,
                          cleanup=head[15].near_branch_target,
                          member_cleanup=head[9].near_branch_target,
                          tables=(head[0].ip_rel_memory_address, head[4].ip_rel_memory_address,
                                  head[7].ip_rel_memory_address, head[10].ip_rel_memory_address,
                                  head[13].ip_rel_memory_address),
                          table_offsets=(0, off1, off2))
    return None


def classify(code, rva):
    from iced_x86 import Decoder

    insns = list(Decoder(64, code, ip=rva))
    if not insns or any(i.is_invalid for i in insns):
        return None
    size = len(code)

    # 1-register prolog (`push rbx; sub rsp, 20h; ...`)
    direct = _classify_push_rbx_variants(insns, rva, size)
    if direct is not None:
        return direct

    # 2-register prolog (`mov [rsp+8], rbx; push rdi; sub rsp, 20h; ...`)
    if not _match_prolog_rbx_rdi(insns):
        return None
    body = insns[3:]

    if len(body) >= 34:
        router = _match_router_tail_dil_exact(body[-31:])
        if router is not None:
            return _classify_router_dil_prefix(body[:-31], rva, size, *router)

    if len(body) >= 24:
        heap = _match_heap_tail_dil(body[-21:])
        if heap is not None:
            return _classify_heap_dil_prefix(body[:-21], rva, size, *heap)

    return None


def _is_rdata_address(image, rva, align=1):
    try:
        sec = image.section_for(rva)
        return (sec.name == '.rdata'
                and not (sec.flags & SCN_MEM_EXECUTE)
                and not (sec.flags & SCN_MEM_WRITE)
                and rva + align <= sec.vaddr + sec.vsize
                and rva % align == 0)
    except Reject:
        return False


def _is_writable_data_address(image, rva, width):
    try:
        sec = image.section_for(rva)
        return (sec.name == '.data'
                and not (sec.flags & SCN_MEM_EXECUTE)
                and bool(sec.flags & SCN_MEM_WRITE)
                and rva + width <= sec.vaddr + sec.vsize
                and rva % width == 0)
    except Reject:
        return False


def _indexed_target(image, member, target, starts):
    return leaf_family_batch.indexed_callee(
        image, SimpleNamespace(rva=member.rva, size=member.size, callee=target), starts)


def _has_eh_handler(image, pdata, rva):
    entry = pdata.get(rva)
    if entry is None:
        return False
    try:
        _, hdr = image.read(entry[1], 4, 'unwind header')
        return bool((hdr[0] >> 3) & 3)
    except Reject:
        return True


def _validate_member_targets(image, member, starts, pdata):
    if _has_eh_handler(image, pdata, member.rva):
        return False
    if not _indexed_target(image, member, member.global_dealloc, starts):
        return False
    for callee in (member.cleanup, member.member_cleanup, member.release_callee):
        if callee is not None and not _indexed_target(image, member, callee, starts):
            return False
    if member.tls_slot is not None:
        if not _is_writable_data_address(image, member.tls_slot, 4):
            return False
        if member.tls_getter is None or not _is_rdata_address(image, member.tls_getter, 8):
            return False
    if member.global_heap is not None:
        if not _is_writable_data_address(image, member.global_heap, 8):
            return False
    for table in member.tables:
        if not _is_rdata_address(image, table, 1):
            return False
    return True


def discover(image, extents, inventory):
    pdata = {begin: (end, unwind) for begin, end, unwind in image.runtime_functions()}
    starts = set(extents) | set(pdata)
    raw = [m for m in leaf_family_batch.candidates(image, extents, inventory, CANDIDATE_SIZES, classify)
           if _validate_member_targets(image, m, starts, pdata)]

    # Keep each base family free of member-to-member references and conflicting
    # external symbol declarations, then shard to stay under per-PR caps.
    result = []
    for base in BASE_FAMILIES:
        rows = [m for m in raw if m.family == base]
        member_rvas = {m.rva for m in rows}
        deallocs = {m.global_dealloc for m in rows}
        clean = []
        for m in rows:
            if m.global_dealloc in member_rvas:
                continue
            void_callees = [c for c in (m.cleanup, m.member_cleanup, m.release_callee) if c is not None]
            if any(c in member_rvas or c in deallocs for c in void_callees):
                continue
            # Also ensure tls_getter never collides with any table address in the same family
            if m.tls_getter is not None and m.tls_getter in m.tables:
                continue
            clean.append(m)
        if len(clean) <= SHARD_SIZE:
            result.extend(clean)
        else:
            for index in range(0, len(clean), SHARD_SIZE):
                shard = f'{base}{index // SHARD_SIZE + 1}'
                result.extend(replace(m, family=shard) for m in clean[index:index + SHARD_SIZE])
    return result


def _emit_layout_structs(family, base, members):
    lines = []
    if base in (ROUTER_CLEANUP, ROUTER_TABLE):
        lines.extend([
            f'struct {family}TaggedObject',
            '{',
            '    void* table;',
            '    unsigned short memSizeAndFlags;',
            '};',
            '',
        ])
    elif base in (ROUTER_FIXED_TABLE, HEAP_TABLE, HEAP_TABLE_CLEANUP):
        lines.extend([
            f'struct {family}TableObject',
            '{',
            '    void* table;',
            '};',
            '',
        ])
    elif base in (ROUTER_MEMBER_CLEANUP, ROUTER_MEMBER_TABLE):
        for off in sorted({m.member_offset for m in members}):
            lines.extend([
                f'struct {family}MemberObject{off:x}',
                '{',
                '    void* table;',
                '    unsigned short memSizeAndFlags;',
                f'    unsigned char unk0a[0x{off - 10:x}];',
                f'    unsigned char member{off:x}[1];',
                '};',
                '',
            ])
    elif base == ROUTER_REF_MEMBER:
        for mem_off, ref_off in sorted({(m.member_offset, m.ref_offset) for m in members}):
            lines.extend([
                f'struct {family}RefMemberObject{mem_off:x}_{ref_off:x}',
                '{',
                '    void* table;',
                '    unsigned short memSizeAndFlags;',
            ])
            if mem_off < ref_off:
                lines.append(f'    unsigned char unk0a[0x{mem_off - 10:x}];')
                lines.append(f'    unsigned char member{mem_off:x}[0x{ref_off - mem_off:x}];')
                lines.append('    void* refObj;')
            else:
                lines.append(f'    unsigned char unk0a[0x{ref_off - 10:x}];')
                lines.append('    void* refObj;')
                if mem_off > ref_off + 8:
                    lines.append(f'    unsigned char unk{ref_off + 8:x}[0x{mem_off - ref_off - 8:x}];')
                lines.append(f'    unsigned char member{mem_off:x}[1];')
            lines.extend(['};', ''])
    elif base == HEAP_DUAL_TABLE:
        for off1 in sorted({m.table_offsets[1] for m in members}):
            lines.extend([
                f'struct {family}DualTableObject{off1:x}',
                '{',
                '    void* table0;',
            ])
            if off1 > 8:
                lines.append(f'    unsigned char unk08[0x{off1 - 8:x}];')
            lines.extend(['    void* table1;', '};', ''])
    elif base in (HEAP_TRIPLE_TABLE, HEAP_FIVE_TABLE):
        for off1, off2 in sorted({(m.table_offsets[1], m.table_offsets[2]) for m in members}):
            lines.extend([
                f'struct {family}TripleTableObject{off1:x}_{off2:x}',
                '{',
                '    void* table0;',
            ])
            if off1 > 8:
                lines.append(f'    unsigned char unk08[0x{off1 - 8:x}];')
            lines.append('    void* table1;')
            if off2 > off1 + 8:
                lines.append(f'    unsigned char unk{off1 + 8:x}[0x{off2 - off1 - 8:x}];')
            lines.extend(['    void* table2;', '};', ''])
    return lines


def _emit_allocator_types(family, is_router):
    if is_router:
        return [
            f'struct {family}BlockHeap',
            '{',
            '    virtual void Slot00();',
            '    virtual void Slot01();',
            '    virtual void BlockFree(void* block, int size);',
            '};',
            '',
            f'struct {family}MemoryRouter',
            '{',
            '    unsigned char unk00[0x58];',
            f'    {family}BlockHeap* heap;',
            '};',
            '',
        ]
    return [
        f'struct {family}GlobalHeap',
        '{',
        '    virtual void Slot00();',
        '    virtual void Slot01();',
        '    virtual void Slot02();',
        '    virtual void Slot03();',
        '    virtual void Slot04();',
        '    virtual void Slot05();',
        '    virtual void Slot06();',
        '    virtual void Slot07();',
        '    virtual void Slot08();',
        '    virtual void Slot09();',
        '    virtual void Slot0a();',
        '    virtual void Slot0b();',
        '    virtual void Free(void* block);',
        '};',
        '',
    ]


def emit(root, family, members, build_id, label):
    base = members[0].base_family
    is_router = members[0].tls_slot is not None
    prefix = [
        '// Source exposure: mixed (pinned image and community function boundaries).',
        f'// Boundary source: {label}',
        '// Code origin: original custom-allocator deleting-destructor template.',
        f'// {family}, types, methods and referenced symbols: GUESS(low) STANDIN; original ownership and layouts unknown.',
        '// Adapted bodies: none',
    ]
    header = prefix + ['#pragma once', '']
    header.extend(_emit_allocator_types(family, is_router))
    header.extend(_emit_layout_structs(family, base, members))

    symbols = {}
    if is_router:
        for slot in sorted({m.tls_slot for m in members}):
            name = f'RouterTlsSlot{slot:x}'
            header.append(f'extern "C" unsigned int {name};')
            symbols[name] = dict(rva=slot, size=None)
        for getter in sorted({m.tls_getter for m in members}):
            name = f'TlsGetValueSlot{getter:x}'
            header.append(f'extern "C" void* (*const {name})(unsigned int slot);')
            symbols[name] = dict(rva=getter, size=None)
    else:
        for heap in sorted({m.global_heap for m in members}):
            name = f'GlobalHeapSlot{heap:x}'
            header.append(f'extern "C" {family}GlobalHeap* {name};')
            symbols[name] = dict(rva=heap, size=None)

    for dealloc in sorted({m.global_dealloc for m in members}):
        name = f'GlobalDeallocTarget{dealloc:x}'
        header.append(f'extern "C" void {name}(void* object, unsigned long long size);')
        symbols[name] = dict(rva=dealloc, size=None)

    void_callees = sorted({c for m in members
                           for c in (m.cleanup, m.member_cleanup, m.release_callee)
                           if c is not None})
    for callee in void_callees:
        name = f'CleanupTarget{callee:x}'
        header.append(f'extern "C" void {name}(void* object);')
        symbols[name] = dict(rva=callee, size=None)

    for table in sorted({t for m in members for t in m.tables}):
        name = f'TableTarget{table:x}'
        header.append(f'extern "C" unsigned char {name}[];')
        symbols[name] = dict(rva=table, size=None)

    header.extend(['', f'struct {family}', '{'])
    source = prefix + [f'// 0x{m.rva:x} {family}::{m.name}' for m in members] + [f'#include "{family}.h"']
    functions = []

    for m in members:
        ptype = 'void*' if m.param_struct is None else f'{m.param_struct}*'
        header.append(f'    static void* {m.name}({ptype} object, unsigned int flags);')
        body = ['', f'void* {family}::{m.name}({ptype} object, unsigned int flags)', '{']

        if base == ROUTER_CLEANUP or base == HEAP_CLEANUP:
            body.append(f'    CleanupTarget{m.cleanup:x}(object);')
        elif base in (ROUTER_TABLE, ROUTER_FIXED_TABLE, HEAP_TABLE):
            body.append(f'    object->table = TableTarget{m.tables[0]:x};')
        elif base == ROUTER_MEMBER_CLEANUP:
            body.append(f'    CleanupTarget{m.member_cleanup:x}(object->member{m.member_offset:x});')
            body.append(f'    CleanupTarget{m.cleanup:x}(object);')
        elif base == ROUTER_MEMBER_TABLE:
            body.append(f'    CleanupTarget{m.member_cleanup:x}(object->member{m.member_offset:x});')
            body.append(f'    object->table = TableTarget{m.tables[0]:x};')
        elif base == ROUTER_REF_MEMBER:
            body.extend([
                '    if (object->refObj != nullptr)',
                '    {',
                f'        CleanupTarget{m.release_callee:x}(object->refObj);',
                '    }',
                '    object->refObj = nullptr;',
                f'    CleanupTarget{m.member_cleanup:x}(object->member{m.member_offset:x});',
                f'    CleanupTarget{m.cleanup:x}(object);',
            ])
        elif base == HEAP_TABLE_CLEANUP:
            body.append(f'    object->table = TableTarget{m.tables[0]:x};')
            body.append(f'    CleanupTarget{m.cleanup:x}(object);')
        elif base == HEAP_DUAL_TABLE:
            body.append(f'    object->table0 = TableTarget{m.tables[0]:x};')
            body.append(f'    object->table1 = TableTarget{m.tables[1]:x};')
            body.append(f'    CleanupTarget{m.cleanup:x}(object);')
        elif base == HEAP_TRIPLE_TABLE:
            body.append(f'    object->table0 = TableTarget{m.tables[0]:x};')
            body.append(f'    object->table1 = TableTarget{m.tables[1]:x};')
            body.append(f'    object->table2 = TableTarget{m.tables[2]:x};')
            body.append(f'    CleanupTarget{m.member_cleanup:x}(&object->table2);')
            body.append(f'    CleanupTarget{m.cleanup:x}(object);')
        elif base == HEAP_FIVE_TABLE:
            body.append(f'    object->table0 = TableTarget{m.tables[0]:x};')
            body.append(f'    object->table1 = TableTarget{m.tables[1]:x};')
            body.append(f'    object->table2 = TableTarget{m.tables[2]:x};')
            body.append(f'    CleanupTarget{m.member_cleanup:x}(&object->table2);')
            body.append(f'    object->table0 = TableTarget{m.tables[3]:x};')
            body.append(f'    object->table1 = TableTarget{m.tables[4]:x};')
            body.append(f'    CleanupTarget{m.cleanup:x}(object);')

        body.extend(['    if ((flags & 1u) != 0u)', '    {', '        if ((flags & 4u) == 0u)', '        {'])
        if is_router:
            if base == ROUTER_FIXED_TABLE:
                body.extend([
                    f'            {family}MemoryRouter* router = static_cast<{family}MemoryRouter*>(TlsGetValueSlot{m.tls_getter:x}(RouterTlsSlot{m.tls_slot:x}));',
                    f'            router->heap->BlockFree(object, {m.object_size});',
                ])
            else:
                body.extend([
                    '            unsigned short tagged = object->memSizeAndFlags;',
                    f'            int allocSize = (tagged == 0xffffu) ? {m.object_size} : tagged;',
                    f'            {family}MemoryRouter* router = static_cast<{family}MemoryRouter*>(TlsGetValueSlot{m.tls_getter:x}(RouterTlsSlot{m.tls_slot:x}));',
                    '            router->heap->BlockFree(object, allocSize);',
                ])
        else:
            body.append(f'            GlobalHeapSlot{m.global_heap:x}->Free(object);')

        body.extend([
            '        }',
            '        else',
            '        {',
            f'            GlobalDeallocTarget{m.global_dealloc:x}(object, {m.object_size}ull);',
            '        }',
            '    }',
            '    return object;',
            '}',
        ])
        source.extend(body)
        symbols[m.symbol] = dict(rva=m.rva, size=m.size)
        functions.append(dict(rva=m.rva, size=m.size, symbol=m.symbol))

    header.append('};')
    return leaf_family_batch.write_unit(root, family, build_id, header, source, symbols, functions)


if __name__ == '__main__':
    raise SystemExit(leaf_family_batch.run(__doc__, discover, emit))
