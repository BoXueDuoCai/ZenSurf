# filepath: src\logger_util.py
import sys
from datetime import datetime
from collections import deque

_log_queue_ref = None
_log_file_obj_ref = None
_original_stdout_ref = sys.__stdout__  # 始终保留原始的 stdout 引用
_original_stderr_ref = sys.__stderr__  # 始终保留原始的 stderr 引用


class ConsoleRedirector:
    """
    一个用于重定向 sys.stdout/stderr 的类，
    同时将输出写入日志队列和日志文件，
    并可选择性地抑制向原始控制台输出。
    """

    def __init__(
        self, target_stream_name, log_q, log_file=None, suppress_console_output=True
    ):
        self.target_stream_name = target_stream_name  # 'stdout' 或 'stderr'
        self.log_q = log_q
        self.log_file = log_file
        self.suppress_console_output = suppress_console_output

    def write(self, text):
        # 如果不抑制控制台输出，则先写入原始流
        if not self.suppress_console_output:
            if self.target_stream_name == "stdout":
                _original_stdout_ref.write(text)
            else:  # stderr
                _original_stderr_ref.write(text)

        # 始终写入日志队列供 GUI 显示
        if self.log_q is not None:
            self.log_q.append(text)

        # 如果日志文件对象可用，则写入日志文件
        if hasattr(self.log_file, "write"):
            try:
                self.log_file.write(text)
                self.log_file.flush()
            except Exception as e:
                # 如果日志文件写入失败，则将错误记录到原始 stderr (以防万一控制台未被抑制)
                _original_stderr_ref.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] 写入日志文件失败: {e}\n"
                )

    def flush(self):
        # 只有在不抑制控制台输出时才刷新原始流
        if not self.suppress_console_output:
            if self.target_stream_name == "stdout":
                _original_stdout_ref.flush()
            else:  # stderr
                _original_stderr_ref.flush()
        if hasattr(self.log_file, "flush"):
            try:
                self.log_file.flush()
            except Exception as e:
                _original_stderr_ref.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] 刷新日志文件失败: {e}\n"
                )


def init_logging(log_q_instance, log_file_instance, suppress_console_output=True):
    """
    初始化全局日志对象并重定向 sys.stdout/stderr。
    如果 suppress_console_output 为 True，则输出将不会进入原始控制台。
    """
    global _log_queue_ref, _log_file_obj_ref
    _log_queue_ref = log_q_instance
    _log_file_obj_ref = log_file_instance

    sys.stdout = ConsoleRedirector(
        "stdout", _log_queue_ref, _log_file_obj_ref, suppress_console_output
    )
    sys.stderr = ConsoleRedirector(
        "stderr", _log_queue_ref, _log_file_obj_ref, suppress_console_output
    )


def log_message(message, level="INFO"):
    """
    记录带有时间戳和级别的消息。
    此消息将通过当前的 sys.stdout (或 sys.stderr 对于 ERROR 级别) 写入。
    其行为 (控制台/文件/GUI) 取决于 sys.stdout/stderr 如何被重定向。
    """
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    # 对于 ERROR 级别，使用 sys.stderr 流，否则使用 sys.stdout 流
    stream_to_write = sys.stderr if level == "ERROR" else sys.stdout
    stream_to_write.write(f"{timestamp} [{level}] {message}\n")


def get_log_queue():
    """返回全局日志队列，供 UI 更新使用。"""
    return _log_queue_ref


def get_original_stdout():
    """返回原始的 sys.stdout 引用。"""
    return _original_stdout_ref


def get_original_stderr():
    """返回原始的 sys.stderr 引用。"""
    return _original_stderr_ref
