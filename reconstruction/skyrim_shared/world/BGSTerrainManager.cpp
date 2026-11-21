// Source exposure: mixed
// Origin: independently decoded target and anonymous sibling hint.
// BGSTerrainManager::GetLODLandRootForLevel: SIBLING(fo4-private@1b765c70, author-permission); adapted to target observations.
// Sibling source: fo4-private@1b765c70 src/Shared/DistantTerrain/BGSTerrainManager.cpp:6
// names: GUESS(low); names and original signatures are tentative.
// 0x5164c0 BGSTerrainManager::GetLODLandRootForLevel
// Code origin: original; the pinned image listing and community declarations only
// 0x5166e0 BGSTerrainManager::Function5166e0
// Adapted bodies: none
// 0x516c20 BGSTerrainManager::Function516c20
#include "BGSTerrainManager.h"

NiNode* BGSTerrainManager::GetLODLandRootForLevel(unsigned level) { switch(level) { case 4: return roots[0]; case 8: return roots[1]; case 16: return roots[2]; } NiNode* node = roots[3]; if (level != 32) return nullptr; return node; }

void* BGSTerrainManager::Function5166e0(const void* a_point, bool a_flag)
{
    BGSTerrainNode* node = rootNode;
    if (node) {
        return node->GetChunkForPoint(a_point, a_flag);
    }
    return nullptr;
}

bool BGSTerrainManager::Function516c20()
{
    return g_terrainGlobal->field10 > 0;
}
