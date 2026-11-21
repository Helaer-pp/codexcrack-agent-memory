"""Prepare the verified Win64 SDK from the Release DLL and sealed per-frame comparisons."""
import csv
import hashlib
import json
import math
import shutil
import statistics
from itertools import groupby
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BUILD=ROOT/'output/build/v510_native/src/cpp/v510/Release'
VERIFY=ROOT/'output/verification/v510_native'
CV=ROOT/'third_party/opencv440'
RELEASE=ROOT/'output/releases/V5_10_Win64_OpenCV440'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text('utf-8-sig'))

def report():
    identity=digest(BUILD/'CrackV510.dll')
    assert load(VERIFY/'freeze.json')['dll_sha256']==identity
    source=ROOT/'output/experiments/v510_vertex_r02'
    totals=[0,0,0,0]
    body=['# V5.10 C++ 动态库回放验证',
          'Win64 Release，MSVC v142、OpenCV 4.4.0。直接从原始 BMP 和每帧实测 P1/P2 调用公开 C ABI。referenceResult 读缓存，Process 重新裁切及配准，路径从 DLL 拷出。Python 的既有 r02 预测仅用于计算差异。开发组A作为开发重放，验证组C和三点弯在二进制冻结后验证。排除组X排除。',f'**DLL SHA256** `{identity}`',
          '| 组别 | 点位 | 模式 | 帧数 | 状态相同 | 尖端相同 | 完整折线逐点相同 | 成对尖端最大差 px | 弧长最大差 px | 投影最大差 px | 平均耗时 ms | P95 ms |',
          '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    notes=[];selected=[];path_notes=[]
    for g,n in [('group_a',551),('three_point_bend',520),('group_c',562)]:
        sizes=(1 if g!='group_c' else 2)*2*n
        rows=list(csv.DictReader((VERIFY/(g+'_all.csv')).open(encoding='utf-8-sig')))
        assert len(rows)==sizes and all(r['dll']==identity for r in rows)
        scores=list(csv.DictReader((source/(g+'_scores.csv')).open(encoding='utf-8-sig')))
        gname={'group_a':'开发组A','three_point_bend':'三点弯','group_c':'验证组C'}[g]
        for (p,m),rs in groupby(sorted(rows,key=lambda r:(r['place'],r['mode'])),key=lambda r:(r['place'],r['mode'])):
            sub=list(rs);assert sorted(int(r['frame']) for r in sub)==list(range(1,n+1))
            counts=[len(sub)]+[sum(r[key]=='True' for r in sub) for key in ('status_equal','tip_equal','path_equal')]
            totals=[a+b for a,b in zip(totals,counts)]
            values=lambda k:[abs(float(r[k])) for r in sub if r[k]]
            err,arc,proj=[max(values(k),default=0) for k in ('error','arc_delta','proj_delta')]
            times=values('native_ms');p95=sorted(times)[math.ceil(.95*len(times))-1]
            body.append('| '+' | '.join(map(str,[gname,p,m,*counts,f'{err:.3f}',f'{arc:.6f}',f'{proj:.6f}',f'{statistics.mean(times):.2f}',f'{p95:.2f}']))+' |')
            different=[r for r in sub if r['path_equal']!='True']
            measured=[abs(float(r['max_column_y_delta'])) for r in different if r['max_column_y_delta']]
            if different:
                path_notes.append(f'- {gname} {p} / {m}，{len(different)} 条折线存在差异；其中 {len(measured)} 条起止列一致，逐列对应的最大纵向偏差为 {max(measured,default=0):g} px。')
            for r in sub:
                if r['tip_equal']!='True':notes.append(f"- {gname} {r['frame']}，{p} / {m}，Python {r['expected'] or '无尖端'}，C++ {r['actual'] or '无尖端'}，成对距离 {r['error'] or '—'} px。")
            if m=='full':
                labels={int(r['frame']):r for r in scores if r['stage']=='v5_10' and r['mode']==m and r['placement']==p and r['state']=='VISIBLE'}
                hit=identical=0
                for r in sub:
                    label=labels.get(int(r['frame']))
                    if not label:continue
                    identical+=r['path_equal']=='True'
                    if r['actual']:hit+=math.dist(json.loads(r['actual']),json.loads(label['gt']))<=10
                actual=list(csv.DictReader((VERIFY/'native_full_label_scores.csv').open(encoding='utf-8-sig')))
                checked=[r for r in actual if r['group']==g and r['place']==p and r['joint']]
                assert len(checked)==len(labels) and sum(r['hit10']=='True' for r in checked)==hit
                joint=sum(r['joint']=='True' for r in checked)
                selected.append(f'- {gname} {p}，C++ Hit@10 为 {hit}/{len(labels)}，C++ 路径与尖端联合命中 {joint}/{len(labels)}。与冻结版整条路径逐点相同 {identical}/{len(labels)}。')
    paragraphs=body[:3]+['\n'.join(body[3:]),
        f'共 {totals[0]} 次回放，状态一致 {totals[1]}，尖端一致 {totals[2]}，整条折线逐点一致 {totals[3]}。状态与尖端的一致数包含双方同时无尖端。弧长、投影与欧氏误差的最大值只统计成对有效输出。C++ 速度为原图已解码、4 个 OpenCV 线程时的 Process 调用耗时，含上游配准。Python 上轮报告的缓存 ROI 计时范围不同。','## 标注可见帧','\n'.join(selected),
        '## 尖端差异','\n'.join(notes) if notes else '所有被测输入的尖端一致。逐帧 CSV 的 path_equal、arc_delta 与 max_column_y_delta 可定位内部折线差异，正负弧长差以 C++ 减 Python 计。',
        '## 内部折线差异','\n'.join(path_notes) or '全部折线相同。', 'C++ 的图像算子采用 OpenCV 4.4，沿路径保留 float 累计状态。现有证据能确定差异的帧及像素范围，尚未逐帧定位首个出现数值分歧的算子。', '## 接口与依赖','通过带步长图像、错误点序、空点对、空结果、错误结构体尺寸、短缓冲区、最近路径及基准结果缓存检查。原生依赖见 dependencies.txt，导出函数见 exports.txt。精度和泛化限制参见项目 evidence/v5_10/REPORT.md。']
    (VERIFY/'REPORT.md').write_text('\n\n'.join(paragraphs)+'\n','utf8')
    return totals

def stage():
    for directory in ('bin','lib','include','example','verification'):
        (RELEASE/directory).mkdir(parents=True,exist_ok=True)
    for p in ['CrackV510.dll','CrackV510Example.exe','opencv_world440.dll']:shutil.copy2(BUILD/p,RELEASE/'bin'/p)
    shutil.copy2(BUILD/'CrackV510.lib',RELEASE/'lib')
    shutil.copy2(CV/'lib/opencv_world440.lib',RELEASE/'lib')
    shutil.copytree(CV/'include/opencv2',RELEASE/'include/opencv2',dirs_exist_ok=True)
    for p in ('CrackV510.h','CrackV510.hpp'):shutil.copy2(HERE/p,RELEASE/'include')
    shutil.copy2(HERE/'example.cpp',RELEASE/'example');shutil.copy2(HERE/'SDK.cmake',RELEASE/'CMakeLists.txt')
    shutil.copy2(CV/'LICENSE',RELEASE/'OpenCV-LICENSE.txt');shutil.copy2(HERE/'集成说明.md',RELEASE)
def main():
    counts=report();stage()
    for p in ['REPORT.md','freeze.json','abi_checks.txt','dependencies.txt','exports.txt','native_full_label_scores.csv','group_a_all.csv','three_point_bend_all.csv','group_c_all.csv']:
        shutil.copy2(VERIFY/p,RELEASE/'verification')
    files=sorted(p for p in RELEASE.rglob('*') if p.is_file() and p.name!='SHA256.txt')
    (RELEASE/'SHA256.txt').write_text(''.join(f'{digest(p)}  {p.relative_to(RELEASE).as_posix()}\n' for p in files),'utf8')
    with ZipFile(RELEASE.with_suffix('.zip'),'w',ZIP_DEFLATED,compresslevel=6) as z:
        for p in [*files,RELEASE/'SHA256.txt']:z.write(p,p.relative_to(RELEASE))
    with ZipFile(RELEASE.with_suffix('.zip')) as z:assert z.testzip() is None
    print(counts, RELEASE.with_suffix('.zip'))
if __name__=='__main__':main()
