#pragma once
#include <stdint.h>
#ifdef _WIN32
#define GRAYREF_V2_API __declspec(dllexport)
#else
#define GRAYREF_V2_API
#endif
// Image memory is borrowed during the call; gray uint8, original pixel coordinates.
struct GrayRefV2Image {const unsigned char* data;int width,height;int64_t stride;};
struct GrayRefV2Point {double x,y;};
extern "C" {
GRAYREF_V2_API void* GrayRefV2Create(const GrayRefV2Image*,const GrayRefV2Point* referencePair);
GRAYREF_V2_API int GrayRefV2Process(void*,const GrayRefV2Image*,const GrayRefV2Point* currentPair);
// JSON/array pointers remain valid until next Process or Destroy. Copy if needed.
GRAYREF_V2_API const char* GrayRefV2Read(void*);
GRAYREF_V2_API const float* GrayRefV2Array(void*,int field,int* width,int* height);
GRAYREF_V2_API void GrayRefV2Destroy(void*);
GRAYREF_V2_API int GrayRefV2NumericSelfTest();
}
