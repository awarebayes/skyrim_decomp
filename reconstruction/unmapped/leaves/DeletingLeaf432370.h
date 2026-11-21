// Source exposure: binary-analysis (the shape of the compared function in the pinned image).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original stand-in; the pinned image listing and community names only
// Adapted bodies: none
// DeletingLeaf432370, object: GUESS(low) STANDIN
// unk08, unk10: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf432370
{
public:
    DeletingLeaf432370();
    virtual ~DeletingLeaf432370();  // compared: 0x432370 (scalar deleting destructor)

    std::uint64_t unk08;  // 0x08
    std::uint64_t unk10;  // 0x10
};
static_assert(sizeof(DeletingLeaf432370) == 24, "size observed from the sized delete argument");
