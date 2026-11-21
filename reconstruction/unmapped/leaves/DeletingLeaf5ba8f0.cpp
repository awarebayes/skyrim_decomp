// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original stand-in from the pinned image listing; no external declaration or body reused.
// 0x5ba8f0 DeletingLeaf5ba8f0::~DeletingLeaf5ba8f0
// CI hash: 0x5ba8f0 ??_GDeletingLeaf5ba8f0@@UEAAPEAXI@Z
// Adapted bodies: none
#include "DeletingLeaf5ba8f0.h"

void operator delete(void*, unsigned __int64) noexcept;

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
DeletingLeaf5ba8f0::DeletingLeaf5ba8f0() {}

DeletingLeaf5ba8f0::~DeletingLeaf5ba8f0() {}
