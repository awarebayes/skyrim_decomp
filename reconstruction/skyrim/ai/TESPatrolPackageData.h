// Source exposure: mixed (pinned image listing, public declarations and anonymous sibling hints).
// Origin: original reconstruction using target listing and anonymous sibling hints.
// Copy: SIBLING(fo4-private@1b765c70, author-permission); src/Shared/AI/PackageDataPatrol.cpp:42; adapted cast and copy.
// Compare: SIBLING(fo4-private@1b765c70, author-permission); src/Shared/AI/PackageDataPatrol.cpp:54; adapted cast and comparison.
// LoadGame: SIBLING(fo4-private@1b765c70, author-permission); src/Shared/AI/PackageDataPatrol.cpp:89; adapted two loads.
// TESPackageData and virtual declarations: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT); adapted declarations.
// TESPatrolPackageData: GUESS(low); qualified-name hint, target type name unverified.
// Field names and semantics: GUESS(low); from target accesses and sibling, signatures unverified.
// PatrolRefData, PatrolRefData::InitItem: CRASHLOGGER_PDB(59818@2026.10.24)
// PatrolRefData::Copy, PatrolData, member offsets: GUESS(low); from the target copy and init forwards.
// Code origin: brown-room reconstruction from disassembly
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
#pragma once
#include <cstddef>
#include <cstdint>
class TESForm;
class BGSLoadFormBuffer { public: void LoadDataEndian(void*, unsigned int, unsigned int); };
class TESPackageData { public: virtual std::uint8_t Compare() const; virtual void Copy(TESPackageData*, TESForm*); virtual void InitItem(TESForm*); virtual void LoadGame(BGSLoadFormBuffer*); };
class TESPatrolPackageData : public TESPackageData { public: void Copy(TESPackageData*, TESForm*) override; bool Compare(TESPackageData*); void LoadGame(BGSLoadFormBuffer*) override; bool repeatable; bool startAtNearestPoint; };
class PatrolData
{
public:
    void Copy(PatrolData* a_src, TESForm* a_form);
    void InitItem(TESForm* a_form);
    std::uint32_t unk00;
    std::uint32_t unk04;
    std::uint32_t unk08;
    std::uint32_t unk0C;
    std::uint32_t unk10;
    std::uint32_t unk14;
    std::uint32_t unk18;
    std::uint32_t unk1C;
};
class PatrolRefData
{
public:
    void Copy(PatrolRefData* a_src, TESForm* a_form);
    void InitItem(TESForm* a_form);
    std::uint32_t unk00;
    std::uint32_t unk04;
    PatrolData data;
};
static_assert(offsetof(PatrolRefData, data) == 8, "patrol data offset");
static_assert(sizeof(PatrolRefData) == 0x28, "patrol ref data size");
