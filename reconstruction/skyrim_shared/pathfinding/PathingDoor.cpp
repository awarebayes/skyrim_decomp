// Source exposure: mixed (local binary analysis and public names).
// Code origin: brown-room reconstruction from disassembly
// SPDX-License-Identifier: CC0-1.0
// Adapted bodies: none
// PathingDoor: EXE_RTTI
// Slot2, Function4e0ee0, Function4e0f40: GUESS(low)
// member, padding: GUESS(low); storage names invented for the measured member offset
// PathingDoorVirtualTarget, Slot0..Slot11: GUESS(low) STANDIN; vtable slots inferred from call offsets
// 0x4e0ed0 PathingDoor::Slot2
// 0x4e0ee0 PathingDoor::Function4e0ee0
// 0x4e0f40 PathingDoor::Function4e0f40
#include "PathingDoor.h"

struct PathingDoorVirtualTarget
{
    virtual void Slot0();
    virtual void Slot1(std::uint32_t* value);
    virtual void Slot2();
    virtual void Slot3();
    virtual void Slot4();
    virtual void Slot5();
    virtual void Slot6();
    virtual void Slot7();
    virtual void Slot8();
    virtual void Slot9();
    virtual void Slot10();
    virtual void Slot11(std::uint32_t value);
};

std::uint32_t PathingDoor::Slot2() const
{
    return member;
}

void PathingDoor::Function4e0ee0(PathingDoorVirtualTarget* target)
{
    target->Slot11(member);
}

void PathingDoor::Function4e0f40(PathingDoorVirtualTarget* target)
{
    target->Slot1(&member);
}
