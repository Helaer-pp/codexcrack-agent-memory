"""Summarize replay against the V5.12 frozen paths and compatibility evidence."""
from .verify_abi import BUILD,DEST,batch

def main():
    names={'group_a':'开发组A','three_point_bend':'三点弯','group_c':'验证组C亮区'}
    lines=['# V5.12 原生 DLL 交付验证','','Windows x64 / Release / MSVC 19.43 / OpenCV 4.4.0。运行文件为 CrackV4.dll。原始 SDK 的 19 个导出名与序号全部保留，另外保留新版 SDK 的两个按名称调用的路径段接口。原版头文件与导入库约定均可沿用。','','| 数据 | 回放帧 | 状态及尖端相同 | 整条折线逐点相同 | 最大同列纵向差 px | 最大弧长差 px |','| --- | ---: | ---: | ---: | ---: | ---: |']
    total=valid=exact=0
    for g,name in names.items():
        rows=batch.read_csv(DEST/(g+'_all.csv'))
        assert len(rows)==batch.GROUPS[g]
        diff=batch.read_csv(DEST/(g+'_path_delta.csv'))
        assert len(diff)==sum(r['same_path']=='False' for r in rows)
        same=sum(r['same_tip']=='True' for r in rows); paths=sum(r['same_path']=='True' for r in rows)
        gap=max([int(r['max_y']) for r in diff if r['max_y']]+[0])
        arc=max([abs(float(r['arc_delta'])) for r in diff]+[0.])
        lines.append(f'| {name} | {len(rows)} | {same} | {paths} | {gap} | {arc:.6f} |')
        total+=len(rows);valid+=same;exact+=paths
        other=[r for r in diff if r['same_columns']=='False']
        if other:lines.append('')
    lines+=['',f'共 {total} 帧，{valid} 帧尖端及有无确认结果一致，{exact} 帧整条路径完全相同。各组均对实际 DLL 返回的路径独立累加欧氏弧长、检查观测段弧长及毫米换算。逐帧证据见本目录 CSV。','',
        '处理顺序按单序列单句柄进行。验证组C回放启用冻结的亮区操作员配置并传入原始采集点对；其他两组使用默认模式。三组均使用同一 DLL。V5.12 的研究验收结论与原生移植的一致性分别评估，三点弯 248 仍是已知失败帧。','',
        '兼容性实测包括已有 A 版示例 EXE 直接加载、使用最初四个头文件重新编译原始 C++ 示例、GRAY8 带行填充输入、缺省当前点自动估计、纯缓存基线查询、错误 struct_size 和 stride、三种参考模式以及标定换算。开发组A 299 的旧程序得到尖端 (1248, 1160)、长度 319.874726 px（0.025 mm/px 时为 7.99686815 mm）。','',
        '原 DLL 的算法专属时序/质量计数与 V5.12 的判定含义有差异。V5.12 使用单帧路径证据；集成方读取有效标志后再使用坐标和长度。','',
        'DLL SHA-256 为 `'+batch.sha(BUILD/'CrackV4.dll')+'`。']
    (DEST/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(total,valid,exact)
if __name__=='__main__':main()
