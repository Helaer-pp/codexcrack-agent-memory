# R02 证据盘点

状态值含义：`AVAILABLE`=实际存在并可读取；`MISSING`=文件不存在；`NOT_REPRODUCIBLE`=文件存在但无法按原命令重建。

| 资产 | 状态 | 实际路径/说明 |
|---|---|---|
| R01 README/report/CSV | AVAILABLE | `output/runs/phase1_audit_decoupling_20261110_r01/` |
| 当前 C++ 工程 | AVAILABLE | `src/cpp/a/` |
| 当前候选 DLL | AVAILABLE | `output/build/src/cpp/a/Release/CrackV4.dll` |
| 原始输入清单 | AVAILABLE | `data/inputs/six_groups_manifest.csv` |
| 锚点记录 | AVAILABLE | `data/anchors/` |
| R01 Git commit | NOT_REPRODUCIBLE | 当前目录无 `.git` 仓库，commit=null；用源码树 hash 替代 |
| R01 独立 worktree | NOT_REPRODUCIBLE | 无 Git worktree；R02 只写本目录下新输出，不改 R01 |
| T2-B-real 外部跟踪轨迹 | MISSING | 未发现针对不同初始选点的真实上游轨迹；仅有统一清单中的当前点轨迹 |
| 人工物理 GT | MISSING | 项目当前无可用人工尖端 GT |
