# filepath: src\config_loader.py
import sys
import json
import os

# 导入日志工具
from logger_util import log_message  # 新增导入

CONFIG_FILE_NAME = "ZenSurfSetting.json"  # 配置文件的名称已修改
APP_DATA_DIR_NAME = "ZenSurf"
DISABLED_FLAG_FILE_NAME = "disabled.flag"


def get_app_data_path():
    """获取AppData/Roaming/ZenSurf目录，并确保其存在"""
    # 无论是否打包，都使用APPDATA目录
    appdata_path = os.path.join(os.getenv("APPDATA"), APP_DATA_DIR_NAME)
    if not os.path.exists(appdata_path):
        os.makedirs(appdata_path)
    return appdata_path


def get_config_path():
    """获取配置文件的绝对路径，始终指向AppData/Roaming/ZenSurf"""
    return os.path.join(get_app_data_path(), CONFIG_FILE_NAME)


def get_disabled_flag_path():
    """获取禁用标志文件的绝对路径，始终指向AppData/Roaming/ZenSurf"""
    return os.path.join(get_app_data_path(), DISABLED_FLAG_FILE_NAME)


def get_log_dir_path():
    """获取日志文件目录的绝对路径，并确保其存在"""
    log_dir_path = os.path.join(get_app_data_path(), "logs")
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path)
    return log_dir_path


def get_default_config_data():
    """返回默认配置数据，包含新的限制进程"""
    return {
        "_comment1": "在这里添加需要被限制的程序进程名 (例如: chrome.exe)。每个进程名一行。",
        "限制进程列表": [
            "chrome.exe",
            "msedge.exe",
            "Taskmgr.exe",
        ],
        "_comment2": "在这里设置一个或多个禁用时间段 (24小时制)。每行一个，格式: [注释:]HH:MM-HH:MM",
        "禁用时间段": [
            {"_comment": "测试", "开始时间": "09:00", "结束时间": "16:00"},
        ],
    }


def create_default_config_file_if_not_exists():
    """如果配置文件不存在，则创建一个带默认内容的配置文件"""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        default_config = get_default_config_data()
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            log_message(f"配置文件 {CONFIG_FILE_NAME} 已创建在 {config_path}。")
            return True
        except IOError as e:
            log_message(
                f"错误：无法创建配置文件 {config_path}。原因: {e}", level="ERROR"
            )
            return False
    return True  # 文件已存在


def load_config():
    """加载配置文件"""
    config_path = get_config_path()

    # 确保配置文件夹和文件存在
    if not create_default_config_file_if_not_exists():
        return None  # 无法创建默认配置

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            if not file_content.strip():  # 检查文件是否为空
                log_message("配置文件为空，加载默认配置。", level="WARNING")
                return get_default_config_data()
            return json.loads(file_content)
    except (json.JSONDecodeError, IOError) as e:
        log_message(
            f"错误：无法加载或解析配置文件 {config_path}。请检查文件格式是否正确。原因: {e}",
            level="ERROR",
        )
        log_message("尝试加载默认配置数据作为备用。", level="INFO")
        return get_default_config_data()  # 备用方案：返回硬编码的默认数据


def save_config(config_data):
    """保存配置到文件"""
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        log_message(f"配置已保存到 {config_path}")
        return True
    except IOError as e:
        log_message(f"错误：无法保存配置文件 {config_path}。原因: {e}", level="ERROR")
        return False
