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
from concurrent.futures import ThreadPoolExecutor

# 设置日志配置
logger = logging.getLogger("GlobalLogger")


class DBInsertInterface(QWidget, Ui_DB_Insert):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        config = load_config()
        self.csv_path = config["work_path"]
        self.LineEdit_Path.setText(self.csv_path)
        self.PushButton_Select.clicked.connect(self.show_fileDialog)
        self.PushButton_Excu.clicked.connect(self.start_insertion)
        # self.DBInsertor = CSVtoPostgresInserter()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.TextEdit_Log.append(self.get_files_in_directory())

    def show_fileDialog(self):
        self.csv_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if self.csv_path:
            self.LineEdit_Path.setText(self.csv_path)

    def start_insertion(self):
        self.csv_path = self.LineEdit_Path.text()
        if self.csv_path:
            self.TextEdit_Log.append("Starting insertion...")
            # 异步执行数据库插入任务
            self.future = self.executor.submit(self.insert_data)
            self.future.add_done_callback(self.handle_result)

    def insert_data(self):
        DBInsertor = CSVtoPostgresInserter()
        # 提交任务并获取 Future 对象
        return DBInsertor.repalce_csv_insert2db(self.csv_path)

    def handle_result(self, future):
        try:
            result = future.result()  # 获取返回值
            if result:
                self.TextEdit_Log.append("Data insertion completed successfully.")
            else:
                self.TextEdit_Log.append("Data insertion failed.")
        except Exception as e:
            self.TextEdit_Log.append(f"Task failed with exception: {str(e)}")

    def get_files_in_directory(self):
        # 获取路径下的所有文件和文件夹
        all_entries = os.listdir(self.csv_path)
        # 过滤掉文件夹，只保留文件
        files = [
            entry
            for entry in all_entries
            if os.path.isfile(os.path.join(self.csv_path, entry))
        ]
        # 将文件列表转换为字符串，每个文件名一行
        return "当前文件下的csv文件 \n".join(files)
