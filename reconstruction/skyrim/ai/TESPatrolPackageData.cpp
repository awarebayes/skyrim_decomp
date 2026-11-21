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
// 0x4a10d0 TESPatrolPackageData::Copy
// 0x4a1120 TESPatrolPackageData::Compare
// 0x4a11f0 TESPatrolPackageData::LoadGame
// 0x4a1320 PatrolRefData::InitItem
// Adapted bodies: none
// 0x4a12b0 PatrolRefData::Copy
#include "TESPatrolPackageData.h"
void TESPatrolPackageData::Copy(TESPackageData* src, TESForm*) { if (auto* p = dynamic_cast<TESPatrolPackageData*>(src)) { repeatable = p->repeatable; startAtNearestPoint = p->startAtNearestPoint; } }
bool TESPatrolPackageData::Compare(TESPackageData* src) { auto* p = dynamic_cast<TESPatrolPackageData*>(src); return !p || repeatable != p->repeatable || startAtNearestPoint != p->startAtNearestPoint; }
void TESPatrolPackageData::LoadGame(BGSLoadFormBuffer* b) { b->LoadDataEndian(&repeatable, 1, 1); b->LoadDataEndian(&startAtNearestPoint, 1, 1); }
void PatrolRefData::InitItem(TESForm* a_form) { data.unk08 = 3; data.InitItem(a_form); }
void PatrolRefData::Copy(PatrolRefData* a_src, TESForm* a_form) { unk00 = a_src->unk00; data.Copy(&a_src->data, a_form); }
