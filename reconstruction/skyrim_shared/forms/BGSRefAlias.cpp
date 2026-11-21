// Source exposure: mixed (community headers; the pinned image listing).
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Code origin: original; the listing and community declarations only
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2-root-includes.json
// 0x3a2e60 BGSRefAlias::~BGSRefAlias
// 0x3e0030 BGSRefAlias::GetForcedRefType
// 0x3a2fe0 BGSRefAlias::GetForcedEventData
// 0x3a3000 BGSRefAlias::GetForcedFromEvent
// Adapted bodies: none
#include "BGSRefAlias.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared.
BGSRefAlias::BGSRefAlias()
{
}

// The target calls the complete destructor out of line, so it stays declared only in the header.

// The alias keeps the reference type only when it is filled from another alias.
BGSLocationRefType* BGSRefAlias::GetForcedRefType() const
{
    if (fillType == FILL_TYPE::kFromAlias) {
        return fillData.fromAlias.forcedRefType;
    }
    return nullptr;
}

// The event fill data is only meaningful for an alias filled from an event.
std::uint32_t BGSRefAlias::GetForcedEventData() const
{
    if (fillType == FILL_TYPE::kFromEvent) {
        return fillData.fromEvent.forcedEventData;
    }
    return 0xFFFFFFFF;
}

std::uint32_t BGSRefAlias::GetForcedFromEvent() const
{
    if (fillType == FILL_TYPE::kFromEvent) {
        return fillData.fromEvent.forcedFromEvent;
    }
    return 0xFFFFFFFF;
}
