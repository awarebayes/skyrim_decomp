// Source exposure: mixed (binary-analysis of the pinned image; minimal stand-in).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original stand-in from the pinned image listing; no external body reused.
// 0x398380 DeletingLeaf398380::~DeletingLeaf398380
// CI hash: 0x398380 ??_GDeletingLeaf398380@@UEAAPEAXI@Z
// Adapted bodies: none
#include "DeletingLeaf398380.h"

// Forces emission of the vftable and, beside it, the compared deleting destructor.
static DeletingLeaf398380 object;
