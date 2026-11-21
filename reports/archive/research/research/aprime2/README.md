# A′2 独立研究

运行结果：`output/runs/aprime2_20261105_r01`。结论KEEP_A。生产源/DLL未改。

`native_bridge.py`对照冻结库与独立旁路；`candidates.py`不读参考/GT生成K≤12候选；`reference.py`提供旧阈值下的局部几何/光度及最多3×48块区间查询；`decision.py`比较H_STOP/H_CONTINUE并检查有限扰动；`dev.py`生成全新材料过程的曝光DEV；GT仅供生成器和离线评价器使用。

`prefilter=False`保留v2实验，显式`--prefilter`运行v3；后者前移patch有效比例筛选，避免无效高对比角点挤占预算。不能因为参考覆盖提高就声称尖端更准。两版均没有通过跨场景参考门槛。原生完整候选/参考/决策尚未实现。

复现命令与未执行项详见运行目录`reproduce.md`和`09_reports/development_report.md`。设置`CRACK_AP2_RUN`使用新输出目录。所有脚本在CodexCrack根目录执行，禁止修改封存生产A或外部原图。
