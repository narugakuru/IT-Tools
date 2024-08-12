import csv
from tracemalloc import start
from qfluentwidgets.components import dialog_box, FolderListDialog
from PySide6.QtWidgets import QWidget, QFileDialog
from utils.configManager import load_config, load_start_cyclic_values
from view.Ui_db_insert import Ui_DB_Insert
from utils.db_insert_threading import CSVtoPostgresInserter
import logging
import utils.logger_setup as log
import threading
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QTableView,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtSql import QSqlDatabase, QSqlRelationalTableModel, QSqlRelation
import sys, os

# 设置日志配置
logger = logging.getLogger("GlobalLogger")


class DBInsertInterface(QWidget, Ui_DB_Insert):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        config = load_config()
        self.LineEdit_Path.setText(config["work_path"])
        self.PushButton_Select.clicked.connect(self.show_fileDialog)
        self.PushButton_Excu.clicked.connect(self.start_insertion)
        self.Excutor = CSVtoPostgresInserter()
        self.TextEdit_Log.append(self.get_files_in_directory(config["work_path"]))

    def show_fileDialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if folder_path:
            self.LineEdit_Path.setText(folder_path)

    def start_insertion(self):
        if self.LineEdit_Path.text():
            logger.info("执行插入")
            self.start_threading(self.LineEdit_Path.text())
            logger.info("数据插入结束")
            self.TextEdit_Log.append(log.get_logs())
            log.clear_logs()
            self.TextEdit_Log.append("数据插入结束")

    def start_threading(self, csv_path):
        self.Excutor = threading.Thread(
            target=self.Excutor.start_repalce_csv_insert2db, args={csv_path}
        )
        self.Excutor.start()
        # self.Excutor.join()

    def get_files_in_directory(self, directory_path):
        # 获取路径下的所有文件和文件夹
        all_entries = os.listdir(directory_path)
        # 过滤掉文件夹，只保留文件
        files = [
            entry
            for entry in all_entries
            if os.path.isfile(os.path.join(directory_path, entry))
        ]
        # 将文件列表转换为字符串，每个文件名一行
        return "当前文件下的csv文件 \n".join(files)
