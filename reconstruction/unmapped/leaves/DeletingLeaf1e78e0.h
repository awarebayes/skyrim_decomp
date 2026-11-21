// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; the listing and community declarations only
// SPDX-License-Identifier: CC0-1.0
// Adapted bodies: none
// DeletingLeaf1e78e0: GUESS(low) STANDIN
#pragma once

#include <cstdint>
#include <cstddef>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf1e78e0
{
public:
    DeletingLeaf1e78e0();
    virtual ~DeletingLeaf1e78e0();  // compared: 0x1e78e0

    std::uint8_t padding[0x10];  // 08
};
static_assert(sizeof(DeletingLeaf1e78e0) == 0x18, "leaf size");
