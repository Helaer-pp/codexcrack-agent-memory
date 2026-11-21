"""Exercise the actual pinned LabelMe Qt loader, without saving annotations."""
import os,sys,collections
from common import *
from annotation_qc import validate

def main():
 os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['QT_API']='pyqt5';sys.path.insert(0,str(LABELME))
 import labelme,yaml
 from qtpy import QtWidgets,QtCore
 from labelme.app import MainWindow
 QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
 QtCore.QSettings.setPath(QtCore.QSettings.IniFormat,QtCore.QSettings.UserScope,str(OUT/'qt_settings'))
 QtCore.QSettings.setPath(QtCore.QSettings.IniFormat,QtCore.QSettings.SystemScope,str(OUT/'qt_settings'))
 cfg=yaml.safe_load((LABELME/'labelme/config/default_config.yaml').read_text());cfg.update(yaml.safe_load((PACKAGE/'labelme_config.yaml').read_text()))
 app=QtWidgets.QApplication([]);window=MainWindow(config=cfg);window.resize(1280,900);window.show();opened=[];groups=set()
 for r in rows(PACKAGE/'selection_manifest.csv'):
  p=PACKAGE/r['selected_json'];before=sha(p);window.loadFile(str(p));app.processEvents()
  assert not window.image.isNull() and window.image.width()==int(r['image_width']) and window.image.height()==int(r['image_height'])
  assert window.labelFile is not None and len(window.canvas.shapes)==0 and not window.dirty
  assert sha(p)==before
  if r['dataset_id'] not in groups:window.grab().save(str(OUT/f"labelme_open_{r['dataset_id']}.png"));groups.add(r['dataset_id'])
  opened.append(dict(dataset_id=r['dataset_id'],frame_id=r['frame_id'],json=r['selected_json'],real_labelme_load=True,dimensions_correct=True,empty_shapes=True))
 save(OUT/'labelme_open_validation.csv',opened);progress=validate(PACKAGE,True)
 summary=json.loads((OUT/'inventory_summary.json').read_text());inv=rows(OUT/'input_inventory.csv')
 (OUT/'data_quality_report.md').write_text('# 原图与点映射盘点\n\n'+ '\n'.join(f"- {r['dataset_id']}: {r['decoded']}/{r['listed']} 可解码，唯一哈希 {r['unique_sha']}，尺寸 {r['image_sizes']}；{r['point_mapping']}。" for r in summary)+f"\n\n总计 {len(inv)} 张，非法点 {sum(r['p1p2_valid']!='True' for r in inv)}，精确重复 {sum(r['duplicate_exact']=='True' for r in inv)}。六组原点文件 num 与 manifest 逐帧一致；CT3 仅冻结 CSV 显式文件名/坐标映射，独立原始跟踪文件 NOT_AVAILABLE。固定参考均是各序列 frame_order=0；后续算法只在 t>0 使用该参考。原文件名数字不直接用作帧号。无物理载荷同步，实际裂纹阶段 UNKNOWN。源数据为供应清单的完整原图，已核对哈希，不声称能从像素证明拍摄前不存在任何预处理。\n",encoding='utf8')
 report=f'''# LabelMe 标注包 QA

- PASS：{len(progress)} 张原图，7 组各20张，15 development / 5 holdout。
- PASS：源 SHA256 一致、原分辨率不变、主标注图无重复源 SHA；参考副本单独存放。
- PASS：140 个 JSON 的 shapes=[]、flags={{}}，未预填尖端、路径或无裂纹结论。
- PASS：实际 LabelMe {labelme.__version__} MainWindow.loadFile + Qt 图像/canvas 加载全部 {len(opened)} 个 JSON；不是仅 JSON 解析。离屏窗口逐组截图在运行目录 labelme_open_*.png，未触发保存。
- PASS：便携 annotation_qc.py 检查所有图像/JSON、尺寸、split 和坐标；当前全部 UNANNOTATED。
- 标注集全部来自曝光序列，holdout 不是独立泛化证据。物理阶段尚待人工确认。
'''
 (PACKAGE/'annotation_qc_report.md').write_text(report,encoding='utf8');(OUT/'annotation_qc_report.md').write_text(report,encoding='utf8')
 write(OUT/'annotation_qa.json',dict(status='PASS',actual_labelme_version=labelme.__version__,actual_qt_load_count=len(opened),unannotated=len(progress)))
 print('REAL LABELME OPEN QA PASS',len(opened),flush=True)

if __name__=='__main__':main()
