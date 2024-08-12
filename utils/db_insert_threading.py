import csv
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
import threading
from datetime import datetime
import re
from utils.all_rule_replace import CSVProcessor
import logging
from utils.configManager import load_config

# 设置日志配置
logger = logging.getLogger("GlobalLogger")


class CSVtoPostgresInserter:
    def __init__(
        self,
        db_url=None,
        id_replace=True,
    ):
        self.csv_folder = None
        self.db_url = load_config()["db_url"]
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        # 文件list
        self.csv_folder = None
        logger.info("CSVtoPostgresInserter 初始化成功.")

    def filter_latest_csv_files(self):
        latest_files = {}
        pattern = re.compile(r"^(.*?)(?:_(\d{8}\d{4}))?\.csv$")

        for filename in os.listdir(self.csv_folder):
            if filename.endswith(".csv"):
                match = pattern.match(filename)
                if match:
                    table_name = match.group(1)
                    date_str = match.group(2)
                    file_date = (
                        datetime.min
                        if not date_str
                        else datetime.strptime(date_str, "%Y%m%d%H%M")
                    )

                    if (
                        table_name not in latest_files
                        or latest_files[table_name][1] < file_date
                    ):
                        latest_files[table_name] = (filename, file_date)

        return [entry[0] for entry in latest_files.values()]

    def insert_csv_to_postgresql_with_transaction(self):
        session = self.Session()
        try:
            # 过滤文件
            csv_list = self.filter_latest_csv_files()
            for filename in csv_list:
                file_path = os.path.join(self.csv_folder, filename)
                df = pd.read_csv(file_path, dtype=str)
                table_name = re.match(r"^(.*?)(?:_\d{8}\d{4})?\.csv$", filename).group(
                    1
                )
                try:
                    with self.engine.connect() as connection:
                        trans = connection.begin()
                        try:
                            if not self.engine.dialect.has_table(
                                connection, table_name
                            ):
                                logger.info(
                                    f"Table {table_name} does not exist in the database. Skipping {filename}."
                                )
                                continue

                            connection.execute(text(f"DELETE FROM {table_name}"))
                            df.to_sql(
                                table_name,
                                con=connection,
                                if_exists="append",
                                index=False,
                            )
                            trans.commit()
                            logger.info(
                                f"Inserted data from {filename} into {table_name} table."
                            )
                        except Exception as e:
                            trans.rollback()
                            logger.info(
                                f"Failed to insert data from {filename} into {table_name} table. Rolled back."
                            )
                            logger.info(f"Error: {e}")
                except ProgrammingError as pe:
                    logger.info(pe)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.info(f"Transaction failed and was rolled back. Error: {e}")
        finally:
            session.close()

    def repalce_csv_insert2db(self, csv_path):
        """输入一个文件夹/文件路径，先对数据做批量处理，再批量插入CSV数据到PostgreSQL数据库"""
        csvProcessor = CSVProcessor()
        self.csv_folder = csvProcessor.process_csv(csv_path)
        logger.info("CSV数据处理完成,开始连接数据库")
        if self.Session:
            self.insert_csv_to_postgresql_with_transaction()
            logger.info("数据插入完成")
            return True
        else:
            logger.info("数据库连接失败")
            return False


def insert_data(csv_path):
    db_url = "postgresql+psycopg2://postgres:rootroot@localhost:5432/postgres?options=-csearch_path=takusai_tanntai"
    inserter = CSVtoPostgresInserter(db_url, True)
    inserter.repalce_csv_insert2db(csv_path)


if __name__ == "__main__":
    csv_path = r"Z:\WorkSpace\NADJ20007"
    insert_data(csv_path)
