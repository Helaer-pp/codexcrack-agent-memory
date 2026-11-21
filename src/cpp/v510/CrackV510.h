#pragma once
#include <stdint.h>
#ifdef CRACK510_BUILD
#define CR510 __declspec(dllexport)
#else
#define CR510 __declspec(dllimport)
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef void *Crack510Handle;
typedef struct {
    double x, y;
} Crack510Point;
typedef struct {
    const uint8_t *data;
    int width, height;
    int64_t stride;
} Crack510Image;
typedef struct {
    int left, top, right, bottom;
} Crack510Box;
typedef struct {
    uint32_t struct_size;
    int raw_only;
    /* 0 automatic acquisition window, 1 material window with tracked points,
       2 material window with paired 9x9 bright virtual points. */
    int material_mode;
    Crack510Box reference_box, fixed_band;
    double fixed_floor;
    Crack510Point virtual_points[2];
    double mm_per_pixel; /* 0 = uncalibrated */
} Crack510Config;
enum Crack510Status { CR510_NO_NOTCH = 0, CR510_NO_TIP = 1, CR510_VALID = 2 };
typedef struct {
    uint32_t struct_size;
    int status;
    Crack510Point root, tip;
    double path_length_px, projected_length_px;
    int path_points, bridge_columns;
    Crack510Point actual_reference[2], actual_current[2];
    double path_length_mm, detector_ms;
} Crack510Result;
/* Return 0 on success. No crack is a successful measurement; check status.
   Initialize result.struct_size before each call. P1 must be above P2. */
CR510 void Crack510DefaultConfig(Crack510Config *);
CR510 int Crack510Create(const Crack510Image *, const Crack510Point reference[2], const Crack510Config *,
                         Crack510Handle *);
CR510 int Crack510Process(Crack510Handle, const Crack510Image *, const Crack510Point current[2], Crack510Result *);
CR510 int Crack510GetBaseline(Crack510Handle, Crack510Result *);
CR510 int Crack510CopyPath(Crack510Handle, Crack510Point *, int capacity);
CR510 const char *Crack510LastError(void);
CR510 void Crack510SetNumThreads(int threads);
CR510 void Crack510Destroy(Crack510Handle);
#ifdef __cplusplus
}
#endif
