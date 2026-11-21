// Code origin: bodies written from the pinned image listing; declarations from the community headers.
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned image).
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2-root-includes.json
// Adapted bodies: none.
// 0xff2bc0 BSMultiBoundNode::IsEqual
// 0xff3430 BSMultiBoundNode::QPointWithin
// 0xff3450 BSMultiBoundNode::CheckBound2
// 0xff3470 BSMultiBoundNode::CheckBound1
#include "BSMultiBoundNode.h"

bool BSMultiBoundNode::IsEqual(NiObject* a_object)
{
    BSNiNode::IsEqual(a_object);
    return multiBound == static_cast<BSMultiBoundNode*>(a_object)->multiBound;
}

bool BSMultiBoundNode::QPointWithin(const NiPoint3& a_point)
{
    return multiBound->QWithinPoint(a_point);
}

bool BSMultiBoundNode::CheckBound2(const NiBound& a_targetBound)
{
    return multiBound->data->CheckBound(a_targetBound);
}

bool BSMultiBoundNode::CheckBound1(const BSMultiBound& a_targetBound)
{
    return multiBound->data->CheckBound(a_targetBound);
}
