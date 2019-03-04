import sys
from PyQt5.QtWidgets import QApplication
from modules.importDialog import ImportDirs
from modules.window import MainWindow

def main(argv):
    app = QApplication(sys.argv)
    imt_Dlg = ImportDirs()
    if (not imt_Dlg.exec_()):
        # sys.exit(0)
        dl = imt_Dlg.dir_list
        
        win = MainWindow(dl)
        win.show()

        sys.exit(app.exec_())

if __name__ == '__main__':
    main(sys.argv)
    
