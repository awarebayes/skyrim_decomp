// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; the listing and community declarations only
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf32bad0: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf32bad0
{
public:
    DeletingLeaf32bad0();
    virtual ~DeletingLeaf32bad0();  // compared: 0x32bad0

    std::uint8_t unknown08[0x10];  // 08
};
static_assert(sizeof(DeletingLeaf32bad0) == 0x18, "DeletingLeaf32bad0 size");
