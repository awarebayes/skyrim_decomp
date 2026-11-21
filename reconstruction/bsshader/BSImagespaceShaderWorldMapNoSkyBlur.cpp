// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original; reconstructed from the pinned image listing
// SPDX-License-Identifier: CC0-1.0
// 0x150b440 BSImagespaceShaderWorldMapNoSkyBlur::Unk_0D
// Adapted bodies: none
#include "BSImagespaceShaderWorldMapNoSkyBlur.h"

extern const char gUnk0D_0[];
extern const char gUnk0D_1[];
extern const char gUnk0D_2[];

Unk0DInfo* BSImagespaceShaderWorldMapNoSkyBlur::Unk_0D(Unk0DInfo* a_out)
{
    a_out->unk00 = gUnk0D_0;
    a_out->unk08 = gUnk0D_1;
    a_out->unk10 = gUnk0D_2;
    a_out->unk18 = gUnk0D_1;
    a_out->unk20 = nullptr;
    a_out->unk28 = nullptr;
    return a_out;
}
