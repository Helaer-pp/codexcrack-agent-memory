"""Open the human annotation working copy using the isolated LabelMe install."""
from pathlib import Path
import os,sys,csv

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'output/runs/uctt_r05_prelabel_difference_20261111_r01'
PACKAGE=RUN/'R05_LabelMe_Annotation_Package'
LIB=ROOT/'output/toolchains/labelme_5_2_1'
sys.dont_write_bytecode=True
sys.path.insert(0,str(LIB))
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4.dataset_policy import filter_rows
os.environ['QT_API']='pyqt5'
os.environ['QT_QPA_PLATFORM']='windows'
import yaml
from qtpy import QtWidgets,QtCore,QtGui
from labelme.app import MainWindow

def main():
 settings=ROOT/'output/annotation_session/qt_settings';settings.mkdir(parents=True,exist_ok=True)
 QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
 for scope in [QtCore.QSettings.UserScope,QtCore.QSettings.SystemScope]:
  QtCore.QSettings.setPath(QtCore.QSettings.IniFormat,scope,str(settings))
 cfg=yaml.safe_load((LIB/'labelme/config/default_config.yaml').read_text(encoding='utf8'))
 cfg.update(yaml.safe_load((PACKAGE/'labelme_config.yaml').read_text(encoding='utf8')))
 app=QtWidgets.QApplication(sys.argv);app.setFont(QtGui.QFont('Microsoft YaHei UI',10))
 active=filter_rows(list(csv.DictReader((PACKAGE/'selection_manifest.csv').open(encoding='utf-8-sig'))),'annotation_qc',uses_annotations=True)
 window=MainWindow(config=cfg)
 QtCore.QTimer.singleShot(0,lambda:window.importDroppedImageFiles([str(PACKAGE/r['selected_image']) for r in active]))
 window.showMaximized()
 # Do not create, copy, or save any annotations on launch.
 sys.exit(app.exec_())

if __name__=='__main__':main()
