# 当前基准点解耦算法

## 总体流程

```mermaid
flowchart TD
    A[参考图像 + 参考 P1/P2] --> B[建立固定裂纹坐标系]
    B --> C[提取固定参考纹理块]
    B --> D[提取参考物理标记模板]
    B --> E[参考帧根部/尖端初始化]

    F[当前图像 + 当前 P1/P2] --> G{当前 P1/P2 有效?}
    G -- 否 --> X[返回输入错误]
    G -- 是 --> H[主路径粗刚体定位]

    H --> I[固定参考纹理残差配准]
    I --> J[主裂纹路径搜索]
    J --> K[根部确认与完整长度测量]

    H --> L[端点独立配准入口]
    L --> M[固定参考纹理相位配准]
    M --> N{配准通过?}
    N -- 否 --> O[参考物理标记模板搜索]
    O --> P{标记配准通过?}
    N -- 是 --> Q[得到端点专用变换]
    P -- 是 --> Q
    P -- 否 --> R[registration_uncertain]

    Q --> S[独立计算尖端 ROI 中心和方向]
    S --> T[ROI 内裂纹路径搜索]
    T --> U[尖端终止条件审计]
    U --> V{尖端证据充分?}
    V -- 否 --> W[尖端未确认]
    V -- 是 --> Y[输出尖端坐标和确认状态]

    K --> Z[输出主路径/根到尖端长度]
    Y --> AA[组合结果]
    W --> AA
    Z --> AA
```

## 当前 P1/P2 的作用边界

```mermaid
flowchart LR
    P[当前 P1/P2]
    P --> A[主路径粗定位先验]
    A --> B[路径搜索窗口]
    A --> C[根部与完整长度测量]
    P -. 不直接决定 .-> D[端点 ROI 中心]
    P -. 不直接决定 .-> E[端点 ROI 方向]
    P -. 不直接决定 .-> F[尖端确认状态]

    R[固定参考纹理/标记] --> G[端点专用变换]
    G --> D
    G --> E
    G --> H[端点坐标]
    I[当前图像中的裂纹证据] --> F
    I --> H
```

## 单帧处理顺序

```mermaid
sequenceDiagram
    participant Caller as 调用方
    participant Detector as CrackV4Detector
    participant Main as 主路径配准
    participant Tip as 端点独立配准
    participant ROI as 尖端 ROI
    participant Audit as 终止审计

    Caller->>Detector: 当前图像 + 当前 P1/P2
    Detector->>Detector: 校验点有限、在图像内、顺序和间距有效
    Detector->>Main: 使用 P1/P2 建立粗刚体先验
    Main->>Main: 固定参考纹理残差修正
    Main-->>Detector: 主路径、根部、长度候选

    Detector->>Tip: 不读取当前 P1/P2 的端点配准
    Tip->>Tip: 固定参考纹理相位配准
    alt 纹理配准不足
        Tip->>Tip: 固定参考物理标记模板搜索
    end
    alt 独立配准失败
        Tip-->>Detector: registration_uncertain
        Detector-->>Caller: 尖端未确认
    else 独立配准成功
        Tip-->>ROI: 端点专用中心和方向
        ROI->>ROI: 搜索 ROI 内裂纹候选路径
        ROI->>Audit: 检查尾端支持、连续性、竞争路径和终止条件
        alt 证据充分
            Audit-->>Caller: 尖端确认 + 原图像素坐标
        else 证据不足
            Audit-->>Caller: 尖端未确认
        end
    end
```

## 输出关系

```mermaid
flowchart TD
    A[端点独立变换] --> B[尖端 ROI]
    B --> C[尖端确认状态]
    B --> D[尖端坐标]
    E[主路径测量] --> F[裂纹路径]
    E --> G[根到尖端完整长度]
    C --> H[最终结果]
    D --> H
    F --> H
    G --> H

    I[registration_uncertain] --> C
    J[roi_no_path] --> C
    K[terminal audit failure] --> C
```

## 解耦验证判据

固定参考图像、当前图像和算法参数，只改变当前帧 P1/P2：

1. 尖端确认状态必须一致；
2. 已确认尖端的 `(x, y)` 必须一致；
3. 完整路径和长度单独评估，因为它们仍允许使用 P1/P2 作为主路径粗定位先验；
4. 越界、反向、退化或错误物理对应的 P1/P2 属于输入有效性问题，不作为正常解耦样本。

当前候选版本的严格验证记录见：

[anchor_decoupling_strict_20261110_r03/REPORT.md](../output/runs/anchor_decoupling_strict_20261110_r03/REPORT.md)
