// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in from the pinned image listing; no external declaration or body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf5c9be0, unknown08: GUESS(low) STANDIN
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf5c9be0
{
public:
    DeletingLeaf5c9be0();
    virtual ~DeletingLeaf5c9be0();  // compared: 0x5c9be0 (scalar deleting destructor)
    std::uint8_t unknown08[0x10];
};
static_assert(sizeof(DeletingLeaf5c9be0) == 0x18, "size observed from the sized delete argument");
