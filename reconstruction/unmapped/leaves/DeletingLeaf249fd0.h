// Source exposure: binary-analysis (the shape of the compared function in the pinned image).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original stand-in; the pinned image listing and community names only
// Adapted bodies: none
// DeletingLeaf249fd0, object: GUESS(low) STANDIN
// unk08, unk10, unk18: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf249fd0
{
public:
    DeletingLeaf249fd0();
    virtual ~DeletingLeaf249fd0();  // compared: 0x249fd0 (scalar deleting destructor)

    std::uint64_t unk08;  // 0x08
    std::uint64_t unk10;  // 0x10
    std::uint64_t unk18;  // 0x18
};
static_assert(sizeof(DeletingLeaf249fd0) == 32, "size observed from the sized delete argument");
