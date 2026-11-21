# 第五组：NOT_RUN_GATED

本轮没有读取第五组manifest、原图或逐帧结果，没有生成第五组伪视频/空数据冒充验证。只把此前已曝光frame_id=51/473和超时事实作为历史风险披露。它本来就不属于严格从未接触的盲测；真正外部泛化需要未曝光第六组。

任务书第6节明确要求：“在 freeze_manifest.json 生成且通过 DEV-4 内部准入后，才执行排除组X全序列。”本次H3有合成假尖端、弱/弯裂纹退化，且CT2 K2/K3有超时，DEV-4准入失败。因此冻结的是不可发布研究实物，未授权自身绕过这项门槛执行第五组。第10节要求的M6–M8亦未继续叠加。

51/473复核：NOT_RUN_GATED；第五组逐帧Process、精度、视频和PNG：未生成，非N/A伪成功。config/manifest_final5.json仅为显式未打开的状态说明，不含试验图像路径清单。访问声明见tests/final5_access_log.json，脚本路径白名单见source/tests/joint_common.py。
