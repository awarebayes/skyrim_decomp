// Source exposure: mixed (community headers; the pinned image listing).
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Code origin: original; the listing and community declarations only
// BGSRefAlias, BGSRefAlias::~BGSRefAlias, BGSRefAlias::Load, BGSRefAlias::InitItem, BGSRefAlias::QType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// GenericFillData, FromAliasFillData, FromEventFillData, fillData, conditions: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// GetForcedRefType, GetForcedEventData, GetForcedFromEvent: GUESS(low); the names only, the bodies are the listing
// TESFile, TESForm, BSFixedString, TESCondition, BGSLocationRefType: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); forward declarations only
#pragma once

#include <cstdint>
#include <cstddef>
#include "skyrim_shared/quest/BGSBaseAlias.h"

class TESFile;
class TESForm;
class BSFixedString;
class TESCondition;
class BGSLocationRefType;

class BGSRefAlias : public BGSBaseAlias
{
public:
    virtual ~BGSRefAlias();  // compared: 0x3a2e60  // slot 00
    // BGSBaseAlias in this tree declares no virtual members, so these omit override.
    virtual bool Load(TESFile* a_mod);  // 01
    virtual void InitItem(TESForm* a_form);  // 02
    virtual const BSFixedString& QType() const;  // 03
    BGSRefAlias();

    BGSLocationRefType* GetForcedRefType() const;  // 0x3e0030
    std::uint32_t GetForcedEventData() const;  // 0x3a2fe0
    std::uint32_t GetForcedFromEvent() const;  // 0x3a3000

    struct FromAliasFillData
    {
        std::uint32_t forcedFromAlias;      // 00
        std::uint32_t pad04;                // 04
        BGSLocationRefType* forcedRefType;  // 08
    };

    struct FromEventFillData
    {
        std::uint32_t forcedFromEvent;  // 00
        std::uint32_t forcedEventData;  // 04
    };

    union GenericFillData
    {
        std::uint64_t padding[3];  // 00
        FromAliasFillData fromAlias;
        FromEventFillData fromEvent;
    };
    static_assert(sizeof(GenericFillData) == 0x18, "GenericFillData size");

    GenericFillData fillData;  // 28
    TESCondition* conditions;  // 40
};
static_assert(sizeof(BGSRefAlias) == 0x48, "BGSRefAlias size");
