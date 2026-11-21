# C 研究 V3 测量合同

P1/P2 必须为当前原图同一物理点，P1在上/P2在下。O=(P1+P2)/2，v=(P2-P1)/d，u=(v_y,-v_x)。horizontal_length_px=(T-O)·u。零值是在线上的有效点；负侧不支持，valid=false。无尖端时坐标/投影是null，不能算作真实0。兼容展示可显示0但附valid。

tip_valid 与 root_valid/path_valid/legacy_arc_valid 独立。路径可以是辅助搜索路径或尖端一致子段，不能把根部失效、缺失完整路径、A未确认、shadow未确认或差分未知作为尖端单项否决。现有A的弧长保持原语义，不改名冒充投影。A只提供路径候选，不向C传入GT/试件名/帧号/文件名。C关闭即回退A调用方；C不修改A对象或历史。

灰度编码只接受GRAY8全范围255和GRAY16全范围65535，统一转8-bit等效浮点单位；其他编码显式INVALID_INPUT。A只支持8位，16位输入的A基线由固定round(code/257)适配器生成，非A内部改动。无标定不输出mm。目标是当前图像可观察端点；形成尖端另列，物理真实精度N/A，相位PHASE_UNKNOWN。

C_BASE是独立研究系统基线：固定锚点带、固定线宽/噪声、光度关闭、仅A末端候选与共同独立前方审计。C_ROI/C_SCALE/C_NOISE/C_PHOTO/C_TIP分别只改一项；C_FULL全开。它们相对C_BASE是模块对照，相对原生A仅是系统对照，不能冒称无损替换A内部ROI/评分的因果消融。
