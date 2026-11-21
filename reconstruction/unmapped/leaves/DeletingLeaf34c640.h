// Source exposure: binary-analysis (the pinned image listing).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original; drafted from the pinned image listing
// DeletingLeaf34c640, data: GUESS(low) STANDIN
#pragma once

#include <cstdint>

void operator delete(void*, unsigned __int64) noexcept;

class DeletingLeaf34c640 {
public:
    virtual ~DeletingLeaf34c640() {}

    std::uint8_t data[0x10];
};
static_assert(sizeof(DeletingLeaf34c640) == 0x18, "minimal 24-byte virtual leaf");
