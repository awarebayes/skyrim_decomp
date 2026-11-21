// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original; reconstructed from the pinned image listing
// SPDX-License-Identifier: CC0-1.0
// BSImagespaceShaderISDownsample, BSImagespaceShaderISDownsample::Unk_0D: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

struct Unk0DInfo
{
    const char* volatile unk00;  // 00
    const char* volatile unk08;  // 08
    const char* volatile unk10;  // 10
    const char* volatile unk18;  // 18
    const char* volatile unk20;  // 20
    const char* volatile unk28;  // 28
};
static_assert(sizeof(Unk0DInfo) == 0x30, "Unk0DInfo size");

class BSImagespaceShaderISDownsample
{
public:
    Unk0DInfo* Unk_0D(Unk0DInfo* a_out);
};
