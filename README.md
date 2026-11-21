# CodexCrack · 裂纹路径与尖端检测

当前研究版本为 **V6.3 S2**，软件集成库为 **GrayDetectionV2 2.2.0.0**。日常 Python 入口默认 V5.15 S2，可切换到当前研究候选。[V6.3 开发报告](evidence/v6_3/REPORT.md) · [失败帧审计](evidence/v6_3/FAILURES_AUDIT.md) · [开发过程总索引](reports/INDEX.md)

| 入口 | 内容 |
|---|---|
| [当前状态](docs/CURRENT_STATE.md) | 各轮方法、验证结论和局限 |
| [算法源码](research/notch_identity_v63) | 材料带、白底漆配准、路径与尖端检测 |
| [可配置运行入口](run_crack_tip.py) | 参考图、批量输入、基准点、保存路径及渲染选项 |
| [Visual Studio 工程](GrayDetectionV2) | Windows x64 动态库、公开接口和版本资源 |
| [当前发布头文件](output/releases/GrayDetectionV2-2.2.0.0/GrayDetectionV2.hpp) | C++ 类与 C 导出函数 |
| [集成实测记录](output/verification/GrayDetectionV2_2_2_0_0/integration.json) | 导出表、实帧和调用测试 |
| [最新指标](evidence/latest_metrics.json) | 逐组人工标注对照摘要 |
| [历史归档](reports/archive) | 从既有交付包提取的阶段性报告与任务书 |

## 构建与回放

使用 Visual Studio 2022、x64 Release，打开 GrayDetectionV2/GrayDetectionV2.sln。将 OpenCV 4.4.0 SDK 按项目所需布局提供在 third_party/opencv440 下，或通过 MSBuild 属性 OpenCV440Root 指向其 include、lib 和 bin 所在目录。VS 工程会生成 GrayDetectionV2.hpp、GrayDetectionV2.lib 和 GrayDetectionV2.dll。[工程说明](GrayDetectionV2/README.md)

公开快照包含项目自有源码、报告正文及精选数值证据。外部原图、人工标注、媒体、编译器和第三方预编译依赖由数据持有方提供。原工作区中的媒体或私有数据链接需在本地打开。数据目录和工具路径请在配置中填写；公开版本使用匿名试验标识，原始冻结哈希对应本地封存文件。历史提交保留了上一版交接和可下载的诊断材料。
