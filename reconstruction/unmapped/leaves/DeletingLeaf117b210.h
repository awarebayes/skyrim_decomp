// Source exposure: mixed (community headers; compared functions from the pinned image).
// Code origin: original stand-in from the pinned image listing; no external body reused.
// SPDX-License-Identifier: CC0-1.0
// DeletingLeaf117b210: GUESS(low) STANDIN
// AddCallbackVisitor::dtor: CRASHLOGGER_PDB(59818@2026.10.24)
// unknown08: GUESS(low) STANDIN; padding to the size in the sized delete
#pragma once

#include <cstdint>
#include <cstddef>

class DeletingLeaf117b210
{
public:
    DeletingLeaf117b210();
    virtual ~DeletingLeaf117b210();  // compared: 0x117b210
    unsigned char unknown08[16];
};
static_assert(sizeof(DeletingLeaf117b210) == 0x18, "size observed from the sized delete argument");
