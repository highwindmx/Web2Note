import os
from PyQt5.QtWidgets import (QDialog, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QGridLayout)

class ImportDirs(QDialog):
    def __init__(self):
        super(ImportDirs, self).__init__()
        self.note_index_dir = "E:/Share/Note7Web/Index" # 数据索引
        self.note_root_dir = "E:/Share/Note7Web" # 数据存储
        self.note_cur_dir = "E:/Share/notebook/draft" # 导入库
        self.initDirlist = [self.note_index_dir, self.note_root_dir, self.note_cur_dir]
        self.setWindowTitle("请确认一下路径")
        self.initIF()

    def initIF(self):
        #interface_QW = QWidget(self)
        #self.setCentralWidget(interface_QW)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        
        class LabLineButton(QWidget):
            def __init__(self, interface, label, dir_index):
                super(LabLineButton, self).__init__()
                self.IF = interface
                self.label = label
                self.diridx = dir_index
                self.initLLB()
            
            def initLLB(self):
                self.layout = QGridLayout()
                self.setLayout(self.layout)
                self.import_LB = QLabel(self)
                self.import_LB.setText(self.label)                    
                self.import_LE = QLineEdit(self)
                self.import_LE.setMinimumWidth(200)
                self.import_LE.setText(self.IF.initDirlist[self.diridx])
                if not os.path.exists(self.IF.initDirlist[self.diridx]):
                    self.import_LB.setStyleSheet("color:Red")
                self.import_BT = QPushButton('更改',self)
                self.layout.addWidget(self.import_LB, 0,0, 1,1)
                self.layout.addWidget(self.import_LE, 0,1, 1,1)
                self.layout.addWidget(self.import_BT, 0,2, 1,1)
                self.import_BT.clicked.connect(self.click2ChangeDir)
            
            def click2ChangeDir(self):
                new_dir = QFileDialog().getExistingDirectory(self, "Open file", self.import_LE.text())
                self.import_LE.setText(new_dir)
                self.IF.initDirlist[self.diridx] = new_dir
     
        self.note_Index_Dir_LLB = LabLineButton(self, "数据库地址", 0)
        self.note_Root_Dir_LLB = LabLineButton(self, "笔记库地址", 1)
        self.note_Cur_Dir_LLB = LabLineButton(self, "导入库地址", 2)
        
        #self.create_BT = QPushButton('创建（关闭也会默认创建）',self)
        self.reset_BT = QPushButton('重置',self)
            
        self.layout.addWidget(self.note_Cur_Dir_LLB, 0,0, 1,1)
        self.layout.addWidget(self.note_Root_Dir_LLB, 1,0, 1,1)
        self.layout.addWidget(self.note_Index_Dir_LLB, 2,0, 1,1)
        #self.layout.addWidget(self.create_BT, 3,0, 1,2)
        self.layout.addWidget(self.reset_BT, 3,0, 1,1)               

        self.reset_BT.clicked.connect(self.click2ResetDirs)
        
    def click2ResetDirs(self):
        self.note_index_dir = "E:/Share/Note7Web/Index" # 数据索引
        self.note_root_dir = "E:/Share/Note7Web" # 数据存储
        self.note_cur_dir = "E:/Share/notebook/draft" # 导入库
        self.initDirlist = [self.note_index_dir, self.note_root_dir, self.note_cur_dir]
        i=0
        for llb in [self.note_Index_Dir_LLB, self.note_Root_Dir_LLB, self.note_Cur_Dir_LLB]:
            llb.import_LE.setText(self.initDirlist[i])
            i+=1
 