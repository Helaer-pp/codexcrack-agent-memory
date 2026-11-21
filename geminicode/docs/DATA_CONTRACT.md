# Data Contract Specification (`UCTIP-60Q-v1.0`)

## 1. Input Image Specifications
- **Pixel Encoding**: Original uncompressed 8-bit grayscale BMP images (`uint8`), strictly without downsampling, gamma distortion, or artificial smoothing.
- **Dimensions**:
  - GROUP_A: $1856 \times 2072$ pixels
  - Three-point-bend: $5120 \times 5120$ pixels
  - group_c: $5120 \times 5120$ pixels
- **Sequence Ordering**: Contiguous 0-based tracking number (`tracking_num` $\in [0, N-1]$), matching 1-based `frame_id`.
- **References**:
  - `fixed_ref`: Frame 0 of each dataset, providing baseline geometry and initial material texture.
  - `prev_ref`: Strictly the immediate preceding actual frame ($t-1$), not the last detected frame. Frame 0 has `prev_ref = None`.

## 2. Anchor Definitions
- Anchor points $P1 = (x_1, y_1)$ and $P2 = (x_2, y_2)$ are located on opposite sides of the machined notch.
- $P1$ and $P2$ measure Crack Mouth Opening Displacement (CMOD proxy), NOT the crack propagation axis.
- Normal unit vector $\vec{u}$ is defined perpendicular to $P1 \to P2$, oriented towards the right ($+x$). Swapping $P1$ and $P2$ preserves $\vec{u}_x > 0$.

## 3. Official Output Contract
- Each frame outputs:
  - `status`: One of `VALID`, `NO_VISIBLE_TRACK`, `IDENTITY_UNCERTAIN`, `TRACK_LOST`, `REACQUIRING`, `BUDGET_EXHAUSTED`, `PROCESSING_ERROR`.
  - `tip_x`, `tip_y`: Double precision coordinates in original image pixel space, or `null`.
  - `selected_track_id`: Identifier of the branch chosen.
  - `selection_rule`: Strictly `MAX_VALID_IMAGE_X`.
  - `preferred_uncertain_tip`: Diagnostic-only coordinate for uncertain observations. Never counted in official Hit@10 or Coverage.
- **No Crack Length**: Physical or pixel crack length is explicitly outside algorithm scope.
