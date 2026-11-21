// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in from the pinned image listing; no external declaration or body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf5ba8f0, unknown08: GUESS(low) STANDIN
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf5ba8f0
{
public:
    DeletingLeaf5ba8f0();
    virtual ~DeletingLeaf5ba8f0();  // compared: 0x5ba8f0 (scalar deleting destructor)
    std::uint8_t unknown08[0x10];
};
static_assert(sizeof(DeletingLeaf5ba8f0) == 0x18, "size observed from the sized delete argument");
