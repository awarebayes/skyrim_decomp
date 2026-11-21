// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; derived from the pinned image listing.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf17c3a0: GUESS(low); the sized delete argument is 0x18
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf17c3a0
{
public:
    DeletingLeaf17c3a0();
    virtual ~DeletingLeaf17c3a0();  // compared: 0x17c3a0

    std::uint8_t pad[0x10];
};
static_assert(sizeof(DeletingLeaf17c3a0) == 0x18, "size");
