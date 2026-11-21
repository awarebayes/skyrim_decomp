// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Code origin: brown-room reconstruction from disassembly; the listing only
// Recipe: reconstruction/recipes/o2-fpfast.json
// Adapted bodies: none
// 0x4324e0 BSFaceGenKeyframeExclusive::Function4324e0
// 0x432550 BSFaceGenKeyframeExclusive::Function432550
// Unk_0D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#include "BSFaceGenKeyframeExclusive.h"

// At: GUESS(low)
template <class T>
static T& At(const void* a_base, std::uint32_t a_offset)
{
    return *reinterpret_cast<T*>(const_cast<char*>(static_cast<const char*>(a_base)) + a_offset);
}

bool BSFaceGenKeyframeExclusive::Function4324e0() const
{
    if (0.0f == At<float>(this, 0x14)) {
        return true;
    }
    return false;
}

bool BSFaceGenKeyframeExclusive::Function432550(float a_value)
{
    if (a_value != At<float>(this, 0x14)) {
        At<float>(this, 0x14) = a_value;
        return true;
    }
    return false;
}

// Unk_0D: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
std::uint8_t BSFaceGenKeyframeExclusive::Unk_0D() const
{
    return 0x1;
}
