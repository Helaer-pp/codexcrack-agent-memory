#pragma once
// Independent research ABI. Reuses ONLY the image/point layouts from this header.
// No A detector implementation is called or linked.
#include "CrackV4.h"
extern "C" {
__declspec(dllimport) void* GrayRefCreate(const CrackV4Image* reference, const CrackV4Point* reference_points);
__declspec(dllimport) int GrayRefProcess(void* handle, const CrackV4Image* current, const CrackV4Point* current_points);
__declspec(dllimport) const char* GrayRefRead(void* handle);
__declspec(dllimport) const float* GrayRefArray(void* handle, int field_id, int* width, int* height);
__declspec(dllimport) void GrayRefDestroy(void* handle);
}
// GRAY8 images, original-pixel XY, two points P1 above P2. Create owns a reference copy.
// Process current_points=nullptr selects frozen NCC; no GT or group parameter exists.
// Process return=0 means a serialized result is available; inspect JSON status for rejection.
// Tips are provisional only. Read returns transient handle-owned UTF-8 JSON.
// Array field IDs: reference_aligned, csm, rsm, valley, newdark, flank_low,
// valid_material, score (0..7). All exports float32, including 0/1 mask.
// Array pointers remain valid until next Process/Destroy; copy before reuse.
// Use one handle per sequence; no temporal prediction/GT state is implemented.
