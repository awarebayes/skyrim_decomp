// Source exposure: mixed (community headers and pinned-image analysis).
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Code origin: brown-room reconstruction from disassembly
// BSPCGamepadDeviceHandler, currentPCGamePadDelegate, Process, IsEnabled: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// Shutdown, GetButtonNameFromID, GetMappingKey, GetKeyCodeFromID, ClearInputState, BSIInputDevice vtable order: CRASHLOGGER_PDB(59818@2026.10.24)
// ProcessGamepadEnabledChange: GUESS(low)
#pragma once
#include <cstdint>
#include <cstddef>
class BSIInputDevice
{
public:
    virtual ~BSIInputDevice() {}
    virtual void Initialize();
    virtual void Process(float a_elapsed);
    virtual void Shutdown();
    virtual bool GetButtonNameFromID(std::int32_t a_id, char32_t* a_name);
    virtual std::uint32_t GetMappingKey(char32_t* a_name);
    virtual bool GetKeyCodeFromID(std::int32_t a_id, std::uint32_t* a_code);
    virtual bool IsEnabled() const;
    virtual void ClearInputState();
};
class BSPCGamepadDeviceDelegate : public BSIInputDevice {};
class BSPCGamepadDeviceHandler : public BSIInputDevice
{
public:
    BSPCGamepadDeviceHandler();
    ~BSPCGamepadDeviceHandler() override;
    void Process(float a_elapsed) override;
    void Shutdown() override;
    bool GetButtonNameFromID(std::int32_t a_id, char32_t* a_name) override;
    bool GetKeyCodeFromID(std::int32_t a_id, std::uint32_t* a_code) override;
    bool IsEnabled() const override;
    void ClearInputState() override;
    void InitializeDelegate();
    BSPCGamepadDeviceDelegate* currentPCGamePadDelegate;
};
static_assert(sizeof(BSPCGamepadDeviceHandler) == 0x10, "gamepad handler size");
extern bool ProcessGamepadEnabledChange;
