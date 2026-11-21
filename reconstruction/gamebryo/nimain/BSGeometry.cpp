// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Code origin: community declarations; bodies written from the pinned listing
// Recipe: reconstruction/recipes/o2-fpfast.json
// Adapted bodies: none
// 0xefc6e0 BSGeometry::UpdateDownwardPass
// 0xefc720 BSGeometry::UpdateSelectedDownwardPass
// 0xefc680 BSGeometry::SetSelectiveUpdateFlags
// 0xefc380 BSGeometry::RegisterStreamables
#include "BSGeometry.h"

#include <cstdint>
#include <cstddef>

// FieldAt: GUESS(low); typed access at a fixed byte offset inside the opaque base layout.
template <class T>
static inline T& FieldAt(void* a_base, std::size_t a_offset)
{
    return *reinterpret_cast<T*>(static_cast<std::uint8_t*>(a_base) + a_offset);
}

// Body done: RVA 0xefc6e0, 49 bytes, BSGeometry::UpdateDownwardPass.
void BSGeometry::UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2)
{
    BaseUpdateDownwardPass(a_data, a_arg2);
    if ((FieldAt<std::uint8_t>(&a_data, 0x4) & 1) != 0) {
        UpdateBoundFromFlags(a_data);
    }
}

// Body done: RVA 0xefc720, 56 bytes, BSGeometry::UpdateSelectedDownwardPass.
void BSGeometry::UpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2)
{
    BaseUpdateSelectedDownwardPass(a_data, a_arg2);
    if ((static_cast<std::uint8_t>(FieldAt<std::uint32_t>(this, 0xf4) >> 3) & 1) != 0) {
        UpdateBoundFromFlags(a_data);
    }
}

// Body done: RVA 0xefc680, 75 bytes, BSGeometry::SetSelectiveUpdateFlags.
void BSGeometry::SetSelectiveUpdateFlags(bool& a_selectiveUpdate, bool a_selectiveUpdateTransforms, bool& a_rigid)
{
    BaseSetSelectiveUpdateFlags(a_selectiveUpdate, a_selectiveUpdateTransforms, a_rigid);
    if (FieldAt<void*>(this, 0x130) != nullptr) {
        FieldAt<std::uint32_t>(this, 0xf4) |= 0x4;
        a_selectiveUpdate = true;
        FieldAt<std::uint32_t>(this, 0xf4) |= 0x2;
        a_rigid = false;
    }
}

// Body done: RVA 0xefc380, 121 bytes, BSGeometry::RegisterStreamables.
bool BSGeometry::RegisterStreamables(NiStream& a_stream)
{
    if (!BaseRegisterStreamables(a_stream)) {
        return false;
    }
    if (NiObject* child130 = FieldAt<NiObject*>(this, 0x130)) {
        child130->RegisterStreamables(a_stream);
    }
    if (NiObject* child128 = FieldAt<NiObject*>(this, 0x128)) {
        child128->RegisterStreamables(a_stream);
    }
    if (NiObject* child120 = FieldAt<NiObject*>(this, 0x120)) {
        child120->RegisterStreamables(a_stream);
    }
    return true;
}

