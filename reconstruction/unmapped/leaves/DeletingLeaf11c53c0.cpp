// Source exposure: mixed (binary-analysis of the pinned image; minimal stand-in).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original stand-in from the pinned image listing; no external body reused.
// 0x11c53c0 DeletingLeaf11c53c0::~DeletingLeaf11c53c0
// CI hash: 0x11c53c0 ??_GDeletingLeaf11c53c0@@UEAAPEAXI@Z
// Adapted bodies: none
#include "DeletingLeaf11c53c0.h"

// Forces emission of the vftable and, beside it, the compared deleting destructor.
static DeletingLeaf11c53c0 object;
