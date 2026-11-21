# B4 光度合同未完成：仅原型，不具备决策资格

代码审计补充：quality()验证的是材料分区残差一致性；它虽记录各patch offset/sigma并排除明显局部新异，未建立统一的独立光度有效性判据。conditional_dg.py读取的是new_dark_uncorrected，>=5码及当前暗谷+几何一致性便标SUPPORTED；该原型状态不能等同于任务书要求的“配准与光度均已验证的D/G支持”。全局曝光或局部光度变化仍可能混入变化量。

因此B4严格状态为PROTOTYPE_ONLY / PHOTOMETRY_NOT_VALIDATED；保留原冻结结果供审计，不能把原始CSV中的DG_state=SUPPORTED解释为验证通过的物理或差分证据。CONTRADICTED从未建立，B5仍禁用，未修改任何A尖端。B0/B1/B2只读诊断已完成；B3停止假设为研究导出，H_ALT/H_EXTEND跳过；完整B4决策合同未完成。本轮不是完成了可用的D/G融合版本。

这是冻结代码的合同审计结论，不在已看TEST上修阈值。下一轮若要将D/G证据用于候选排序，必须先在独立DEV建立光度有效性及UNKNOWN规则，再冻结新的TEST。本轮最终决策KEEP_A不变。
