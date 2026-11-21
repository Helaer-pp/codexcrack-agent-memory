# 构建与复现

当前工作目录为`.`。生成文件全部置于项目output；外部F盘图像和原始点文件只读。原始冻结Python不能直接修成Unicode读图：本轮adapter把原字节复制到ASCII路径后运行它，逐帧核验原SHA。输入manifest明确保留原路径，不能把stage路径当成数据原始来源。

## 已实测构建

```powershell
Set-Location .
& D:/CMake/bin/cmake.exe -S research/p1p2_grayref_v1 -B output/build/p1p2_grayref_v1 -G 'Visual Studio 17 2022' -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/p1p2_grayref_v1 --config Release
```

C++17、MSVC19.29/v142、OpenCV4.4、/O2 /fp:strict。产物`output/build/p1p2_grayref_v1/Release/P1P2GrayRefV1.dll`，SHA256 `58e073e7830ccccba77e6cea48e1c33d0977317ed896d1b535d0def7f9d93ef1`。封存后不要覆盖该目录，新的构建用新output子目录。候选SDK见`P1P2GrayRefV1_Research_SDK.zip`，含DLL、导入库、OpenCV依赖、图像/点ABI头和独立接口头；没有生产替换动作。

## 独立目录复现入口

```powershell
$env:PYTHONPYCACHEPREFIX='./output/pycache'
$env:PYTHONIOENCODING='utf-8'
& D:/ProgramData/anaconda3/python.exe research/p1p2_grayref_v1/reproduce.py --output output/runs/p1p2_grayref_v1_reproduction_example --plan
# 检查计划后执行开发全序列（不要指向当前封存目录）：
& D:/ProgramData/anaconda3/python.exe research/p1p2_grayref_v1/reproduce.py --output output/runs/p1p2_grayref_v1_reproduction_example
```

默认只执行四个DEVELOPMENT组，按顺序完整回放Python、C++、parity、离线评分、12帧CLI计时和图像视频。若明确要重现已曝光的两验证组，首次命令额外加`--include-validation`；脚本仅在开发parity通过、固定开发评分完成后锁版本进入，不能拿它调整规则。已有输出目录会被拒绝。每次新执行将读取原图，但不会写回数据集或改标签。

复现所需数据：根目录完整zip、原始F盘文件、`uctt_r05f_20261111_r01/input_inventory_allowed.csv`及`selected_frames.csv`元数据、`r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip`、R05D封存A55结果。这些旧目录仅提供清单/标签/已运行结果，不调用旧检测源码。CT3点源独立TXT缺失，使用明确帧名/坐标num映射的历史坐标CSV。路径和数据角色在本轮inputs目录均可审计。

Python环境：3.12.7、cv2 4.12.0、NumPy1.26.4、SciPy1.17.1、pandas2.2.2、matplotlib3.10.9，另需Pillow。新一键编排只做了`--plan`与语法检查，没有为测试入口而重复整套验证；各实际阶段已完整执行并有日志。此次并行worker与复现入口顺序worker的性能不能直接等同。

## 结果读取与API

- `py_runs/<group>/<frame>/summary_results.csv`：joint/current × T8/10/12六条原始记录；`trace_*`逐列保留选择像素、缺失、预测与灰度。`metadata.json`为冻结main原输出，`input_provenance.json`为独立原图SHA/点源/计时记录。
- `cpp_runs/<group>/<frame>/result.json`：独立native同一输入的六模式结果与完整trace。`traces[].trace`列顺序为x、selected_y、current_contrast、reference_new_darkening、joint_strength、is_observed、missing_run、predicted_y。
- `tables/all_results.csv`是Python准确率来源；`cpp_selected_accuracy.csv`另存原生选帧精度；`first_divergence_audit.csv`明确锁后浮点边界差异。不可假设所有native轨迹严格一致。
- `GrayRefCreate(reference,P1r/P2r)`复制参考；`GrayRefProcess(handle,current,P1c/P2c)`接收原图灰度和原始xy，当前点nullptr才按冻结NCC。返回0表示可读结果，仍需检查JSON status。`GrayRefRead`与`GrayRefArray`返回对象持有的临时内存，下一次process前复制；最终Destroy。没有正式observed承诺。

## 锁与中断记录

`freeze_manifest.json`、`parity_gate.json`、`validation_lock.json`分别为启动、开发parity和验证准入快照，不覆盖历史状态。验证两组Python首帧执行成功后，日志键重名中断；`validation_io_amendment.json`保留原/修复驱动SHA及首帧输出哈希，resume复用首帧结果。当时native验证尚未执行、验证标签未读。检测源码、DLL、参数和评估规则始终未改变。保留初始错误与恢复日志。

当前冻结V1源码diff为空；新源码单独记录在source_snapshot/research、new_source_manifest.json和implementation_additions.patch。最终完整性同时核对生产A和R05H封存结果。
