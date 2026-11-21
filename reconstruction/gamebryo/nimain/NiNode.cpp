// Source exposure: mixed (binary-analysis, community headers).
// Origin: original reconstruction; types informed by CommonLibSSE-NG.
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Code origin: brown-room reconstruction from disassembly
// NiNode: EXE_RTTI
// NiNode: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT)
// NiBound, NiAVObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT)
// BSTempNodeManager, BSNiNode, NodeInFrustum, BoundInFrustum: CRASHLOGGER_PDB(59818@2026.10.24)
// NiNodeBase, worldBound offset, unk00: GUESS(low)
// Function4182a0, UpdateFirst, UpdateSecond, Function152a290, Function14e7f80, Functionfde7a0, UpdateFloat, QueryFlag, UpdateNode, Function6e9a50, GetPackageThatIsRunning, GetSpecialPackage, GetRunningOverride, Function639890, ConvertPosition, CountPosition: GUESS(low)
// 0xfde7a0 NiNode::Functionfde7a0
// 0xfd8fa0 BSTempNodeManager::~BSTempNodeManager
// 0x1005370 BSNiNode::~BSNiNode
// 0x224640 NodeInFrustum
// Adapted bodies: none
#include "NiNode.h"
#include <cstdint>

class NiCamera;

// NiBound: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT)
class NiBound
{
public:
    float x;
    float y;
    float z;
    float radius;
};
// NiAVObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a, MIT)
class NiAVObject
{
public:
    std::uint8_t unk00[0xE4];  // 00
    NiBound worldBound;        // E4
};
// NiNodeBase: GUESS(low); stands in for the polymorphic NiNode base whose destructor at 0xee19d0
// the two destructors below tail-call.
class NiNodeBase
{
public:
    virtual ~NiNodeBase();
};
class BSTempNodeManager : public NiNodeBase
{
public:
    ~BSTempNodeManager() override;
};
class BSNiNode : public NiNodeBase
{
public:
    ~BSNiNode() override;
};
bool BoundInFrustum(NiBound* a_bound, NiCamera* a_camera);

bool NiNode::Functionfde7a0() { bool value = false; QueryFlag(&value); return value; }

// 0xfd8fa0: installs its own vftable and tail-calls the base destructor at 0xee19d0.
BSTempNodeManager::~BSTempNodeManager()
{
}

// 0x1005370: installs its own vftable and tail-calls the base destructor at 0xee19d0.
BSNiNode::~BSNiNode()
{
}

// 0x224640: false for a null object, else the world bound at 0xE4 against the camera.
bool NodeInFrustum(NiAVObject* a_object, NiCamera* a_camera)
{
    if (a_object) {
        return BoundInFrustum(&a_object->worldBound, a_camera);
    }
    return false;
}
