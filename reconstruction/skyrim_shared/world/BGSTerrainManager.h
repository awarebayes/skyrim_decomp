// Source exposure: mixed
// Origin: independently decoded target and anonymous sibling hint.
// BGSTerrainManager::GetLODLandRootForLevel: SIBLING(fo4-private@1b765c70, author-permission); adapted to target observations.
// Sibling source: fo4-private@1b765c70 src/Shared/DistantTerrain/BGSTerrainManager.cpp:6
// names: GUESS(low); names and original signatures are tentative.
// Code origin: original; the pinned image listing and community declarations only
// rootNode: CRASHLOGGER_PDB(59818@2026.10.24)
#pragma once

#include <cstdint>

class NiNode;

class BGSTerrainNode
{
public:
    void* GetChunkForPoint(const void* a_point, bool a_flag);
};

struct TerrainGlobal
{
    std::uint8_t pad00[0x10];
    std::uint32_t field10;
};

// g_terrainGlobal, TerrainGlobal: GUESS(low)
extern TerrainGlobal* g_terrainGlobal;

class BGSTerrainManager
{
public:
    static NiNode* roots[4];
    static NiNode* GetLODLandRootForLevel(unsigned level);
    void* Function5166e0(const void* a_point, bool a_flag);
    static bool Function516c20();

    std::uint8_t unknown00[0x10];
    BGSTerrainNode* rootNode;
};
