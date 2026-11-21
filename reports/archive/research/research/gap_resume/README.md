# 冻结 A 断点后尖端恢复实验

本分支生成独立的原生研究库 CrackV4GapResume.dll。软件发布版仍使用冻结 A。研究库以冻结源码作为同一翻译单元的只读依赖，沿用 A 的局部评分、动态规划、配准和尖端检查。

调用方先在研究库的句柄上按时序执行一次 CrackV4Process。仅对停止原因为 gap_unresolved 的当前帧，在同一线程、同一句柄上用同一幅原图及其帧序号调用 CrackGapResume。不能把另一个 DLL 的句柄传入。导出返回 UTF-8 JSON 指针，调用方需在同线程的下次调用前复制。segments 表示当前原图中的多段折线，tip_px 表示本分支确认的尖端。分段之间留白，complete_length_px 为空。恢复结果不会写回 A 的时序历史。

候选必须在局部窗口内有方向相容的后续暗线，16 列里至少 14 列得到支持，再逐窗继续追踪。末端还需通过冻结 A 的终端证据检查。最多输出三段断点后的路径。真实验证只覆盖已曝光 CT3，存在沿裂纹方向新出现的划痕被误接的反例。

在项目根目录编译 CMake 目标 CrackV4GapResume，运行以下命令可回放 CT3 及干扰对照。替换为新的 run-id 以保存独立结果。

```
python -B research/gap_resume/replay.py --run-id ct3_gap_new_run
python -B research/gap_resume/interference.py --run-id ct3_gap_new_run
```

