// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Code origin: original; the community declarations and the pinned listing only
// BGSBaseAlias: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSBaseAlias::~BGSBaseAlias: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// FILL_TYPE, fillType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown08, unknown22: GUESS(low); the compared bodies read neither
#pragma once

#include <cstdint>
#include <cstddef>

// AliasMemberCleanupStub: GUESS(low); releases the member block at 0x8 (0xeb1100)
void AliasMemberCleanupStub(void* a_member) noexcept;

class BGSBaseAlias
{
public:
    enum class FILL_TYPE : std::uint16_t
    {
        kConditions = 0,
        kForced = 1,
        kFromAlias = 2,
        kFromEvent = 3,
        kCreated = 4,
        kFromExternal = 5,
        kUniqueActor = 6,
        kNearAlias = 7
    };

    BGSBaseAlias();
    virtual ~BGSBaseAlias();  // compared: 0x392c60 (scalar deleting destructor)

    std::uint8_t unknown08[0x18];  // 08
    FILL_TYPE fillType;            // 20
    std::uint8_t unknown22[0x06];  // 22
};
static_assert(sizeof(BGSBaseAlias) == 0x28, "BGSBaseAlias size");
