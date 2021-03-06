import os
from PyQt5.QtGui import (QIcon, QPixmap)
from PyQt5.QtWidgets import (QDialog, QWidget, QLabel, QLineEdit
                            ,QPushButton, QRadioButton, QButtonGroup, QFileDialog, QGridLayout)

class ImportDirs(QDialog):
    def __init__(self):
        super(ImportDirs, self).__init__()
        self.setWindowTitle("请确认以下目录是否正确，没错的话关掉就好")
        self.initIF()

    def initIF(self):
        #interface_QW = QWidget(self)
        #self.setCentralWidget(interface_QW)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        icon = QIcon()
        icon.addPixmap(QPixmap("./style/logo3.png"))
        self.setWindowIcon(icon)
        
        self.switch_Config_PC1_RB = QRadioButton("PC1")
        self.switch_Config_PC1_RB.setChecked(True)
        self.switch_Config_PC1_RB.toggled.connect(self.toggle2SetPath)
        self.switch_Config_PC2_RB = QRadioButton("PC2")
        self.switch_Config_PC2_RB.toggled.connect(self.toggle2SetPath)
        self.switch_Config_BG = QButtonGroup()
        self.switch_Config_BG.addButton(self.switch_Config_PC1_RB)
        self.switch_Config_BG.addButton(self.switch_Config_PC2_RB)
        
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
                #
                self.import_BT = QPushButton('更改',self)
                self.layout.addWidget(self.import_LB, 0,0, 1,1)
                self.layout.addWidget(self.import_LE, 0,1, 1,1)
                self.layout.addWidget(self.import_BT, 0,2, 1,1)
                self.import_BT.clicked.connect(self.click2ChangeDir)
            
            def click2ChangeDir(self):
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog #啃爹啊，5.12的文档中是DontUseNativeDialogs，少个s
                options |= ~QFileDialog.ShowDirsOnly # 还是得活学活用才行 
                new_dir = QFileDialog.getExistingDirectory(self, "选择目录", self.import_LE.text(), options=options)
                #就是这个非NativeDialog加载的又慢，长得又难看，。。。-_-|| 为了搞个能同时显示文件夹directory和文件file的FileDialog也是醉了
                self.import_LE.setText(new_dir)
                self.IF.dir_list[self.diridx] = new_dir
     
        self.note_Index_Dir_LLB = LabLineButton(self, "数据库地址", 0)
        self.note_Root_Dir_LLB = LabLineButton(self, "笔记库地址", 1)
        self.note_Cur_Dir_LLB = LabLineButton(self, "导入库地址", 2)
        self.toggle2SetPath()
        
        #self.create_BT = QPushButton('创建（关闭也会默认创建）',self)
        self.reset_BT = QPushButton('重置',self)
        self.reset_BT.clicked.connect(self.click2ResetDirs)
        
        self.layout.addWidget(self.switch_Config_PC1_RB, 0,0, 1,1)    
        self.layout.addWidget(self.switch_Config_PC2_RB, 0,1, 1,1)
        self.layout.addWidget(self.note_Cur_Dir_LLB, 1,0, 1,2)
        self.layout.addWidget(self.note_Root_Dir_LLB, 2,0, 1,2)
        self.layout.addWidget(self.note_Index_Dir_LLB, 3,0, 1,2)
        #self.layout.addWidget(self.create_BT, 3,0, 1,2)
        self.layout.addWidget(self.reset_BT, 4,0, 1,2)               
    
    def showPath(self):
        i=0
        for llb in [self.note_Index_Dir_LLB, self.note_Root_Dir_LLB, self.note_Cur_Dir_LLB]:
            llb.import_LE.setText(self.dir_list[i])
            if not os.path.exists(self.dir_list[i]):
                llb.import_LB.setStyleSheet("color:Red")
            else:
                llb.import_LB.setStyleSheet("color:Green")
            i+=1
    
    def toggle2SetPath(self):
        if self.switch_Config_PC1_RB.isChecked():
            self.note_index_dir = "E:/Share/Note7Web/Index" # 数据索引
            self.note_root_dir = "E:/Share/Note7Web" # 数据存储
            self.note_cur_dir = "E:/Share/notebook/draft" # 导入库
        else:
            self.note_index_dir = "D:/Share/Note7Web/Index" # 数据索引
            self.note_root_dir = "D:/Share/Note7Web" # 数据存储
            self.note_cur_dir = "D:/Share/notebook/draft" # 导入库
        self.dir_list = [self.note_index_dir, self.note_root_dir, self.note_cur_dir]
        self.showPath()
        
    def click2ResetDirs(self):
        self.toggle2SetPath()
        #self.setPath()
        # if self.switch_Config_PC1_RB.isChecked():
        #     self.note_index_dir = "E:/Share/Note7Web/Index" # 数据索引
        #     self.note_root_dir = "E:/Share/Note7Web" # 数据存储
        #     self.note_cur_dir = "E:/Share/notebook/draft" # 导入库
        # else:
        #     self.note_index_dir = "D:/Share/Note7Web/Index" # 数据索引
        #     self.note_root_dir = "D:/Share/Note7Web" # 数据存储
        #     self.note_cur_dir = "D:/Share/notebook/draft" # 导入库    
        # self.dir_list = [self.note_index_dir, self.note_root_dir, self.note_cur_dir]
        # i=0
        # for llb in [self.note_Index_Dir_LLB, self.note_Root_Dir_LLB, self.note_Cur_Dir_LLB]:
        #     llb.import_LE.setText(self.dir_list[i])
        #     i+=1
 