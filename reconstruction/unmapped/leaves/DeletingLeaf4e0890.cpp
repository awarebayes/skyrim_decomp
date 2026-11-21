// Source exposure: mixed (community headers; the pinned image listing).
// Code origin: original stand-in from the pinned image listing; no external declaration or body reused.
// 0x4e0890 DeletingLeaf4e0890::~DeletingLeaf4e0890
// CI hash: 0x4e0890 ??_GDeletingLeaf4e0890@@UEAAPEAXI@Z
// Adapted bodies: none
#include "DeletingLeaf4e0890.h"

void operator delete(void*, unsigned __int64) noexcept;

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
DeletingLeaf4e0890::DeletingLeaf4e0890() {}

DeletingLeaf4e0890::~DeletingLeaf4e0890() {}
