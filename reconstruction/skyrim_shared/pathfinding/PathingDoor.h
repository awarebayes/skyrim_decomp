// Source exposure: mixed (local binary analysis and public names).
// Code origin: brown-room reconstruction from disassembly
// SPDX-License-Identifier: CC0-1.0
// PathingDoor: EXE_RTTI
// Slot2, Function4e0ee0, Function4e0f40: GUESS(low)
// member, padding: GUESS(low); storage names invented for the measured member offset
// PathingDoorVirtualTarget: GUESS(low) STANDIN
#pragma once
#include <cstdint>
class PathingDoorVirtualTarget;
class PathingDoor
{
public:
    virtual std::uint32_t Slot2() const;
    void Function4e0ee0(PathingDoorVirtualTarget* target);
    void Function4e0f40(PathingDoorVirtualTarget* target);
    std::uint8_t padding[0x8];
    std::uint32_t member;
};
