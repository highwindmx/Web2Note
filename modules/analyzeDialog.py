import os
from PyQt5.QtWidgets import (QDialog, QWidget, QLabel, QGridLayout)
from PyQt5.QtGui import QPixmap, QImage 
from wordcloud import WordCloud
import jieba

class Analysis(QDialog):
    def __init__(self, mainwin):
        super().__init__()
        self.main_Win = mainwin
        # self.note_index_dir = "E:/Share/Note7Web/Index" # 数据索引
        # self.note_root_dir = "E:/Share/Note7Web" # 数据存储
        # self.note_cur_dir = "E:/Share/notebook/draft" # 导入库
        # self.initDirlist = [self.note_index_dir, self.note_root_dir, self.note_cur_dir]
        # self.setWindowTitle("请确认一下路径")
        self.initIF()

    def initIF(self):
        #interface_QW = QWidget(self)
        #self.setCentralWidget(interface_QW)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        
        self.info1_LB = QLabel(self)
        self.info1_LB.setText("笔记库共含{}条笔记，末次更新时间为：{}".format(self.main_Win.note_index.data.shape[0]
                                                                             ,self.main_Win.note_index.getUpdateTime().strftime("%Y-%m-%d %H:%M:%S")))
        self.info2_LB = QLabel(self)
        self.info2_LB.setText("笔记加载文件夹：{}".format(self.main_Win.note_cur_dir))
        self.info3_LB = QLabel(self)
        self.info3_LB.setText("笔记索引文件夹：{}".format(self.main_Win.note_index_dir))
        self.info4_LB = QLabel(self)
        self.info4_LB.setText("笔记库根文件夹：{}".format(self.main_Win.note_root_dir))
        self.info5_LB = QLabel(self)
        tb = self.main_Win.note_index.data["keywords"]
        text = "/".join(jieba.cut(" ".join(tb)))
        wordcloud = WordCloud(background_color="white", font_path="./style/GenWanMinTW-Regular.ttf", margin=2).generate(text)
        wordcloud.to_file("./style/wordcould.png") #还是直接用文件的形式比较方便
        self.info5_LB.setPixmap(QPixmap("./style/wordcould.png"))
        # self.info4_LB.setPixmap(QPixmap.fromImage(wordcloud.to_image()))
        # self.layout.addWidget(self.info0_LB, 0,0, 1,1)  
        self.layout.addWidget(self.info1_LB, 0,0, 1,1)
        self.layout.addWidget(self.info2_LB, 1,0, 1,1)
        self.layout.addWidget(self.info3_LB, 2,0, 1,1)
        self.layout.addWidget(self.info4_LB, 3,0, 1,1)
        self.layout.addWidget(self.info5_LB, 4,0, 1,1)
        
        
 