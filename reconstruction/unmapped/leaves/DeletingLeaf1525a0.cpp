// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original; derived from the pinned image listing.
// SPDX-License-Identifier: CC0-1.0
// 0x1525a0 DeletingLeaf1525a0::~DeletingLeaf1525a0
// CI hash: 0x1525a0 ??_GDeletingLeaf1525a0@@UEAAPEAXI@Z
// Adapted bodies: none
#include "DeletingLeaf1525a0.h"

void operator delete(void*, unsigned __int64) noexcept;

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
DeletingLeaf1525a0::DeletingLeaf1525a0()
{
}

DeletingLeaf1525a0::~DeletingLeaf1525a0()
{
}
