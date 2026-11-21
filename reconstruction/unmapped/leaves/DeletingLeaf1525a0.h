// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; derived from the pinned image listing.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf1525a0: GUESS(low); the sized delete argument is 0x20
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf1525a0
{
public:
    DeletingLeaf1525a0();
    virtual ~DeletingLeaf1525a0();  // compared: 0x1525a0

    std::uint8_t pad[0x18];
};
static_assert(sizeof(DeletingLeaf1525a0) == 0x20, "size");
