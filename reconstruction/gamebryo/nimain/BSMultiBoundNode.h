// Source exposure: mixed (community declarations; the pinned image listing).
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Code origin: original bodies; class layout and virtual slot order follow the community declarations and the pinned listing.
// Declarations informed by powerof3/CommonLibSSE, GPL-3.0.
// BSMultiBoundNode, BSNiNode, BSMultiBound, BSMultiBoundShape, NiPoint3, QPointWithin, QWithinPoint, Unk_26, multiBound, cullingMode, lastAccumTime, unk10, pad14, data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSMultiBoundNode::CheckBound1, BSMultiBoundNode::CheckBound2, BSMultiBoundShape::CheckBound, NiBound: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// GetMultiBoundRoom, IsEqual, ~BSMultiBoundNode, GetRTTI, AsMultiBoundNode, CreateClone, LoadBinary, LinkObject, RegisterStreamables, SaveBinary, UpdateDownwardPass, UpdateWorldBound, OnVisible, UpdateUpwardPass: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSMultiBoundShape::unknown10: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "declarations/NiNode.h"

class BSMultiBoundRoom;
class NiPoint3;
class NiBound;
class BSMultiBound;
class BSMultiBoundShape;

class BSNiNode : public NiNode
{
public:
    ~BSNiNode() override;  // 00
    const NiRTTI* GetRTTI() const override;  // 02
    NiObject* CreateClone(NiCloningProcess& a_cloning) override;  // 17
};
static_assert(sizeof(BSNiNode) == 0x128, "BSNiNode size");

// The bound object a node carries. Only the two added virtual slots and the shape pointer are used here.
// data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares NiPointer, the target loads the stored pointer directly
class BSMultiBound : public NiObject
{
public:
    virtual bool QWithinPoint(const NiPoint3& a_pos);  // 25
    virtual void Unk_26();  // 26

    std::uint32_t unk10;  // 10
    std::uint32_t pad14;  // 14
    BSMultiBoundShape* data;  // 18
};
static_assert(sizeof(BSMultiBound) == 0x20, "BSMultiBound size");
static_assert(offsetof(BSMultiBound, data) == 0x18, "BSMultiBound data offset");

// The shape a bound points at. Slots 25 to 28 are the ones the compared functions reach.
// The two CheckBound overloads are declared with the later slot first: MSVC gives the
// later-declared overload the lower slot, so this order puts the BSMultiBound overload at 27.
class BSMultiBoundShape : public NiObject
{
public:
    virtual std::uint32_t GetType() = 0;  // 25
    virtual float GetLength() = 0;  // 26
    virtual bool CheckBound(const NiBound& a_targetBound) = 0;  // 28
    virtual bool CheckBound(const BSMultiBound& a_targetBound) = 0;  // 27

    std::uint8_t unknown10[0x8];  // 10
};
static_assert(sizeof(BSMultiBoundShape) == 0x18, "BSMultiBoundShape size");

class BSMultiBoundNode : public BSNiNode
{
public:
    ~BSMultiBoundNode() override;  // 00
    const NiRTTI* GetRTTI() const override;  // 02
    BSMultiBoundNode* AsMultiBoundNode() override;  // 06
    NiObject* CreateClone(NiCloningProcess& a_cloning) override;  // 17
    void LoadBinary(NiStream& a_stream) override;  // 18
    void LinkObject(NiStream& a_stream) override;  // 19
    bool RegisterStreamables(NiStream& a_stream) override;  // 1A
    void SaveBinary(NiStream& a_stream) override;  // 1B
    virtual bool IsEqual(NiObject* a_object);  // compared: 0xff2bc0  // slot 1C
    void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2) override;  // 2C
    void UpdateWorldBound() override;  // 2F
    void OnVisible(NiCullingProcess& a_process) override;  // 34
    void UpdateUpwardPass(NiUpdateData& a_data) override;  // 3D
    virtual BSMultiBoundRoom* GetMultiBoundRoom();  // 3E
    virtual bool QPointWithin(const NiPoint3& a_point);  // 3F
    virtual bool CheckBound1(const BSMultiBound& a_targetBound);  // 40
    virtual bool CheckBound2(const NiBound& a_targetBound);  // 41

    BSMultiBound* multiBound;  // 128, NG: NiPointer<BSMultiBound>
    std::uint32_t cullingMode;  // 130, NG: BSCullingProcess::BSCPCullingType
    float lastAccumTime;  // 134
};
static_assert(sizeof(BSMultiBoundNode) == 0x138, "BSMultiBoundNode size");
static_assert(offsetof(BSMultiBoundNode, multiBound) == 0x128, "multiBound offset");
