# 构建与复现

工作目录 `.`。已实际执行的各阶段日志在logs/，V1原生每帧CSV/stdout/stderr在frames/*/*/v1/，G0未修改CLI输出在gate0/。完整新编排仅做语法和路径检查；没有为测试编排再重复全部2647帧，但每个实际阶段均已执行，独立Python CLI另有cli_smoke/与命令日志。

```powershell
Set-Location .
& ./research/p1p2_grayref_v2/reproduce.ps1 -Output './output/experiments/p1p2_grayref_v2_replay01'
```

源码快照python_v2/包含完整脚本及其C++构建依赖，也可从该目录调用reproduce.ps1。输出必须为全新ASCII项目output子目录。python_v2/和cpp_v2/的C++文件是相同源码副本；活动源码在research/p1p2_grayref_v2/。不执行旧封存代码；旧结果只供身份/回放比较。不要指向本轮封存目录。

实际构建：`build.ps1 -Output <新目录>/cpp_build`，内部调用CMake、Visual Studio17 2022、x64、v142。真正DLL是cpp_build/Release/GrayRefV2.dll；GrayRefV2_Research_SDK.zip包含DLL/导入库/头文件/OpenCV依赖及许可。native_v2.py是C ABI调用桥，不承担检测计算。

算法推理接口`detect(R,C,rp,cp)`只接收原始uint8图像和四点。无标签、组名、帧名或历史参数。独立CLI参数见python_v2/cli.py --help；P1/P2必须是实际当前帧点。C接口GrayRefV2Create/Process/Read/Array/Destroy，线程与指针寿命见README及头文件。

依赖使用config/project.json现有Python和工具链；完整实测版本见environment_versions.json。requirements.txt是现有环境快照，不是已验证的全新pip解析锁：OpenCV4.12轮子声明NumPy>=2，而本机1.26.4组合已经完成全部实测；不自动安装或覆盖现有环境。字体使用Windows微软雅黑。新机器环境重建与目标i7性能未验证。

原始F盘图像、逐帧点、旧V1回放、标签快照必须仍可读；不写回原图/标签。开发组和验证组顺序固定，标签仅分组全部推理后读取。新跑仍属已曝光回归，不自动变为盲测。单次API调用耗时、Python桥耗时和视频8fps不是同一个指标。
