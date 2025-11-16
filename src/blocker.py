# filepath: src\blocker.py
import time
from datetime import datetime
import psutil
import tkinter as tk
from tkinter import messagebox
import os
import win32gui
import win32con
import win32process
import threading

# 导入路径辅助函数
from config_loader import (
    get_disabled_flag_path,
    load_config,
)

# 导入日志工具
from logger_util import log_message  # 新增导入

# --- 在这里直接设置你的固定密码 ---
UNLOCK_PASSWORD = "123456"
# ---------------------------------

# 状态文件，用于控制功能的开启和关闭
# 使用集中式路径函数
DISABLED_FLAG_FILE = get_disabled_flag_path()

unlocked_process_names = set()


# 新增：获取所有浏览器窗口句柄
def get_browser_window_handles(process_names):
    """获取指定进程名对应的所有窗口句柄"""
    handles = []

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):  # 只处理可见窗口
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(process_id)
                if proc.name() in process_names:
                    handles.append(hwnd)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # log_message(f"获取窗口进程信息失败: {e}", level="DEBUG") # 避免过多日志
                pass
        return True

    # 枚举所有顶级窗口
    win32gui.EnumWindows(callback, None)
    return handles


# 新增：最小化指定窗口
def minimize_windows(handles):
    """最小化指定句柄的窗口"""
    for hwnd in handles:
        try:
            # 检查窗口是否已最小化
            if not (win32gui.GetWindowPlacement(hwnd)[1] == win32con.SW_SHOWMINIMIZED):
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        except Exception as e:
            log_message(f"最小化窗口失败: {e}", level="ERROR")


def is_blocking_enabled():
    """检查功能是否被禁用"""
    return not os.path.exists(DISABLED_FLAG_FILE)


def is_time_restricted(time_ranges):
    """检查当前时间是否落在任何一个禁用时间段内"""
    if not time_ranges:
        return False
    now = datetime.now().time()
    for time_range in time_ranges:
        try:
            start_time = datetime.strptime(time_range.get("开始时间"), "%H:%M").time()
            end_time = datetime.strptime(time_range.get("结束时间"), "%H:%M").time()
            if start_time <= now <= end_time:
                return True
        except (ValueError, TypeError, AttributeError) as e:
            log_message(f"解析禁用时间段失败: {time_range}，错误: {e}", level="ERROR")
            continue
    return False


def ask_for_password(restricted_process_names):
    """弹出一个强置顶的密码输入框，使用硬编码的密码"""
    # 获取并最小化所有浏览器窗口
    browser_handles = get_browser_window_handles(restricted_process_names)
    minimize_windows(browser_handles)

    # 记录密码错误次数
    error_count = 0

    def check_password():
        nonlocal error_count
        if password_entry.get() == UNLOCK_PASSWORD:
            root.is_correct = True
            log_message("密码验证成功，已解锁。", level="INFO")
            root.destroy()
        else:
            error_count += 1
            if error_count >= 3:
                # 第三次错误显示嘲讽窗口
                mock = tk.Toplevel(root)
                mock.title("提示")
                mock.attributes("-topmost", True)
                tk.Label(mock, text="没mm还玩nm", font=("Arial", 12)).pack(
                    padx=20, pady=10
                )
                # 自定义按钮文本
                tk.Button(mock, text="你™再试试", command=mock.destroy).pack(pady=5)

                # 居中显示
                mock.update_idletasks()
                x = (
                    root.winfo_x()
                    + (root.winfo_width() // 2)
                    - (mock.winfo_width() // 2)
                )
                y = (
                    root.winfo_y()
                    + (root.winfo_height() // 2)
                    - (mock.winfo_height() // 2)
                )
                mock.geometry(f"+{x}+{y}")
                log_message("密码错误次数过多，显示嘲讽窗口。", level="WARNING")

                # 等待嘲讽窗口关闭
                root.wait_window(mock)
                error_count = 0  # 重置错误计数
            else:
                messagebox.showerror(
                    "密码错误",
                    f"密码不正确，还剩{3 - error_count}次机会！",
                    parent=root,
                )
                log_message(
                    f"密码不正确，还剩{3 - error_count}次机会。", level="WARNING"
                )
            password_entry.delete(0, tk.END)

    # 关闭所有指定进程的函数
    def kill_restricted_processes():
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"] in restricted_process_names:
                    proc.kill()
                    log_message(
                        f"已关闭进程: {proc.info['name']} (PID: {proc.info['pid']})"
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception as e:
                log_message(f"尝试关闭进程失败: {e}", level="ERROR")

    # 定时检查并最小化窗口的函数
    def check_windows():
        if root.winfo_exists():  # 检查窗口是否仍存在
            new_handles = get_browser_window_handles(restricted_process_names)
            minimize_windows(new_handles)
            root.after(2000, check_windows)  # 2秒后再次检查

    root = tk.Tk()
    root.withdraw()  # 先隐藏主窗口
    root.title("访问限制")

    # 增强置顶模式：设置为系统级置顶（类似任务管理器）
    root.attributes("-topmost", True)  # 基础置顶
    # 设置窗口扩展样式，实现更高级的置顶
    hwnd = root.winfo_id()
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    # 添加工具窗口样式和顶层窗口样式
    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        ex_style | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TOPMOST,
    )

    # 强制刷新窗口样式
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        0,
        0,
        0,
        0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
    )

    root.attributes("-toolwindow", True)  # 工具窗口样式（无最小化按钮）
    root.resizable(False, False)  # 禁止调整窗口大小

    # 创建对话框内容
    dialog_frame = tk.Frame(root, padx=20, pady=10)
    dialog_frame.pack()

    tk.Label(
        dialog_frame, text="该应用在当前时间段被限制访问。\n请输入密码以临时解锁："
    ).pack(pady=(0, 10))
    password_entry = tk.Entry(dialog_frame, show="*", width=20)
    password_entry.pack(pady=5)
    password_entry.focus_set()  # 自动获取焦点
    password_entry.bind("<Return>", lambda event: check_password())  # 支持回车确认
    tk.Button(dialog_frame, text="确定", command=check_password).pack(pady=5)

    # 居中显示窗口
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    root.deiconify()  # 显示窗口

    # 关闭窗口时视为密码错误（需要终止进程）
    root.is_correct = False

    def on_close():
        root.is_correct = False
        kill_restricted_processes()  # 关闭窗口时杀死所有受限进程
        log_message("访问限制密码对话框已关闭，终止受限进程。", level="WARNING")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)  # 捕获关闭事件

    # 启动定时窗口检查（每2秒一次）
    root.after(0, check_windows)  # 立即执行第一次检查

    root.mainloop()

    return root.is_correct


# 这是 find_and_kill_processes 函数，它确实是定义在这里的
def find_and_kill_processes(config):
    if not is_blocking_enabled():
        unlocked_process_names.clear()
        return

    restricted_process_names = config.get("限制进程列表", [])
    time_ranges = config.get("禁用时间段", [])

    if not is_time_restricted(time_ranges):
        unlocked_process_names.clear()
        return

    # 收集所有正在运行的受限进程名
    # running_restricted_procs = set() # 此变量未使用，可以移除
    # for proc in psutil.process_iter(["pid", "name"]):
    #     try:
    #         proc_name = proc.info["name"]
    #         if proc_name in restricted_process_names:
    #             running_restricted_procs.add(proc_name)
    #     except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
    #         pass

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            proc_name = proc.info["name"]
            if (
                proc_name in restricted_process_names
                and proc_name not in unlocked_process_names
            ):
                log_message(f"检测到受限进程: {proc_name} (PID: {proc.pid})")
                # 传递限制进程列表给密码框函数
                if ask_for_password(restricted_process_names):
                    log_message(f"密码正确，已解锁所有 {proc_name} 进程")
                    unlocked_process_names.add(proc_name)
                else:
                    # 密码错误，终止所有同名进程
                    log_message(f"密码错误，终止所有 {proc_name} 进程", level="WARNING")
                    for p_to_kill in psutil.process_iter(["pid", "name"]):
                        try:
                            if p_to_kill.info["name"] == proc_name:
                                p_to_kill.kill()
                                log_message(
                                    f"已强制关闭进程: {p_to_kill.info['name']} (PID: {p_to_kill.pid})",
                                    level="INFO",
                                )
                        except (
                            psutil.NoSuchProcess,
                            psutil.AccessDenied,
                            psutil.ZombieProcess,
                        ) as e:
                            log_message(
                                f"关闭进程 {proc_name} (PID: {p_to_kill.pid}) 失败: {e}",
                                level="ERROR",
                            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            log_message(f"处理进程时发生错误: {e}", level="ERROR")


# 修改 start_blocking_loop 函数以接受共享配置和重载事件
def start_blocking_loop(config_wrapper, config_reload_event):  # <-- 接收共享配置和事件
    """启动持续监控的循环"""
    log_message("监控服务已启动。")
    while True:
        try:
            # 检查是否有配置需要重新加载的信号
            if config_reload_event.is_set():
                log_message("收到配置更新信号，正在重新加载配置...")
                new_config = load_config()
                if new_config is not None:
                    config_wrapper["config"] = new_config  # 更新共享配置
                    log_message("配置已成功重新加载。")
                else:
                    log_message(
                        "警告: 重新加载配置失败，将继续使用当前配置。", level="WARNING"
                    )
                config_reload_event.clear()  # 清除信号

            current_config = config_wrapper["config"]  # 使用当前活跃的配置

            if current_config is None:
                log_message(
                    "错误: 监控循环中没有可用配置。等待有效配置。", level="ERROR"
                )
                time.sleep(5)  # 等待更长时间，直到有配置可用
                continue

            find_and_kill_processes(current_config)  # 传递当前配置
            time.sleep(2)
        except Exception as e:
            log_message(f"监控循环发生错误: {e}", level="ERROR")
            time.sleep(10)
