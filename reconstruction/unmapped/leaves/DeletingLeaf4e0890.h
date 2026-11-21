// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in from the pinned image listing; no external declaration or body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf4e0890, unknown08: GUESS(low) STANDIN
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf4e0890
{
public:
    DeletingLeaf4e0890();
    virtual ~DeletingLeaf4e0890();  // compared: 0x4e0890 (scalar deleting destructor)
    std::uint8_t unknown08[0x10];
};
static_assert(sizeof(DeletingLeaf4e0890) == 0x18, "size observed from the sized delete argument");
