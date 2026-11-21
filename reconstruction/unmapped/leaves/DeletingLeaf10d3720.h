// Source exposure: mixed (binary-analysis of the pinned image; minimal stand-in).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original stand-in from the pinned image listing; no external body reused.
// DeletingLeaf10d3720: GUESS(low) STANDIN
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf10d3720
{
public:
    virtual ~DeletingLeaf10d3720() {}

private:
    // Unknown storage named by offset; only the 0x50 object size is evidenced.
    std::uint64_t unk8;   // 08
    std::uint64_t unk10;  // 10
    std::uint64_t unk18;  // 18
    std::uint64_t unk20;  // 20
    std::uint64_t unk28;  // 28
    std::uint64_t unk30;  // 30
    std::uint64_t unk38;  // 38
    std::uint64_t unk40;  // 40
    std::uint64_t unk48;  // 48
};

static_assert(sizeof(DeletingLeaf10d3720) == 0x50, "object size differs from the compared delete");
