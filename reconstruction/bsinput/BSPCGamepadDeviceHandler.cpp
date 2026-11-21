// Source exposure: mixed (community headers and pinned-image analysis).
// SPDX-License-Identifier: MIT (CommonLibSSE-NG declarations, Copyright (c) 2018 Ryan-rsm-McKenzie; full text: licenses/CommonLibSSE-NG.txt)
// Code origin: brown-room reconstruction from disassembly
// 0xe11ee0 BSPCGamepadDeviceHandler::Process
// 0xe11f30 BSPCGamepadDeviceHandler::Shutdown
// 0xe11f50 BSPCGamepadDeviceHandler::GetButtonNameFromID
// 0xe11f90 BSPCGamepadDeviceHandler::GetKeyCodeFromID
// 0xe11fb0 BSPCGamepadDeviceHandler::ClearInputState
// 0xe12390 BSPCGamepadDeviceHandler::~BSPCGamepadDeviceHandler
// 0xe12490 BSPCGamepadDeviceHandler::IsEnabled
#include "BSPCGamepadDeviceHandler.h"
BSPCGamepadDeviceHandler::BSPCGamepadDeviceHandler() {}
BSPCGamepadDeviceHandler::~BSPCGamepadDeviceHandler() { if (currentPCGamePadDelegate) delete currentPCGamePadDelegate; }
void BSPCGamepadDeviceHandler::Process(float a_elapsed) { if (!currentPCGamePadDelegate) { if (!ProcessGamepadEnabledChange) return; InitializeDelegate(); if (!currentPCGamePadDelegate) return; } currentPCGamePadDelegate->Process(a_elapsed); }
void BSPCGamepadDeviceHandler::Shutdown() { if (!currentPCGamePadDelegate) return; currentPCGamePadDelegate->Shutdown(); }
bool BSPCGamepadDeviceHandler::GetButtonNameFromID(std::int32_t a_id, char32_t* a_name) { if (currentPCGamePadDelegate) return currentPCGamePadDelegate->GetButtonNameFromID(a_id, a_name); return false; }
bool BSPCGamepadDeviceHandler::GetKeyCodeFromID(std::int32_t a_id, std::uint32_t* a_code) { if (currentPCGamePadDelegate) return currentPCGamePadDelegate->GetKeyCodeFromID(a_id, a_code); return false; }
void BSPCGamepadDeviceHandler::ClearInputState() { if (!currentPCGamePadDelegate) return; currentPCGamePadDelegate->ClearInputState(); }
bool BSPCGamepadDeviceHandler::IsEnabled() const { return currentPCGamePadDelegate != nullptr; }
