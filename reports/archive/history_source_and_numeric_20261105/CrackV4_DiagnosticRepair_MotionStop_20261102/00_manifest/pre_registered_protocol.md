# 预注册方案

{
  "version": "DiagnosticRepair-MotionStop-v2",
  "registered_utc": "2026-11-02T09:03:15.201154+00:00",
  "production": "KEEP_FROZEN_A",
  "flags": 3572,
  "SHADOW": 1,
  "terminal_validation": 1,
  "refine": true,
  "ratio": 1,
  "threads": 4,
  "real_tip_GT": "N/A",
  "isolation": {
    "DEV": "first four groups only",
    "spatial": "192px chips, disjoint DEV/TEST rectangles with >=32px gap; DEV early third, TEST last third reference source frames",
    "temporal": "DEV source at frame0, TEST source at >=0.8*N; different texture rectangles and random seeds; same specimen is correlated",
    "LOGO": "four folds choose candidate on three groups DEV only, evaluate remaining group TEST; no heldout feedback",
    "holdout": "one new native replay and one diagnostic pass after all source/tests/templates/selection committed+hashed; known historical regression not blind"
  },
  "seeds": {
    "DEV": 2026110201,
    "TEST": 2026110202,
    "bootstrap": 2026110203
  },
  "states": {
    "current": ">=16 finite fixed-path samples, >=60% lower-bound normal dark valley >max(1.5,3*noiseMAD); independent of legacy photo",
    "material": "valid train>=2, spatially disjoint heldout>=2, heldout corrected residual P95<=2px and center span>=62px; conditional consistency not physical error bound",
    "reference": "material PASS plus >=32 photometrically eligible fixed-path pairs, affine residual MAD<=12 and encoded fractions<=.15; otherwise UNKNOWN/FAIL, never infer new crack"
  },
  "match_variants": {
    "LEGACY": {
      "radius": 12,
      "ncc": 0.75,
      "margin": 0.025,
      "fb": 1.5,
      "encoding_high_reject": true
    },
    "STRUCTURE": {
      "radius": 12,
      "ncc": 0.75,
      "margin": 0.025,
      "fb": 1.5,
      "encoding_high_reject": false
    },
    "CONSERVATIVE12": {
      "radius": 12,
      "ncc": 0.9,
      "margin": 0.05,
      "fb": 0.5,
      "photo_mad": 6,
      "encoding_high_reject": false
    },
    "CONSERVATIVE24": {
      "radius": 24,
      "ncc": 0.9,
      "margin": 0.05,
      "fb": 0.5,
      "photo_mad": 6,
      "encoding_high_reject": false
    }
  },
  "shared_match_requirements": "finite; template std>=2 and median gradient>=.65; low<=20 fraction<=.15 and dynamic P90-P10>=4 for repaired variants; original anchor/path/heldout geometric exclusions retained; peak not border; shadow never feeds detector",
  "gt_grid": {
    "radii": [
      12,
      24
    ],
    "ncc": [
      0.6,
      0.75,
      0.9
    ],
    "error_tolerance_px": 0.5,
    "positive_conditions": [
      "identity",
      "subpixel",
      "integer",
      "edge11",
      "edge12",
      "outside16",
      "outside28",
      "rotate0.5",
      "scale1.01",
      "nonrigid2",
      "offset10",
      "gain0.8",
      "gamma1.5",
      "gradient20",
      "clip_gain1.6",
      "noise2"
    ],
    "textures": [
      "material",
      "bright_structured",
      "low_texture",
      "repeated",
      "hole_edge",
      "random_textured"
    ],
    "negative_conditions": [
      "unrelated_texture",
      "similar_repeat",
      "exact_lookalike_no_correspondence",
      "occluded_template"
    ],
    "all_failures_retained": true
  },
  "selection": "per LOGO training only: require accepted>=30, no added false accept in any training material, paired false count<=legacy, Wilson95 upper false/accepted<=.05, >=.05 absolute correct/all gain; choose most correct/all then fewer false then lower radius then lexical. If none select LEGACY/NO_SAFE_REPAIR. TEST claims require paired no added false each group, >=.05 correct/all gain and Wilson upper<=.05; zero evaluable -> N/A.",
  "intervals": "Wilson95 for rates; paired new-correct/new-false counts; 1000 fixed-seed paired bootstrap for difference correct/all and false/all, conditional on constructed cases, not specimen independence",
  "CT2": {
    "mode": "auto=2",
    "selection": "union prior locked14 and exactly prior19 INDETERMINATE; plus fixed native branch-boundary first case if not already included",
    "coarse": "all467 on/off with exact native double path/state check",
    "deep": "prior14 + first3 unexplained",
    "counterfactual": "fresh independent detector per trial; copy captured prior/history/frame and last-confirmed state by value; same on and off positive controls, symmetric swapped motions",
    "translation_amplitudes_px": [
      0,
      0.25,
      0.5,
      1,
      2,
      4,
      8
    ],
    "directions": [
      "+x",
      "-x",
      "+y",
      "-y"
    ],
    "rotation_degrees": [
      0.02,
      -0.02,
      0.05,
      -0.05,
      0.1,
      -0.1,
      0.2,
      -0.2,
      0.4,
      -0.4
    ],
    "rotation_center": "reference P1/P2 center mapped into current by on transform; rotate around that current point",
    "intervention_scope": "post motion R/T only; cfg and production rules untouched; amplitude not material error",
    "divergence_tolerances": [
      1,
      3,
      5
    ],
    "persistent_arc_px": 12,
    "continuation": "short-to-long P95<=3 and arc gap>30; geometric only",
    "keep_original_19_unexplained": true
  },
  "synthetic_cracks": "all prior archived engineering weak/curved/fading/static/no-line/encoding control cases replayed against immutable A snapshots; new motion-only probe has known motion, not physical crack tip GT",
  "performance": "predecoded production native Process+GetResultV2+CopyPath+necessary allocation; separate dedicated DEV pass after research tasks; fifth unique replay; no abnormal exclusions; budget66.67ms",
  "hardware": "NOT_RUN_HARDWARE, no camera/stage session; digitally known transforms are not actual exposure",
  "status_choices": [
    "PASS_DIAGNOSTIC_ONLY",
    "PARTIAL",
    "NOT_PROVEN",
    "FAIL"
  ],
  "final_default": "KEEP_FROZEN_A"
}

在本轮DEV指标计算前写入；开发修复若偏离，保留偏离记录。第五组只在最终Git/SHA冻结后执行。GT容差0.5px仅用于程序构造运动，不是实际裂纹精度容差。
