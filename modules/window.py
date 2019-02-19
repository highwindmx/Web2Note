import os
# import time
import uuid
from datetime import datetime
import pathlib

from PyQt5.QtCore import (pyqtSignal, Qt, QUrl, QSize, QPoint, QThread, QEventLoop, QFileInfo, QRect, QDate)
from PyQt5.QtGui import (QIcon, QCursor, QColor, QFont, QDesktopServices,QStandardItemModel) # QPainter,
from PyQt5.QtWidgets import (qApp, QMainWindow, QWidget
                            ,QListWidget, QListWidgetItem, QTabWidget, QCalendarWidget
                            ,QLabel, QLineEdit, QPlainTextEdit, QTextBrowser, QProgressBar, QProgressDialog
                            ,QButtonGroup, QPushButton, QRadioButton, QCheckBox, QComboBox
                            ,QMenu, QFileDialog, QMessageBox, QAction, QFileIconProvider
                            ,QLayout, QGridLayout, QSplitter, QListView
                            ,QSizePolicy,  # QDesktopWidget, QApplication, 
                            )
from PyQt5.QtWebEngineWidgets import QWebEngineView
from .db import (NoteIndex, NotePack)
from .analyzeDialog import Analysis

class MainWindow(QMainWindow):
    onHtmlGot = pyqtSignal() # 不要动它，答案见：https://stackoverflow.com/questions/48386253/save-html-files-in-qwebengineview-browser
    def __init__(self, lst):
        super().__init__()
        # 构建窗体
        self.setWindowTitle("我的笔记本") # 在这里设置窗口标题
        self.setGeometry(60, 60, 1120, 630) # 在这里设置窗口位置和大小
        self.setContentsMargins(0, 0, 0, 0)
        # 
        self.ctr_showHide_left_panel = 0 # 初始化显隐左侧栏的计数
        self.ctr_showHide_right_panel = 0 # 初始化显隐右侧栏的计数
        # 载入初始值
        self.setDataDirList(lst)
        #print(self.data_index_dir, self.note_root_dir, self.note_cur_dir)
        self.initUI()
        
    def initUI(self): # 加载UI
        # 菜单栏
        self.menu_Bar = self.menuBar()
        self.menu_Bar_File = self.menu_Bar.addMenu('程序')
        menu_Bar_File_Exit_AC = QAction(QIcon("./style/logo3.png"), '退出', self)
        # menu_Bar_File_Exit_AC.setShortcut('Ctrl+Q')
        self.menu_Bar_File.addAction(menu_Bar_File_Exit_AC)
        
        self.menu_Bar_Reload = self.menu_Bar.addMenu('重载')
        menu_Bar_Reload_Import_AC = QAction(QIcon("./style/logo3.png"), '&导入笔记目录', self) # 这个&是干啥用的？？？？？？
        menu_Bar_Reload_All_AC = QAction(QIcon("./style/logo3.png"), '重载所有的笔记', self)
        menu_Bar_Reload_New_AC = QAction(QIcon("./style/logo3.png"), '重载更新的笔记', self)
        self.menu_Bar_Reload.addAction(menu_Bar_Reload_Import_AC)
        self.menu_Bar_Reload.addAction(menu_Bar_Reload_All_AC)
        self.menu_Bar_Reload.addAction(menu_Bar_Reload_New_AC)
        
        self.menu_Bar_Analyze = self.menu_Bar.addMenu('分析')
        menu_Bar_Analyze_Stt_AC = QAction(QIcon("./style/logo3.png"), '统计', self)
        self.menu_Bar_Analyze.addAction(menu_Bar_Analyze_Stt_AC)

    # 主窗体
        central_QW = QWidget(self)
        self.setCentralWidget(central_QW)
        self.layoutMainGrid = QGridLayout() # 这里（）不能加self，不然会出现错误：Attempting to add QLayout , which already has a layout
        central_QW.setLayout(self.layoutMainGrid)
        self.panels_SP = QSplitter(Qt.Horizontal)
        
        # 左侧板块
        self.left_Panel_QW = QWidget(self)
        self.layoutLeftGrid = QGridLayout()
        self.layoutLeftGrid.setContentsMargins(0,0,0,0)
        self.left_Panel_QW.setLayout(self.layoutLeftGrid) # 注意：好像只能widget set layout不能add layout，而layout可以add widget        
        # 加入搜索栏
        self.search_QW = QWidget(self)
        self.layoutSearch = QGridLayout()
        self.layoutSearch.setContentsMargins(0,0,0,0)
        self.search_QW.setLayout(self.layoutSearch)
        # -检索输入框
        self.search_Input_QW = QPlainTextEdit(self)
        self.search_Input_QW.setObjectName("search_Input_QW")
        self.search_Input_QW.setStyleSheet("font: 12pt;")
        self.search_Input_QW.setPlaceholderText("请按行输入查询关键词") 
        self.search_Input_QW.setMaximumHeight(140) # 这是主要影响左边高度分配的值
        # -与或选择
        self.search_And_RBT = QRadioButton("与", self)
        self.search_Or_RBT = QRadioButton("或",self)
        self.search_andOr_BG = QButtonGroup(self)
        self.search_andOr_BG.addButton(self.search_And_RBT, 0) # 注意与后边self.search_andOr_BG.checkedId()对应
        self.search_andOr_BG.addButton(self.search_Or_RBT, 1)
        self.search_Or_RBT.setChecked(True)
        # -大小写敏感
        self.search_caseSense_CB = QCheckBox("大小写\n敏感")
        # -检索按钮
        self.search_BT = QPushButton('检索',self)
        self.search_BT.setObjectName("search_BT")
        self.search_BT.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        # -重置按钮
        self.search_Reset_BT = QPushButton('重置',self)
        self.search_Reset_BT.setObjectName("search_Reset_BT")
        self.search_Reset_BT.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        
        self.layoutSearch.addWidget(self.search_Input_QW, 0,0, 6,6)
        self.layoutSearch.addWidget(self.search_BT, 6,0, 2,2)
        self.layoutSearch.addWidget(self.search_And_RBT, 6,2, 1,1)
        self.layoutSearch.addWidget(self.search_Or_RBT, 7,2, 1,1)
        self.layoutSearch.addWidget(self.search_caseSense_CB, 6,3, 2,1)
        self.layoutSearch.addWidget(self.search_Reset_BT, 6,4, 2,2)
        #
        class NoteListQW(QListWidget):
            def __init__(self, mainwin):
                super().__init__()
                self.main_Win = mainwin
                self.setContextMenuPolicy(Qt.CustomContextMenu)
                self.customContextMenuRequested.connect(self.noteListContextMenu)
                self.main_Win.first_item = True
                self.itemClicked.connect(self.main_Win.noteItemClicked)

            def noteListContextMenu(self, pos):
                item = self.itemAt(pos)
                pop_MN = QMenu()
                pop_MN_Srt_MN = QMenu("排序", self)
                pop_MN_Srt_MN_Time0_AC = QAction("从早到晚", self)
                pop_MN_Srt_MN_Time1_AC = QAction("从晚到早", self)
                pop_MN_Srt_MN_Title_AC = QAction("标题", self)
                pop_MN_Srt_MN_Categ_AC = QAction("分类", self)
                pop_MN_Srt_MN_Exten_AC = QAction("文件类型", self)
                pop_MN_Srt_MN.addAction(pop_MN_Srt_MN_Time0_AC)
                pop_MN_Srt_MN.addAction(pop_MN_Srt_MN_Time1_AC)
                pop_MN_Srt_MN.addAction(pop_MN_Srt_MN_Title_AC)
                pop_MN_Srt_MN.addAction(pop_MN_Srt_MN_Categ_AC)
                pop_MN_Srt_MN.addAction(pop_MN_Srt_MN_Exten_AC)
                pop_MN_New_AC = QAction("新建", self)
                pop_MN_Arc_AC = QAction("存档", self)
                pop_MN_Trs_AC = QAction("回收", self)
                pop_MN_Del_AC = QAction("删除", self)
                pop_MN.addMenu(pop_MN_Srt_MN)
                pop_MN.addAction(pop_MN_New_AC)
                pop_MN.addAction(pop_MN_Arc_AC)
                pop_MN.addAction(pop_MN_Trs_AC)
                pop_MN.addAction(pop_MN_Del_AC)
                if(self.main_Win.note_List_Tab_QW.currentIndex() == 0):
                    pop_MN_New_AC.setEnabled(True)
                else:
                    pop_MN_New_AC.setEnabled(False)
                # 只允许在草稿中新建
                if item:
                    pop_MN_Arc_AC.setEnabled(True)
                    pop_MN_Trs_AC.setEnabled(True)
                    pop_MN_Del_AC.setEnabled(True)
                    if (self.main_Win.note_List_Tab_QW.currentIndex() == 0):
                        pop_MN_Del_AC.setEnabled(False)
                    if (self.main_Win.note_List_Tab_QW.currentIndex() == 1):
                        pop_MN_Arc_AC.setEnabled(False)
                        pop_MN_Del_AC.setEnabled(False)
                    if (self.main_Win.note_List_Tab_QW.currentIndex() == 2):
                        pop_MN_New_AC.setEnabled(False)
                        pop_MN_Trs_AC.setEnabled(False)
                        pop_MN_Del_AC.setEnabled(True)
                else:
                    pop_MN_Arc_AC.setEnabled(False)
                    pop_MN_Trs_AC.setEnabled(False)
                    pop_MN_Del_AC.setEnabled(False)
                if (self.main_Win.note_List_Tab_QW.currentIndex() == 0):
                    pop_MN_New_AC.setEnabled(True)
                else:
                    pop_MN_New_AC.setEnabled(False)
                pop_MN_Srt_MN_Time0_AC.triggered.connect(lambda: self.main_Win.sortNote("time0"))
                pop_MN_Srt_MN_Time1_AC.triggered.connect(lambda: self.main_Win.sortNote("time1"))
                pop_MN_Srt_MN_Title_AC.triggered.connect(lambda: self.main_Win.sortNote("title"))
                pop_MN_Srt_MN_Categ_AC.triggered.connect(lambda: self.main_Win.sortNote("Categ"))
                pop_MN_Srt_MN_Exten_AC.triggered.connect(lambda: self.main_Win.sortNote("Exten"))
                #                
                pop_MN_New_AC.triggered.connect(self.main_Win.addNote)
                pop_MN_Arc_AC.triggered.connect(lambda: self.main_Win.selectNote(item)) # sel 与 cur 并不完全相同
                pop_MN_Trs_AC.triggered.connect(lambda: self.main_Win.selectNote(item))
                pop_MN_Del_AC.triggered.connect(lambda: self.main_Win.selectNote(item))                
                pop_MN_Arc_AC.triggered.connect(lambda: self.main_Win.archiveNote())
                pop_MN_Trs_AC.triggered.connect(lambda: self.main_Win.trashNote())
                pop_MN_Del_AC.triggered.connect(lambda: self.main_Win.deleteNote())
                pop_MN.exec_(self.mapToGlobal(pos))
        
        self.note_List_Tab_Draft_QW = NoteListQW(self)
        self.note_List_Tab_Draft_QW.setObjectName("note_draft_list_QW")
        self.note_List_Tab_Archive_QW = NoteListQW(self)
        self.note_List_Tab_Archive_QW.setObjectName("note_archive_list_QW")
        self.note_List_Tab_Trash_QW = NoteListQW(self)
        self.note_List_Tab_Trash_QW.setObjectName("note_trash_list_QW")
        self.note_List_Tab_Search_QW = NoteListQW(self)
        self.note_List_Tab_Search_QW.setObjectName("note_search_list_QW")
        #
        self.note_List_Tab_QW = QTabWidget(self)
        self.note_List_Tab_QW.addTab(self.note_List_Tab_Draft_QW, "草稿")
        self.note_List_Tab_QW.addTab(self.note_List_Tab_Archive_QW, "存档")
        self.note_List_Tab_QW.addTab(self.note_List_Tab_Trash_QW, "回收")
        self.note_List_Tab_QW.addTab(self.note_List_Tab_Search_QW, "检索")
        
        self.layoutLeftGrid.addWidget(self.search_QW, 0,0, 1,1)
        self.layoutLeftGrid.addWidget(self.note_List_Tab_QW, 1,0, 1,1)
        
        # 加入中间栏
        self.mid_Panel_QW = QWidget(self)
        self.layoutMidGrid = QGridLayout()
        self.layoutMidGrid.setContentsMargins(0,0,0,0)
        self.mid_Panel_QW.setLayout(self.layoutMidGrid)
        
        self.mid_Top_Panel_QW = QWidget(self)
        self.layoutMidTopGrid = QGridLayout()
        self.layoutMidTopGrid.setContentsMargins(0,0,0,0)
        self.mid_Top_Panel_QW.setLayout(self.layoutMidTopGrid)
        #
        self.note_Title_LB = QLabel(self)
        self.note_Title_LB.setText("笔记标题：")
        self.note_Title_LB.setAlignment(Qt.AlignRight)
        self.note_Title_LB.setStyleSheet("font:bold 13pt;")
        self.layoutMidTopGrid.addWidget(self.note_Title_LB, 0,0, 1,1)

        self.note_Title_LE = QLineEdit(self)
        self.layoutMidTopGrid.addWidget(self.note_Title_LE, 0,1, 1,9)

        self.note_Keyword_LB = QLabel(self)
        self.note_Keyword_LB.setText("关键词：")
        self.note_Keyword_LB.setAlignment(Qt.AlignRight) # Qt.AlignBottom and Qt.AlignRight
        self.note_Keyword_LB.setStyleSheet("font:12pt;") # italic 
        self.layoutMidTopGrid.addWidget(self.note_Keyword_LB, 1,0, 1,1)

        class CheckableComboBox(QComboBox):
            def __init__(self, mainwin):
                super().__init__()
                self.main_Win = mainwin
                self.view().pressed.connect(self.handleItemPressed)
                self.setModel(QStandardItemModel(self))
                
            def handleItemPressed(self, index):
                item = self.model().itemFromIndex(index)
                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                    kwl = self.getCheckedItem()
                    self.main_Win.note_Keyword_LE.setText(";".join(kwl))
                else:
                    item.setCheckState(Qt.Checked)
                    kwl = self.getCheckedItem()
                    self.main_Win.note_Keyword_LE.setText(";".join(kwl))
                    
            def getCheckedItem(self):
                checked_items = []
                for index in range(self.count()):
                    item = self.model().item(index)
                    if item.checkState() == Qt.Checked:
                        checked_items.append(item.text())
                return checked_items

        self.note_Keyword_LE = QLineEdit(self)
        self.note_Keyword_CB = CheckableComboBox(self)
        #self.note_Keyword_PB.setStyleSheet("QPushButton { text-align: left; }")
        #self.note_Keyword_MN = QMenu()
        #self.note_Keyword_MN.setMaximumSize(100,100)
        #self.note_Keyword_PB.setMenu(self.note_Keyword_MN)
        self.layoutMidTopGrid.addWidget(self.note_Keyword_LE, 1,1, 1,6)
        self.layoutMidTopGrid.addWidget(self.note_Keyword_CB, 1,7, 1,3)

        self.left_Panel_Show_Hide_BT = QPushButton('>收>',self)
        self.left_Panel_Show_Hide_BT.setFlat(True)
        self.left_Panel_Show_Hide_BT.setMinimumWidth(40)
        self.left_Panel_Show_Hide_BT.setStyleSheet("QPushButton { text-align: left; }")
        self.layoutMidTopGrid.addWidget(self.left_Panel_Show_Hide_BT, 2,0, 1,1)

        self.note_Time_LB = QLabel(self)
        self.layoutMidTopGrid.addWidget(self.note_Time_LB,  2,1,  1,8)

        # 进度条
        class ProgressBar(QProgressBar):
        # https://stackoverflow.com/questions/27564805/place-the-text-in-the-middle-of-qprogressbar-when-setrange0-0-on-windows
            def __init__(self, parent=None):
                super(ProgressBar, self).__init__(parent)
                self.setStyleSheet("""QProgressBar{
                                   background-color: lightblue;
                                   border: 1px;
                                   border-radius: 5px;
                                   text-align: center
                                   }
                                   
                                   QProgressBar::chunk {
                                   background-color: #F0F0F0;
                                   width: 10px;
                                   margin: 0px;
                                   }""")
                
        self.note_Browser_PB = ProgressBar(self)
        self.note_Browser_PB.setObjectName("web_progess_bar_PB")
        self.note_Browser_PB.setMaximumSize(400, 30)
        self.note_Browser_PB.setContentsMargins(0,0,0,0)
        self.note_Browser_PB.hide()
        self.layoutMidTopGrid.addWidget(self.note_Browser_PB, 2,7, 1,2)
        
        self.right_Panel_Show_Hide_BT = QPushButton('<收<',self)
        self.right_Panel_Show_Hide_BT.setFlat(True)
        self.right_Panel_Show_Hide_BT.setMinimumWidth(40)
        self.right_Panel_Show_Hide_BT.setStyleSheet("QPushButton { text-align: right; }")
        self.layoutMidTopGrid.addWidget(self.right_Panel_Show_Hide_BT, 2,9, 1,1)

        self.in_Note_Search_LE = QLineEdit(self)
        self.layoutMidTopGrid.addWidget(self.in_Note_Search_LE, 3,1, 1,6)

        self.in_Note_Search_BT = QPushButton('页面内检索',self)
        self.in_Note_Search_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.in_Note_Search_BT, 3,7, 1,2)
    
        self.in_Note_Search_Reset_BT = QPushButton('重置',self)
        self.in_Note_Search_Reset_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.in_Note_Search_Reset_BT, 3,9, 1,1)
        # 按钮集合   
        class ClickableQLabel(QLabel):
            labelPressedSignal = pyqtSignal()
            def __init__(self, parent=None):
                super(ClickableQLabel, self).__init__(parent)
                self.label_press_ctr = 0
            def mousePressEvent(self, e):
                self.label_press_ctr += 1
            def mouseReleaseEvent(self, e):
                if (self.label_press_ctr == 1):
                    self.labelPressedSignal.emit()
                    self.label_press_ctr = 0
        self.note_View_Edit_LB = ClickableQLabel()
        self.note_View_Edit_LB.setAlignment(Qt.AlignCenter)
        self.note_View_Edit_LB.setText('''
                                <span style='color:grey;'>阅览</span>
                                <span style='color:grey;font-size:14pt;'>|</span>
                                <span style='background-color:#6effbf;font-size:16pt;font:bold;'>编辑</span>
                                ''')
        self.layoutMidTopGrid.addWidget(self.note_View_Edit_LB, 3,0, 2,1)

        self.note_Save_BT = QPushButton('保存',self)
        self.note_Save_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.note_Save_BT, 4,1, 1,1)

        # self.note_Archive_BT = QPushButton('存档',self)
        # self.note_Archive_BT.setMinimumWidth(40)
        # self.note_Archive_BT.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding) 
        # self.layoutMidTopGrid.addWidget(self.note_Archive_BT, 4,2, 1,1)

        # self.btDele = QPushButton('删除',self)
        # self.layoutMidTopGrid.addWidget(self.btDele, bt_layoutMidGrid_row,3)                
        
        # self.note_HTML_Source_BT = QPushButton('源码',self)
        # self.note_HTML_Source_BT.setMinimumWidth(40)
        # self.note_HTML_Source_BT.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding) 
        # self.layoutMidTopGrid.addWidget(self.note_HTML_Source_BT, 4,2, 1,1)

        self.note_Zoom_BT = QPushButton('放大',self)
        self.note_Zoom_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.note_Zoom_BT, 4,2, 1,1)
        
        self.note_Edit_Undo_BT = QPushButton('撤销',self)
        self.note_Edit_Undo_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.note_Edit_Undo_BT, 4,3, 1,1)

        self.note_Edit_Bold_BT = QPushButton('粗',self) # 可以加个颜色的样式
        self.note_Edit_Bold_BT.setStyleSheet("font: bold")
        self.note_Edit_Bold_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.note_Edit_Bold_BT, 4,4, 1,1)

        self.note_Edit_Red_BT = QPushButton('红',self) # 可以加个颜色的样式
        self.note_Edit_Red_BT.setStyleSheet("color: #ff0000")
        self.note_Edit_Red_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.note_Edit_Red_BT, 4,5, 1,1)        

        self.note_Edit_Highlight_Yellow_BT = QPushButton('高亮黄',self) # 可以加个颜色的样式
        self.note_Edit_Highlight_Yellow_BT.setStyleSheet("background-color: #ffff00")
        self.note_Edit_Highlight_Yellow_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.note_Edit_Highlight_Yellow_BT, 4,6, 1,1)

        self.note_Edit_Highlight_Blue_BT = QPushButton('高亮蓝',self) # 可以加个颜色的样式
        self.note_Edit_Highlight_Blue_BT.setStyleSheet("background-color: #00ffff")
        self.note_Edit_Highlight_Blue_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.note_Edit_Highlight_Blue_BT, 4,7, 1,1)

        self.note_Edit_Unorder_List_BT = QPushButton('弹列',self) # 可以加个颜色的样式
        self.note_Edit_Unorder_List_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.note_Edit_Unorder_List_BT, 4,8, 1,1)

        self.note_Edit_Order_List_BT = QPushButton('数列',self) # 可以加个颜色的样式
        self.note_Edit_Order_List_BT.setMinimumWidth(40)
        self.layoutMidTopGrid.addWidget(self.note_Edit_Order_List_BT, 4,9,1,1)

        # 浏览页
        self.mid_Bottom_Panel_QW = QWidget(self)
        self.layoutMidBottomGrid = QGridLayout()
        self.layoutMidBottomGrid.setContentsMargins(0,0,0,0)
        self.mid_Bottom_Panel_QW.setLayout(self.layoutMidBottomGrid)
        
        self.note_Source_QW = QPlainTextEdit(self)
        self.ctr_source_orNot = 0 # 初始化是否为源码的判断
        self.note_Browser_QW = QWebEngineView(self)
        self.note_Browser_QW.setHtml("<h2>欢迎使用:)</h2>")
        #
        self.note_Viewer_Tab_QW = QTabWidget(self) 
        self.note_Viewer_Tab_QW.tabBar().hide() # 多加了一行感觉空间利用不经济
        self.note_Viewer_Tab_QW.addTab(self.note_Browser_QW,"浏览")
        self.note_Viewer_Tab_QW.addTab(self.note_Source_QW,"源码")
        self.layoutMidBottomGrid.addWidget(self.note_Viewer_Tab_QW, 0,0, 1, 1)
        self.layoutMidGrid.addWidget(self.mid_Top_Panel_QW, 0,0, 1,1)
        self.layoutMidGrid.addWidget(self.mid_Bottom_Panel_QW, 1,0, 1,1)
        
    # 开始右侧
        self.right_Panel_QW = QWidget(self)
        self.layoutRightGrid = QGridLayout()
        self.layoutRightGrid.setContentsMargins(0,0,0,0)
        self.right_Panel_QW.setLayout(self.layoutRightGrid)
        #
        limit_width_can_expand = QSizePolicy()
        limit_width_can_expand.PolicyFlag(1) # 所谓的GrowFlag
        
        # 加入链接栏
        self.note_Link_LB = QLabel(self)
        self.note_Link_LB.setObjectName("url_Link_QW")
        self.note_Link_LB.setWordWrap(True)
        self.note_Link_LB.setMaximumSize(400, 30)
        self.note_Link_LB.setContentsMargins(10,0,10,0)
        self.note_Link_LB.setSizePolicy(limit_width_can_expand)
        self.note_Link_LB.setOpenExternalLinks(True) # 或者可以试试按钮加信号 QtGui.QDesktopServices.openUrl(QtCore.QUrl('http://www.hao123.com'))
        # 加入附件栏
        class DragDropList(QListWidget):
            droppedSignal = pyqtSignal([list])
            def __init__(self, mainwin, parent=None):
                super(DragDropList, self).__init__(parent)
                self.main_Win = mainwin
                self.setContextMenuPolicy(Qt.CustomContextMenu)
                self.customContextMenuRequested.connect(self.atmListContextMenu)
                #self.itemClicked.connect(self.main_Win.?????)
                self.setAcceptDrops(True)
                self.setIconSize(QSize(48,48))
            
            def dragEnterEvent(self, event):
                if event.mimeData().hasUrls:
                    event.accept()
                else:
                    event.ignore()
            
            def dragMoveEvent(self, event):
                if event.mimeData().hasUrls:
                    event.setDropAction(Qt.CopyAction)
                    event.accept()
                else:
                    event.ignore()
                    
            def dropEvent(self, event):
                if event.mimeData().hasUrls:
                    event.setDropAction(Qt.CopyAction)
                    event.accept()
                    links = []
                    for url in event.mimeData().urls():
                        links.append(str(url.toLocalFile()))
                    self.droppedSignal.emit(links)
                else:
                    event.ignore()
            
            def atmListContextMenu(self, pos):
                item = self.itemAt(pos)
                pop_MN = QMenu()
                pop_MN_Open_AC = QAction("打开", self)
                pop_MN_Loca_AC = QAction("定位", self)
                pop_MN_Dele_AC = QAction("删除", self)
                pop_MN.addAction(pop_MN_Open_AC)
                pop_MN.addAction(pop_MN_Loca_AC)
                pop_MN.addAction(pop_MN_Dele_AC)
                if item:
                    pop_MN_Open_AC.setEnabled(True)
                    pop_MN_Dele_AC.setEnabled(True)
                else:
                    pop_MN_Open_AC.setEnabled(False)
                    pop_MN_Dele_AC.setEnabled(False)
                
                pop_MN_Open_AC.triggered.connect(lambda: self.main_Win.openAttachment(item))
                pop_MN_Loca_AC.triggered.connect(lambda: self.main_Win.locAttachment())
                pop_MN_Dele_AC.triggered.connect(lambda: self.main_Win.delAttachment(item))
                pop_MN.exec_(self.mapToGlobal(pos))   
               
        self.note_Attachment_QW = DragDropList(self)
        self.note_Attachment_QW.setObjectName("note_Attachment_QW")
        self.note_Attachment_QW.setResizeMode(QListView.Adjust)
        self.note_Attachment_QW.setViewMode(QListView.IconMode)
                  
        # 加入日历栏
        class Calender(QCalendarWidget):
            def __init__(self, parent=None):
                super(Calender, self).__init__(parent)
                self.date_list = []
            
            def paintCell(self, painter, rect, date): # 这个应该是调用了内置的参数 好奇葩哦
                QCalendarWidget.paintCell(self, painter, rect, date)
                if date in self.date_list:
                    color = QColor(1,33,105)
                    color.setAlpha(100)
                    painter.fillRect(rect, color)
            
            def genCell(self, dateset):
                self.date_list = []
                for d in dateset:
                    self.date_list.append(QDate(d))
                self.updateCells()
        
        self.note_Calendar_QW = Calender(self)
        self.note_Calendar_QW.setObjectName("note_Calendar_QW")
        self.note_Calendar_QW.genCell(self.note_index.getAllDate()) # 这个widget真是有意思
        #
        self.layoutRightGrid.addWidget(self.note_Link_LB, 0,0, 1,1)
        self.layoutRightGrid.addWidget(self.note_Attachment_QW, 1,0, 1,1)
        self.layoutRightGrid.addWidget(self.note_Calendar_QW, 2,0, 1,1)
        #
        self.panels_SP.addWidget(self.left_Panel_QW)
        self.panels_SP.addWidget(self.mid_Panel_QW)
        self.panels_SP.addWidget(self.right_Panel_QW)
        # self.panels_SP.setStyleSheet("QSplitter::handle {margin: 0px; bolder: 0px; background-color:grey;}")
        self.layoutMainGrid.addWidget(self.panels_SP)
        # 状态栏
        self.status_Bar = self.statusBar()
        self.status_Bar.setContentsMargins(0,0,0,0)
        self.status_Bar.showMessage('准备就绪') 
        
    # 信号关联
        menu_Bar_File_Exit_AC.triggered.connect(qApp.quit) 
        menu_Bar_Reload_Import_AC.triggered.connect(self.importNoteFolder)
        menu_Bar_Reload_All_AC.triggered.connect(self.click2Reload)     
        menu_Bar_Reload_New_AC.triggered.connect(self.click2ReloadNew)
        menu_Bar_Analyze_Stt_AC.triggered.connect(self.click2Analyze)

        # self.search_And_RBT.toggled.connect(self.searchAndOrState)
        # self.search_Or_RBT.toggled.connect(self.searchAndOrState)
        self.search_BT.clicked.connect(self.click2SearchKeyWords)
        self.search_Reset_BT.clicked.connect(self.click2ResetSearchKeywords)
        #
        # self.note_Title_LE.textChanged[str].connect(self.onChanged)
        # self.note_Keyword_LE.textChanged[str].connect(self.onChanged)
        # self.note_Browser_QW.page().contentsSizeChanged.connect(self.onChanged)
        # 如何监听网页内容变化还不会搞？？？？？？
        self.left_Panel_Show_Hide_BT.clicked.connect(self.showHideLeftPanel)
        self.right_Panel_Show_Hide_BT.clicked.connect(self.showHideRightPanel)
        #
        self.in_Note_Search_BT.clicked.connect(self.click2InNoteSearch)
        self.in_Note_Search_Reset_BT.clicked.connect(self.click2InNoteSearchReset)
        self.note_View_Edit_LB.labelPressedSignal.connect(self.click2ViewEdit)
        self.note_Save_BT.clicked.connect(self.click2Save)
        # self.note_Archive_BT.clicked.connect(self.click2Arcv)
        # self.btDele.clicked.connect(self.click2Dele)
        # self.note_HTML_Source_BT.clicked.connect(self.click2Source)
        self.note_Zoom_BT.clicked.connect(self.click2Zoom)
        self.note_Edit_Undo_BT.clicked.connect(self.click2Undo)
        self.note_Edit_Highlight_Yellow_BT.clicked.connect(self.click2HighlightYellow)
        self.note_Edit_Highlight_Blue_BT.clicked.connect(self.click2HighlightBlue)
        self.note_Edit_Bold_BT.clicked.connect(self.click2Bold)
        self.note_Edit_Red_BT.clicked.connect(self.click2Red)
        self.note_Edit_Unorder_List_BT.clicked.connect(self.click2UOList)
        self.note_Edit_Order_List_BT.clicked.connect(self.click2OList)
        ####
        # self.note_Browser_QW.loadChanged(?????? 提示保存)
        self.note_Browser_QW.loadProgress.connect(self.onWebLoading)
        self.note_Browser_QW.loadFinished.connect(self.onWebLoadFinished)
        #
        self.note_Attachment_QW.droppedSignal.connect(self.addAttachment)
        self.note_Calendar_QW.clicked.connect(self.click2SearchDate)
        self.refreshNotesList() # 也算是一种初始化。。。不过必须放在函数包含的各种widget加入之后哦
        self.refreshKeywordsList()
        
    # 功能函数 
    def setDataDirList(self, lst):
        self.note_index_dir = lst[0] # 数据库
        self.note_root_dir = lst[1] # 数据表
        self.note_cur_dir = lst[2] # 导入库     
        # 初始化构建
        self.note_col = ["type","title","path","ctime","mtime","atime"
                        ,"url","ext","cat","keywords","summary"] # ,"attachments"
        self.note_index = NoteIndex(self.note_index_dir, "Note", self.note_col, self.note_root_dir)
        self.note_index.create()
        
    def click2SearchKeyWords(self):
        kwl = self.search_Input_QW.toPlainText().split("\n")
        if kwl == [""]:
            self.searchDupNotes()
        else:
            self.searchNoteIndex(kwl, flag=0)
        self.note_List_Tab_QW.setCurrentIndex(3)
        
    def click2SearchDate(self):
        selected_date = self.note_Calendar_QW.selectedDate().toPyDate() # datetime.datetime.strptime(??, "%Y-%m-%d").date()
        self.searchNoteIndex(selected_date, flag=1)
        self.note_List_Tab_QW.setCurrentIndex(3)
        
    def searchNoteIndex(self, keywords, flag):
        tb_a = self.note_index.data
        c = tb_a.any(axis='columns') # 先获得一个全True的列
        if flag == 0: # 说明不是日期检索
            search_in = ["title", "keywords"] # 内容什么的就是索引该怎么搞还是个问题（见开头）
            # print(c)
            c_si = ~c
            for si in search_in:
                if self.search_andOr_BG.checkedId() == 0: # 与 查询
                    sao = " 与 "
                    c_kw = c
                    for kw in keywords:
                        if (not kw or kw.isspace()):
                            pass # 忽略所有空行或空格
                        else:                   
                            c_si_kw = tb_a[si].str.contains(kw, case=self.search_caseSense_CB.isChecked(), na=False)
                        c_kw = (c_kw) & (c_si_kw) 
                elif self.search_andOr_BG.checkedId() == 1: # 或 查询
                    sao = " 或 "
                    c_kw = ~c
                    for kw in keywords:
                        if (not kw or kw.isspace()):
                            pass # 忽略所有空行或空格
                        else:                   
                            c_si_kw = tb_a[si].str.contains(kw, case=self.search_caseSense_CB.isChecked(), na=False)
                        c_kw = (c_kw) | (c_si_kw)
                else:
                    self.statusBar().showMessage("有点问题："+self.search_andOr_BG.checkedId())
                c_si = (c_si) | (c_kw) # 可能和计算顺序等有关系，这里用&=,|=会出错
            tb_s = tb_a[c_si].copy()
        else: # 即日期索引
            search_in = ["atime", "ctime", "mtime"]
            # print(tb_a["atime"])
            c_si_dt = c
            for si in search_in:
                c_si = (tb_a[si].dt.date == keywords) # 日期这里就一个元素 
                c_si_dt = (c_si_dt | c_si)
            tb_s = tb_a[c_si_dt].copy()
            sao = "日期为"
            keywords = ["", str(keywords)]
        if tb_s.empty:
            self.note_List_Tab_Search_QW.clear()
            self.statusBar().showMessage("笔记库中未找到{}的笔记".format(sao.join(keywords)))
        else:
            self.note_List_Tab_Search_QW.clear()
            self.showInSearchTab(tb_s)
            self.statusBar().showMessage("笔记库中共找到{}条笔记".format(tb_s.shape[0]))
  
    def searchDupNotes(self):
        tb_a = self.note_index.data.loc[self.note_index.data["type"].isin(["Draft","Archive"])] # 回收的就不包含在内了
        search_in = ["title","url"]
        c = ~tb_a.any(axis='columns') # 先获得一个全False的列
        for si in search_in:
            c = c | tb_a.duplicated(si, keep=False)
        tb_s = tb_a[c].copy()
        if tb_s.empty:
            self.statusBar().showMessage("笔记库中未找到 标题 或 链接 重复的项目")
        else:
            self.note_List_Tab_Search_QW.clear()
            self.showInSearchTab(tb_s)
            self.statusBar().showMessage("共找到{}条重复的项目".format(tb_s.shape[0]))
  
    def showInSearchTab(self, df):
        for index, row in df.iterrows(): # 以下行为其实等于复制一个笔记记录
            s_info = NotePack(self.note_index)
            s_info.load(index)
            s_item = QListWidgetItem()
            s_item.setText(s_info.title)
            s_item.setData(Qt.UserRole, s_info)
            self.note_List_Tab_Search_QW.addItem(s_item)
    
    def click2ResetSearchKeywords(self):
        self.note_List_Tab_Search_QW.clear()
        self.search_Input_QW.setPlainText("")
    
    def showHideLeftPanel(self):
        self.ctr_showHide_left_panel += 1
        if self.ctr_showHide_left_panel % 2 == 1:
            self.left_Panel_QW.setHidden(True)
            self.statusBar().showMessage("收起来节约点空间")
            self.left_Panel_Show_Hide_BT.setText(">展>") # 注意这里是下次应该看到的内容
        else:
            self.left_Panel_QW.setHidden(False)
            self.statusBar().showMessage("我又回来了")
            self.left_Panel_Show_Hide_BT.setText(">收>")

    def showHideRightPanel(self):
        self.ctr_showHide_right_panel += 1
        if self.ctr_showHide_right_panel % 2 == 1:
            self.right_Panel_QW.setHidden(True)
            self.statusBar().showMessage("收起来节约点空间")
            self.right_Panel_Show_Hide_BT.setText("<展<")
        else:
            self.right_Panel_QW.setHidden(False)
            self.statusBar().showMessage("我又回来了")
            self.right_Panel_Show_Hide_BT.setText("<收<")

    def click2InNoteSearch(self):
        kw = str(self.in_Note_Search_LE.text())
        self.note_Browser_QW.page().findText(kw)
    
    def click2InNoteSearchReset(self):
        self.in_Note_Search_LE.setText("")
        self.note_Browser_QW.page().findText("")

    def click2ViewEdit(self):
        self.ctr_viewEdit += 1
        if (self.ctr_viewEdit % 2 == 0):
            self.note_Browser_QW.page().runJavaScript("document.documentElement.contentEditable = false;")
            self.note_View_Edit_LB.setText('''
                                <span style='background-color:#faf096;font-size:16pt;font:bold;'>阅览</span>
                                <span style='color:grey;font-size:14pt;'>|</span>
                                <span style='color:grey;'>编辑</span>
                                ''')                                
            self.statusBar().showMessage('只能浏览了。。') 
        else:
            self.note_Browser_QW.page().runJavaScript("document.documentElement.contentEditable = true;") 
            self.note_View_Edit_LB.setText('''
                                <span style='color:grey;'>阅览</span>
                                <span style='color:grey;font-size:14pt;'>|</span>
                                <span style='background-color:#6effbf;font-size:16pt;font:bold;'>编辑</span>
                                ''')
            self.statusBar().showMessage('可以编辑了。。')

    def click2Save(self):
        self.saveNote()
        
    # def click2Arcv(self):
    #     self.sel_item = self.cur_item
    #     self.archiveNote()
        
    #def click2Dele(self):
    #    self.statusBar().showMessage('删掉咯')
    #    self.deleNote()

    # def click2Source(self):
    #     self.ctr_source_orNot += 1
    #     if self.ctr_source_orNot % 2 == 1: # 从浏览到源码
    #         self.saveNote()
    #         self.loadNote()
    #     else: # 从源码到浏览
    #         if (os.path.splitext(self.cur_note.path)[1] == ".html"):
    #             self.cur_note_html = self.note_Source_QW.toPlainText()
    #             self.saveHTMLContent()??????
    #         self.loadNote()
    #     self.note_Viewer_Tab_QW.setCurrentIndex(self.ctr_source_orNot % 2)
      
    def click2Zoom(self):
        self.zoom_fac += 0.25
        if self.zoom_fac <= 5: # 参考Qt文档对zoomFactor的限制
            self.statusBar().showMessage('网页放大至{:.0%}'.format(self.zoom_fac))
        else:
            self.zoom_fac = 1
        self.note_Browser_QW.setZoomFactor(self.zoom_fac)
        
    def click2Undo(self): # 要是知道什么时候算是撤销到底就好了 
        self.statusBar().showMessage('撤了撤了')
        self.note_Browser_QW.page().runJavaScript("document.execCommand('undo');")              
        self.note_Browser_QW.setZoomFactor(1)
        
    def click2HighlightYellow(self):  
        self.statusBar().showMessage('变黄了吧')
        self.note_Browser_QW.page().runJavaScript("document.documentElement.contentEditable = true;") 
        self.note_View_Edit_LB.setText('''
                                <span style='color:grey;'>阅览</span>
                                <span style='color:grey;font-size:14pt;'>|</span>
                                <span style='background-color:#6effbf;font-size:16pt;font:bold;'>编辑</span>
                                ''')
        self.note_Browser_QW.page().runJavaScript("document.execCommand('backColor', false, 'ffff00');") 
        
    def click2HighlightBlue(self):  
        self.statusBar().showMessage('变蓝了吧')
        self.note_Browser_QW.page().runJavaScript("document.documentElement.contentEditable = true;")
        self.note_View_Edit_LB.setText('''
                                <span style='color:grey;'>阅览</span>
                                <span style='color:grey;font-size:14pt;'>|</span>
                                <span style='background-color:#6effbf;font-size:16pt;font:bold;'>编辑</span>
                                ''')   
        self.note_Browser_QW.page().runJavaScript("document.execCommand('backColor', false, '00ffff');") 
        
    def click2Bold(self):  
        self.statusBar().showMessage('变粗了吧')
        self.note_Browser_QW.page().runJavaScript("document.documentElement.contentEditable = true;")
        self.note_View_Edit_LB.setText('''
                                <span style='color:grey;'>阅览</span>
                                <span style='color:grey;font-size:14pt;'>|</span>
                                <span style='background-color:#6effbf;font-size:16pt;font:bold;'>编辑</span>
                                ''')
        self.note_Browser_QW.page().runJavaScript("document.execCommand('bold', false, '000000');")
        
    def click2Red(self):  
        self.statusBar().showMessage('变红了吧')
        self.note_Browser_QW.page().runJavaScript("document.documentElement.contentEditable = true;")
        self.note_View_Edit_LB.setText('''
                                <span style='color:grey;'>阅览</span>
                                <span style='color:grey;font-size:14pt;'>|</span>
                                <span style='background-color:#6effbf;font-size:16pt;font:bold;'>编辑</span>
                                ''')
        self.note_Browser_QW.page().runJavaScript("document.execCommand('foreColor', false, 'ff0000');")        
        
    def click2UOList(self):  
        self.statusBar().showMessage('弹列开始')
        self.note_Browser_QW.page().runJavaScript("document.documentElement.contentEditable = true;")
        self.note_View_Edit_LB.setText('''
                                <span style='color:grey;'>阅览</span>
                                <span style='color:grey;font-size:14pt;'>|</span>
                                <span style='background-color:#6effbf;font-size:16pt;font:bold;'>编辑</span>
                                ''')
        self.note_Browser_QW.page().runJavaScript("document.execCommand('InsertUnorderedList', false);") 
        
    def click2OList(self):  
        self.statusBar().showMessage('数列开始')
        self.note_Browser_QW.page().runJavaScript("document.documentElement.contentEditable = true;")
        self.note_View_Edit_LB.setText('''
                                <span style='color:grey;'>阅览</span>
                                <span style='color:grey;font-size:14pt;'>|</span>
                                <span style='background-color:#6effbf;font-size:16pt;font:bold;'>编辑</span>
                                ''')
        self.note_Browser_QW.page().runJavaScript("document.execCommand('InsertnorderedList', false);")           

    def noteItemClicked(self, item):
        if self.first_item:
            pass
        else:
            self.ifSaved()
            if not self.saveFlag:
                note_save_cfm = QMessageBox.question(self, "注意", "之前的文件可能有变动未保存！！!\n是否保存更改？"
                                                    ,QMessageBox.Ok|QMessageBox.Cancel, QMessageBox.Ok)
                if note_save_cfm == QMessageBox.Ok:
                    self.saveNote()
                else: # note_save_cfm == QMessageBox.Cancel:
                    pass
            else:
                pass
        self.cur_item = item 
        self.cur_note = item.data(Qt.UserRole) # 这个Qt.UserRole 还真是神奇 -_-||
        self.loadNote()

    def ifSaved(self):
        if_t = (self.cur_note.title == self.note_Title_LE.text())
        if_k = (self.cur_note.keywords == self.note_Keyword_LE.text())
        # if os.path.splitext(self.cur_note.content)[1] == ".html":
        #     prv_note_html = self.cur_note_html
        #     self.getHTMLContent() #
        #     if_c = (prv_note_html == self.cur_note_html)
        # else:
        #     if_c = True
        # print(self.cur_note_html)
        if_a = (set(self.cur_note.att_list) == set(os.listdir(self.cur_note.att_dir)))
        self.saveFlag=(if_t & if_k & if_a) # 如果有一个假就说明发生改变 if_c & 
     
    def loadNote(self):
        self.cur_note.load()
        if os.path.exists(self.cur_note.path):
            self.note_Title_LE.setText(self.cur_note.title) 
            self.note_Keyword_LE.setText(self.cur_note.keywords)
            self.note_Time_LB.setText("修改时间：{}".format(self.cur_note.mtime))
            self.note_Link_LB.setText("<html><a href={0}>{0}</a></html>".format(self.cur_note.url))
            self.loadNoteContent()
            self.loadNoteAttachments()
            self.first_item = False 
        else: 
            self.statusBar().showMessage("读取笔记{}有问题呢".format(self.cur_note.path))
        
    def loadNoteContent(self):
        file_fullname = os.path.basename(self.cur_note.content)
        file_ext = os.path.splitext(file_fullname)
        if (file_ext[1] == ".html"):
            with open(self.cur_note.content, "r", encoding="utf-8") as f: #.decode("utf-8")
                self.cur_note_html = f.read()
            # load外部数据时非同步，setHtml有2Mb的限制
            self.note_Browser_QW.load(QUrl.fromLocalFile(self.cur_note.content)) # QUrl(pathlib.Path(self.cur_note["path"]).as_uri())
            self.note_Source_QW.setPlainText(self.cur_note_html)
            
        elif (file_ext[1] == ".pdf"):
            PDFJS = "file:///E:/Work/Programming/WebNote/pyqt5/asset/pdfjs/web/viewer.html"
            path_u = pathlib.Path(self.cur_note.content).as_uri() # 必须先转化成file:///开头这种形式
            with open(self.cur_note.content, "rb") as f:
                self.cur_note_html = f.read()
            self.note_Browser_QW.load(QUrl.fromUserInput('{}?file={}'.format(PDFJS, path_u))) # 采用FIrefox的PDFjs解决问题 https://stackoverflow.com/questions/23389001/how-to-render-pdf-using-pdf-js-viewer-in-pyqt
            # self.note_Browser_QW.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True) # 不管用了
            self.note_Source_QW.setPlainText("显示的是PDF格式，没有所谓原始代码哟！")
        else:
            try:
                self.note_Browser_QW.load(QUrl.fromLocalFile(self.cur_note.content))
            except Exception as e:
                self.statusBar().showMessage("打开{}时，有点问题:{}".format(self.cur_note.content, e))
        self.statusBar().showMessage('加载中。。。')
    
    def onWebLoading(self, progress):
        self.note_Browser_PB.show()
        self.note_Browser_PB.setValue(progress)
    
    def onWebLoadFinished(self, isFinished):
        # if isFinished:
        self.note_Browser_PB.hide() 
        self.note_Time_LB.show()
        self.note_Browser_QW.page().runJavaScript("document.documentElement.contentEditable = true;") 
        self.ctr_viewEdit = 1 # 初始化编辑或预览的计数 奇数为可编辑
        self.zoom_fac = 1 # 初始化放大倍数
        self.statusBar().showMessage('加载完毕可以编辑啦')
 
    def loadNoteAttachments(self): 
        self.note_Attachment_QW.clear()
        try:
            for att_n in self.cur_note.att_list:
                att_p = os.path.join(self.cur_note.att_dir, att_n)
                self.loadAttItem(att_p)
        except Exception as e:
            self.statusBar().showMessage("读取附件有误：",e)
        
    def loadAttItem(self, file_path):
        fileInfo = QFileInfo(file_path)
        fileIcon = QFileIconProvider()
        icon = QIcon(fileIcon.icon(fileInfo))
        pixmap = icon.pixmap(72, 72)                
        icon = QIcon(pixmap)
        #
        a_item = QListWidgetItem()
        a_item.setText(os.path.basename(file_path))
        a_item.setIcon(icon)
        a_item.setData(Qt.UserRole, os.path.abspath(file_path))
        self.note_Attachment_QW.addItem(a_item)
 
    def addNote(self):
        self.cur_note = NotePack(self.note_index)
        self.cur_note.create()
        self.cur_item = QListWidgetItem()
        self.cur_item.setText(self.cur_note.title) 
        self.cur_item.setData(Qt.UserRole, self.cur_note)
        self.note_List_Tab_Draft_QW.insertItem(0, self.cur_item)
        self.statusBar().showMessage('新建了一个')

    def saveNote(self):
        self.cur_note.title = self.note_Title_LE.text()
        self.cur_note.keywords = self.note_Keyword_LE.text()
        self.getHTMLContent()
        self.cur_note.update(content = self.cur_note_html)
        # -> item.data
        self.cur_item.setText(self.cur_note.title)
        self.cur_item.setData(Qt.UserRole, self.cur_note)
        self.statusBar().showMessage('我保存啦') 
    
    def getHTMLContent(self):
        self.note_Browser_QW.page().toHtml(self.callHTML)
        # 以下内容具体原因见：https://stackoverflow.com/questions/48386253/save-html-files-in-qwebengineview-browser
        loop = QEventLoop()
        self.onHtmlGot.connect(loop.quit)
        loop.exec_()
        # 以上内容原因是：the toHtml() function of QtWebEngine is asynchronous,
        # to convert that process asynchronous to synchronous we use a QEventLoop with the help of a signal        

    def callHTML(self, html):
        self.cur_note_html = html
        self.onHtmlGot.emit()

    def selectNote(self, item):
        qw_dict = {0:self.note_List_Tab_Draft_QW
                  ,1:self.note_List_Tab_Archive_QW
                  ,2:self.note_List_Tab_Trash_QW
                  }
        self.sel_list_QW = qw_dict[self.note_List_Tab_QW.currentIndex()]
        self.sel_item = item
        self.sel_note = self.sel_item.data(Qt.UserRole)
 
    def archiveNote(self):
        self.sel_note.type = "Archive"
        self.sel_note.move(dest=self.sel_note.type)
        self.sel_item.setData(Qt.UserRole, self.sel_note)
        self.sel_list_QW.takeItem(self.sel_list_QW.row(self.sel_item))
        self.note_List_Tab_Archive_QW.addItem(self.sel_item)
        self.statusBar().showMessage('我存档啦') 

    def trashNote(self):
        self.sel_note.type = "Trash"
        self.sel_note.move(dest=self.sel_note.type)
        self.sel_item.setData(Qt.UserRole, self.sel_note)
        self.sel_list_QW.takeItem(self.sel_list_QW.row(self.sel_item))
        self.note_List_Tab_Trash_QW.addItem(self.sel_item)
        self.statusBar().showMessage('回收掉啦') 

    def deleteNote(self):
        self.sel_note.delete()
        self.sel_list_QW.takeItem(self.sel_list_QW.row(self.sel_item))
        self.statusBar().showMessage('就删掉呗') 
        self.first_item = True
     
    def importNoteFolder(self):
        selected_note_path = QFileDialog().getExistingDirectory(self, "Open file", self.note_root_dir)
        if selected_note_path:
            self.note_cur_dir = os.path.abspath(selected_note_path)
            self.statusBar().showMessage('笔记根目录已改为：{}'.format(self.note_cur_dir))
        else:
            print("选择笔记暂存文件夹有问题：",e)
            
    def click2Reload(self):
        reload_all_cfm = QMessageBox.warning(self, "Warning", "注意：文件多的话会超慢！！!\n确定要继续吗？"
                                            ,QMessageBox.Ok|QMessageBox.Cancel, QMessageBox.Ok)
        if reload_all_cfm == QMessageBox.Ok:
            self.reloadAll()
        elif reload_all_cfm == QMessageBox.Cancel:
            self.statusBar().showMessage("破电脑，怂的一匹")
        else:
            return
            
    def click2ReloadNew(self):
        self.reloadNew()

    def reloadAll(self):
        self.note_index.archive()
        self.note_index = NoteIndex(self.note_index_dir, "Note", self.note_col, self.note_root_dir)
        self.note_index.create()
        self.walkDir()     
        self.refreshNotesList()
        self.refreshKeywordsList()
        self.note_Calendar_QW.genCell(self.note_index.getAllDate())

    def reloadNew(self):
        self.note_index = NoteIndex(self.note_index_dir, "Note", self.note_col, self.note_root_dir)
        self.note_index.create()
        self.walkDir(1)
        self.refreshNotesList()
        self.refreshKeywordsList()
        self.note_Calendar_QW.genCell(self.note_index.getAllDate())

    def sortNote(self, flag):
        if flag == "time0":
            self.note_index.data.sort_values(by="mtime", ascending=True, inplace=True)
        elif flag == "time1":
            self.note_index.data.sort_values(by="mtime", ascending=False, inplace=True)
        elif flag == "title":
            self.note_index.data.sort_values(by="title", inplace=True)
        elif flag == "Categ":
            self.note_index.data.sort_values(by="cat", inplace=True)
        elif flag == "Exten":
            self.note_index.data.sort_values(by="ext", inplace=True)
        else:
            pass
        self.refreshNotesList()

    def refreshNotesList(self):
        try:
            qw_dict = {"Draft":self.note_List_Tab_Draft_QW
                      ,"Archive":self.note_List_Tab_Archive_QW
                      ,"Trash":self.note_List_Tab_Trash_QW
                      }
            for qw_Key,qw_Val in qw_dict.items():
                qw_Val.clear()
                if self.note_index.data.empty:
                    self.note_Browser_QW.setHtml("<h2>欢迎使用:)</h2><p>不过索引表暂空，请进行重新加载</p>") # self.reloadAll()
                else:
                    tb = self.note_index.data.loc[self.note_index.data["type"].str.contains(qw_Key, na=False)].copy()
                    for index, row in tb.iterrows():
                        #
                        ql_info = NotePack(self.note_index)
                        ql_info.load(index) 
                        ql_item = QListWidgetItem()
                        ql_item.setText(ql_info.title)
                        ql_item.setData(Qt.UserRole, ql_info) # 这个Qt.UserRole 还真是神奇 -_-||
                        qw_Val.addItem(ql_item)
        except Exception as e:
            print("加载出错:",e)

    def refreshKeywordsList(self):
        if self.note_index.data.empty:
            pass
        else:
            tb = self.note_index.data["keywords"].sort_values().unique().copy()
            for index,kw in enumerate(tb):
                self.note_Keyword_CB.addItem(kw)
                item = self.note_Keyword_CB.model().item(index, 0) # 大致意思应该是获取刚刚那个item
                item.setCheckState(False)
                
                
                # self.note_Keyword_AC[kw] = QAction(kw, self.note_Keyword_MN)
                # self.note_Keyword_AC[kw].setCheckable(True)
                # # self.note_Keyword_AC[kw].triggered.connect(lambda: self.updateKeywords(item))
                # self.note_Keyword_AC[kw].triggered.connect(lambda: self.updateKeywords(self.note_Keyword_AC[kw],kw))
                # .addAction(self.note_Keyword_AC[kw])
    
    # def updateKeywords(self, item, kw):
    #     # print(self, item, kw)
    #     if self.first_item:
    #         pass
    #     else:
    #         if item.isChecked():
    #             kwl = self.note_Keyword_PB.text().split(";")
    #             kwl.append(kw)
    #             self.note_Keyword_PB.setText(";".join(kwl))
    #         else:
    #             kwl = self.note_Keyword_PB.text().split(";")
    #             kwl.remove(kw)
    #             self.note_Keyword_PB.setText(";".join(kwl))

    def walkDir(self, du_flag=0):
        def isValidUUID(idstring, version=1):
            try:
                uuid_obj = uuid.UUID(idstring, version=version) # version 好像影响不大？
            except:
                return False
            else:
                return True
        #
        iu_time = self.note_index.getUpdateTime()
        # 进度条
        self.note_Import_Progress_PD = QProgressDialog()
        self.note_Import_Progress_PD.setWindowTitle("笔记们")
        self.note_Import_Progress_PD.setLabelText("正在导入中")
        self.note_Import_Progress_PD.setMinimumWidth(320)
        self.note_Import_Progress_PD.setModal(True)
        self.note_Import_Progress_PD.setMinimumDuration(0)
        # self.note_Import_Progress_PD.setAutoClose(True)
        self.note_Import_Progress_PD.setCancelButton(None)
        self.note_Import_Progress_PD.hide()
        start_time = datetime.now()
        #
        i = 0
        for type_n in ["Draft", "Archive", "Trash"]:
            path_list = os.listdir(os.path.join(self.note_root_dir, type_n))
            self.note_Import_Progress_PD.setRange(0,len(path_list))
            self.note_Import_Progress_PD.show()
            for path_n in path_list:
                if isValidUUID(path_n):
                    new_note = NotePack(self.note_index) 
                    new_note.id = path_n
                    new_note.path = os.path.join(self.note_root_dir, type_n, path_n)
                    if (du_flag == 1):
                        time_compare1 = (datetime.fromtimestamp(os.path.getatime(new_note.path))>iu_time) #.any()
                        time_compare2 = (datetime.fromtimestamp(os.path.getmtime(new_note.path))>iu_time) #.any()                    
                        if (time_compare1 | time_compare2):
                            new_note.load()
                            i += 1
                            timeelps = str(datetime.now() - start_time)
                            self.note_Import_Progress_PD.setValue(i)
                            self.note_Import_Progress_PD.setLabelText("已有{}条旧笔记导入，用时{}".format(i, timeelps))
                    else:
                        new_note.load()
                        i += 1
                        timeelps = str(datetime.now() - start_time)
                        self.note_Import_Progress_PD.setValue(i)
                        self.note_Import_Progress_PD.setLabelText("已有{}条旧笔记导入，用时{}".format(i, timeelps))
                    # if ((i%10==0) & (i>0)):
                        # print("已有{}记录被导入".format(i))
                        # self.statusBar().showMessage("已有{}记录被导入".format(i))
        self.note_Import_Progress_PD.setValue(100)
        self.note_Import_Progress_PD.hide()          
        if os.path.abspath(os.path.commonpath([self.note_cur_dir, self.note_root_dir])) == os.path.abspath(self.note_root_dir):
            pass # 如果要加载的文件夹本身就是根目录时就不再作重复录入了
        else:
            j = 0
            # for root, dirs, files in os.walk(self.note_cur_dir, topdown=False): 还是别搞这么复杂了
            file_list = os.listdir(self.note_cur_dir)
            self.note_Import_Progress_PD.setRange(0,len(file_list))
            self.note_Import_Progress_PD.setValue(0)
            self.note_Import_Progress_PD.show()
            for file_n in file_list:
                new_note = NotePack(self.note_index)
                f_path = os.path.abspath(os.path.join(self.note_cur_dir, file_n))                
                if (du_flag == 1):
                    time_compare1 = (datetime.fromtimestamp(os.path.getatime(f_path))>iu_time) #.any()
                    time_compare2 = (datetime.fromtimestamp(os.path.getmtime(f_path))>iu_time) #.any()
                    if (time_compare1 | time_compare2):
                        new_note.create(file_path=f_path)
                        i += 1
                        j += 1
                        timeelps = str(datetime.now() - start_time)
                        self.note_Import_Progress_PD.setValue(j)
                        self.note_Import_Progress_PD.setLabelText("已有{}条新笔记，共{}条笔记导入，用时{}".format(j,i,timeelps))
                else:
                    new_note.create(file_path=f_path)
                    i += 1
                    j += 1
                    timeelps = str(datetime.now() - start_time)
                    self.note_Import_Progress_PD.setValue(j)
                    self.note_Import_Progress_PD.setLabelText("已有{}条新笔记，共{}条笔记导入，用时{}".format(j,i,timeelps))
                # if ((i%10==0) & (i>0)):
                    # print("已有{}记录被导入".format(i))
                    # self.statusBar().showMessage("已有{}记录被导入".format(i))
            self.note_Import_Progress_PD.setValue(100)
            self.note_Import_Progress_PD.hide()    
        self.statusBar().showMessage("共有{}记录被导入".format(i))
    
    def addAttachment(self, file_lst):
        for f_p in file_lst:
            if os.path.exists(f_p):
                self.loadAttItem(f_p)
                self.cur_note.addAtt(f_p)

    def delAttachment(self, item):
        cur_att_itm_path = item.data(Qt.UserRole)
        self.cur_note.delAtt(cur_att_itm_path)
        self.note_Attachment_QW.takeItem(self.note_Attachment_QW.row(item))

    def openAttachment(self, item):
        cur_att_itm_path = item.data(Qt.UserRole)
        QDesktopServices.openUrl(QUrl.fromLocalFile(cur_att_itm_path))

    def locAttachment(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.cur_note.att_dir))
        
    def click2Analyze(self):
        self.ana_DLG = Analysis(self)
        self.ana_DLG.show()

