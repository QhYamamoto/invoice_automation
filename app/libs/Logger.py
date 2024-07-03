import os
import inspect
import logging
import traceback
import sys
import shortuuid
from datetime import datetime
from logging import getLogger, Formatter, INFO
from pytz import timezone


class Logger():
    def __get_logger(
            self,
            file_name: str,
            line_no: int,
            trace_shown: bool = True,
    ) -> logging.LoggerAdapter:
        """
        メッセージIDを指定して新規のLoggerインスタンスを取得する

        Args:
            file_name (str): ファイル名
            line_no (int): 出力する行数
            trace_shown (bool): traceを表示するかを示すフラグ
        """
        logger = getLogger(shortuuid.uuid())
        logger.propagate = False
        logger.setLevel(logging.INFO)

        dt_now = datetime.now()
        log_dir = "/app/logs"
        log_file = dt_now.strftime("%Y.log")

        # ディレクトリが存在しない場合は作成
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(os.path.join(log_dir, log_file))
        file_handler.setLevel(logging.INFO)

        log_format = "%(asctime)s { loglevel: %(levelname)s, " \
            "file: %(file_name)s, " \
            "line: %(line_no)s, "\
            "trace: %(trace)s, " \
            "message_content: %(message)s }"

        formatter = Formatter(log_format, "%Y-%m-%d %H:%M:%S")
        formatter.converter = lambda *args: datetime.now(
            timezone("Asia/Tokyo")
        ).timetuple()
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        trace = (
            traceback.format_exc().strip().split("\n")
            if trace_shown else ""
        )

        return logging.LoggerAdapter(logger, {
            "file_name": file_name,
            "line_no": line_no,
            "trace": trace,
        })

    def info(self, message: str) -> None:
        """INFOログ出力

        Args:
            message (str): メッセージ
        """
        # 呼び出し元のファイル名
        file_name = inspect.currentframe().f_back.f_code.co_filename
        # 呼び出し元の行番号
        line_no = inspect.currentframe().f_back.f_lineno

        logger = self.__get_logger(
            file_name=file_name,
            line_no=line_no,
            trace_shown=False
        )
        logger.info(message)

    def error(self, message: str) -> None:
        """ERRORログ出力

        Args:
            message (str): メッセージ
        """

        # 例外発生箇所のファイル名・行番号を取得
        exc_info = sys.exc_info()
        file_name = exc_info[2].tb_frame.f_code.co_filename
        line_no = exc_info[2].tb_lineno

        logger = self.__get_logger(
            file_name=file_name,
            line_no=line_no,
        )
        logger.error(message)
