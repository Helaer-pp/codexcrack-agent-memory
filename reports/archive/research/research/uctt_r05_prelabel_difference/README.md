# R05-PRE：原图标注与因果参考差分

研究目录不导入生产检测器、不修改ABI、不产生伪GT。运行产物统一在 `output/runs/uctt_r05_prelabel_difference_20261111_r01`；原图在F盘只读。现有运行已交付，复现应先把 `common.py` 中 OUT 改为新的唯一输出目录，不能覆盖已交给用户的JSON。

项目根目录 PowerShell 命令（依次执行）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$py='D:/ProgramData/anaconda3/python.exe'
& $py research/uctt_r05_prelabel_difference/inventory_sources.py
& $py research/uctt_r05_prelabel_difference/select_annotation_frames.py
& $py research/uctt_r05_prelabel_difference/build_labelme_package.py
& $py research/uctt_r05_prelabel_difference/validate_labelme_package.py
& $py research/uctt_r05_prelabel_difference/package_delivery.py
# 此时先交付标注包，不等差分实验结束。
& $py research/uctt_r05_prelabel_difference/test_contracts.py
& $py research/uctt_r05_prelabel_difference/test_annotation_import.py
& $py research/uctt_r05_prelabel_difference/compare_reference_arms.py
& $py research/uctt_r05_prelabel_difference/evaluate_after_annotation.py
& $py research/uctt_r05_prelabel_difference/report_results.py
& $py research/uctt_r05_prelabel_difference/render_comparison_gallery.py
& $py research/uctt_r05_prelabel_difference/render_video.py
```

LabelMe 5.2.1、termcolor 3.3.0 被隔离安装在 `output/toolchains/labelme_5_2_1`，复用已安装PyQt5/qtpy/imgviz/Pillow；没有改系统Python或下载AI模型。若工具目录不存在，使用 `pip install --no-deps --no-cache-dir --no-compile --target output/toolchains/labelme_5_2_1 labelme==5.2.1 termcolor==3.3.0`；TEMP/TMP应指向项目output内。QA直接加载默认yaml再传MainWindow，避开LabelMe自动写用户主目录配置，Qt设置也在output内。官方格式来源：https://github.com/wkentaro/labelme/tree/v5.2.1 。

主程序共享同一规则，无按试件调阈值。全序列只用于离线原图抽样；在线候选API只能接收已出现的历史。候选原图按需从只读文件读取，解码LRU上限8图；历史元数据默认64条，上限4候选。第一帧不和自身做历史差分。配准质量失败不会填0指标。

合成软件测试在独立 `synthetic_annotation_qc` 文件夹，不进入用户包。真正的人工作业目录是 `R05_LabelMe_Annotation_Package/images`。报告与HTML/视频全部明确“诊断，不是GT”。

人工标签回来后默认只评价development：`evaluate_after_annotation.py --package <包目录>`。若要评价holdout，必须显式传 `--include-holdout --locked-rules-sha <global_rules.json的SHA256>`；在调参前保存锁定版本，禁止据holdout再调规则。可选 `--predictions <CSV>` 要求 dataset_id,frame_id,x,y,valid,output_type；只评observed点误差，predicted/fallback不冒充观测。没有预测时点准确率N/A，仍可评路径容差带与干扰激活。真实无标签时只输出AWAITING_MANUAL_ANNOTATION。

CSV缺失数值为空字段，JSON为null。所有面积/残差是统一缩放ROI内的代理；原图坐标映射保存在每案例NPZ。C0/C1残差使用四臂公共交集（分母ablation_common_pixel_count）；E1/E2主指标使用两臂公共交集。quality_status指E1/E2基本配对可用性，消融是否可用仍需检查ablation分母。几何稳定条带未经人工验证，不能假定不存在裂纹。中央过渡带排除可能损失真实路径，必须等标注后量化。

性能是Python研究计时，不是i7 DLL ≤50ms验收。当前结论保留生产A、等待真实标注，不进入正式R05生产开发。
