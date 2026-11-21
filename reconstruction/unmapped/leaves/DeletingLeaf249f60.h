// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; the listing and community declarations only
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf249f60: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

// operator delete: the sized form the compared deleting destructor calls
void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf249f60
{
public:
    DeletingLeaf249f60();
    virtual ~DeletingLeaf249f60();  // compared: 0x249f60

    // pad: GUESS(low); storage sized to the allocation the compared destructor frees
    std::uint8_t pad[0x40];  // 08
};
static_assert(sizeof(DeletingLeaf249f60) == 0x48, "DeletingLeaf249f60 size");
