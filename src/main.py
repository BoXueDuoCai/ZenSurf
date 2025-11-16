# filepath: src\main.py
import sys
import os
import psutil
import time
import threading

import tkinter as tk # 延迟导入 tkinter，以便先设置日志重定向
from tkinter import messagebox, scrolledtext # 延迟导入
from datetime import datetime

import tkinter.ttk as ttk # 延迟导入
from collections import deque

import keyboard

from config_loader import (
    load_config,
    save_config,
    get_config_path,
    get_disabled_flag_path,
    APP_DATA_DIR_NAME,
    get_app_data_path,
    get_log_dir_path,
)

from blocker import (
    UNLOCK_PASSWORD,
    get_browser_window_handles,
    minimize_windows,
    is_blocking_enabled,
    is_time_restricted,
    ask_for_password,
    find_and_kill_processes,
    start_blocking_loop,
)

# 导入日志工具
from logger_util import (
    log_message,
    init_logging,
    get_log_queue,
    get_original_stdout,
    get_original_stderr,
)

APP_NAME = "ZenSurf"
DISABLED_FLAG_FILE = get_disabled_flag_path()

current_config_wrapper = {"config": None}
config_reload_event = threading.Event()


# ask_settings_password 函数 (无改动，内部已使用 log_message)
def ask_settings_password(parent, correct_password, title="ZenSurf 设置需要密码"):
    """
    弹出一个密码输入框，验证密码。
    返回 True 如果密码正确，否则返回 False。
    这个函数用于设置界面，不涉及进程最小化或终止。
    """
    # import tkinter as tk  # 确保 Tkinter 在此函数内部导入
    # from tkinter import messagebox  # 确保 Tkinter 在此函数内部导入

    password_correct = False
    password_dialog = tk.Toplevel(parent)
    password_dialog.title(title)
    password_dialog.geometry("300x150")
    password_dialog.attributes("-topmost", True)
    password_dialog.resizable(False, False)

    def on_dialog_close():
        nonlocal password_correct
        password_correct = False
        password_dialog.destroy()
        log_message("设置密码验证对话框已关闭。", level="INFO")

    password_dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)

    label = tk.Label(password_dialog, text="请输入密码以访问设置：", font=("宋体", 10))
    label.pack(pady=10)

    password_entry = tk.Entry(password_dialog, show="*", font=("宋体", 10))
    password_entry.pack(pady=5)
    password_entry.focus_set()

    def check_password_in_settings(event=None):
        nonlocal password_correct
        if password_entry.get() == correct_password:
            password_correct = True
            log_message("设置密码验证成功。", level="INFO")
            password_dialog.destroy()
        else:
            messagebox.showerror("错误", "密码不正确！", parent=password_dialog)
            log_message("设置密码不正确。", level="WARNING")
            password_entry.delete(0, tk.END)  # 清空输入框以便重新输入

    password_entry.bind("<Return>", check_password_in_settings)

    submit_button = tk.Button(
        password_dialog,
        text="确定",
        command=check_password_in_settings,
        font=("宋体", 10),
    )
    submit_button.pack(pady=10)

    password_dialog.update_idletasks()
    x = (
        parent.winfo_x()
        + (parent.winfo_width() // 2)
        - (password_dialog.winfo_width() // 2)
    )
    y = (
        parent.winfo_y()
        + (parent.winfo_height() // 2)
        - (password_dialog.winfo_height() // 2)
    )
    password_dialog.geometry(f"+{x}+{y}")

    parent.wait_window(password_dialog)  # 等待密码对话框关闭
    return password_correct


# SettingsApp 类 (无改动，内部已使用 log_message)
class SettingsApp:
    def __init__(self, master_toplevel):
        import tkinter as tk  # 确保 Tkinter 在此函数内部导入
        from tkinter import messagebox, scrolledtext  # 确保 Tkinter 在此函数内部导入
        import tkinter.ttk as ttk  # 确保 Tkinter 在此函数内部导入

        self.master = master_toplevel
        self.master.title("ZenSurf 设置")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master.resizable(True, True)
        self.master.attributes("-topmost", True)

        self.config_data = load_config()
        if self.config_data is None:
            messagebox.showerror(
                "错误", "无法加载配置文件，请检查文件权限或格式。", parent=self.master
            )
            log_message("错误：无法加载配置文件，请检查文件权限或格式。", level="ERROR")
            self.master.destroy()
            return

        self.setup_ui()
        self.load_settings_into_ui()
        self.master.deiconify()
        self.master.lift()
        self.master.focus_force()
        self.center_window()

        self.log_queue_ref = get_log_queue()  # 获取共享的日志队列
        self.update_log_widget()

    def center_window(self):
        self.master.update_idletasks()
        x = (self.master.winfo_screenwidth() // 2) - (self.master.winfo_width() // 2)
        y = (self.master.winfo_screenheight() // 2) - (self.master.winfo_height() // 2)
        self.master.geometry(f"+{x}+{y}")

    def setup_ui(self):
        import tkinter.ttk as ttk  # 确保 Tkinter 在此函数内部导入

        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.settings_frame = tk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="设置")
        self._setup_settings_tab(self.settings_frame)

        self.log_frame = tk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="日志")
        self._setup_log_tab(self.log_frame)

    def _setup_settings_tab(self, parent_frame):
        import tkinter as tk  # 确保 Tkinter 在此函数内部导入
        from tkinter import scrolledtext  # 确保 Tkinter 在此函数内部导入

        process_frame = tk.LabelFrame(
            parent_frame, text="限制进程列表 (每行一个进程名，例如: chrome.exe)"
        )
        process_frame.pack(padx=5, pady=5, fill="both", expand=True)
        self.process_names_text = scrolledtext.ScrolledText(
            process_frame, width=60, height=8, wrap=tk.WORD, font=("宋体", 10)
        )
        self.process_names_text.pack(padx=5, pady=5, fill="both", expand=True)

        time_frame = tk.LabelFrame(
            parent_frame, text="禁用时间段 (每行一个，格式: [注释:] HH:MM-HH:MM)"
        )
        time_frame.pack(padx=5, pady=5, fill="both", expand=True)
        self.time_ranges_text = scrolledtext.ScrolledText(
            time_frame, width=60, height=8, wrap=tk.WORD, font=("宋体", 10)
        )
        self.time_ranges_text.pack(padx=5, pady=5, fill="both", expand=True)

        self.blocking_enabled_var = tk.BooleanVar()
        self.blocking_checkbox = tk.Checkbutton(
            parent_frame,
            text="启用应用限制功能",
            variable=self.blocking_enabled_var,
            font=("宋体", 10),
        )
        self.blocking_checkbox.pack(padx=5, pady=5, anchor="w")

        button_frame = tk.Frame(parent_frame)
        button_frame.pack(pady=10)
        tk.Button(
            button_frame,
            text="保存设置",
            command=self.save_settings,
            font=("宋体", 10),
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            button_frame, text="取消", command=self.on_close, font=("宋体", 10)
        ).pack(side=tk.LEFT, padx=5)

    def _setup_log_tab(self, parent_frame):
        from tkinter import scrolledtext  # 确保 Tkinter 在此函数内部导入

        self.log_display = scrolledtext.ScrolledText(
            parent_frame,
            width=80,
            height=20,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state="disabled",
        )
        self.log_display.pack(padx=5, pady=5, fill="both", expand=True)

        log_button_frame = tk.Frame(parent_frame)
        log_button_frame.pack(pady=5)
        tk.Button(
            log_button_frame,
            text="清空日志",
            command=self.clear_log_display,
            font=("宋体", 10),
        ).pack(side=tk.LEFT, padx=5)

    def update_log_widget(self):
        while (
            self.log_queue_ref and self.log_queue_ref
        ):  # 检查 log_queue_ref 是否存在且非空
            message = self.log_queue_ref.popleft()
            self.log_display.configure(state="normal")
            self.log_display.insert(tk.END, message)
            self.log_display.see(tk.END)
            self.log_display.configure(state="disabled")
        self.master.after(200, self.update_log_widget)

    def clear_log_display(self):
        self.log_display.configure(state="normal")
        self.log_display.delete(1.0, tk.END)
        self.log_display.configure(state="disabled")
        if self.log_queue_ref:
            self.log_queue_ref.clear()
        log_message("日志显示已清空。", level="INFO")

    def load_settings_into_ui(self):
        processes = self.config_data.get("限制进程列表", [])
        self.process_names_text.delete(1.0, tk.END)
        self.process_names_text.insert(tk.END, "\n".join(processes))

        time_ranges = self.config_data.get("禁用时间段", [])
        time_ranges_str_list = []
        for tr in time_ranges:
            comment = tr.get("_comment", "")
            start = tr.get("开始时间", "00:00")
            end = tr.get("结束时间", "00:00")
            if comment:
                time_ranges_str_list.append(f"{comment}: {start}-{end}")
            else:
                time_ranges_str_list.append(f"{start}-{end}")
        self.time_ranges_text.delete(1.0, tk.END)
        self.time_ranges_text.insert(tk.END, "\n".join(time_ranges_str_list))

        disabled_flag_exists = os.path.exists(get_disabled_flag_path())
        self.blocking_enabled_var.set(not disabled_flag_exists)

    def save_settings(self):
        import tkinter as tk  # 确保 Tkinter 在此函数内部导入
        from tkinter import messagebox  # 确保 Tkinter 在此函数内部导入

        new_config_data = self.config_data.copy()

        processes_str = self.process_names_text.get(1.0, tk.END).strip()
        new_config_data["限制进程列表"] = [
            line.strip() for line in processes_str.split("\n") if line.strip()
        ]

        time_ranges_raw_input = self.time_ranges_text.get(1.0, tk.END).strip()
        new_time_ranges = []
        for line in time_ranges_raw_input.split("\n"):
            line = line.strip()
            if not line:
                continue

            comment_part = ""
            time_part = line

            if ":" in line and "-" in line:
                parts = line.split(":", 1)
                if len(parts) > 1 and "-" in parts[1]:
                    comment_candidate = parts[0].strip()
                    time_candidate = parts[1].strip()
                    try:
                        datetime.strptime(time_candidate.split("-")[0].strip(), "%H:%M")
                        datetime.strptime(time_candidate.split("-")[1].strip(), "%H:%M")
                        comment_part = comment_candidate
                        time_part = time_candidate
                    except ValueError:
                        pass  # 如果时间部分格式不正确，则不使用注释，按纯时间处理

            try:
                start_time_str, end_time_str = time_part.split("-")
                start_time = datetime.strptime(start_time_str.strip(), "%H:%M").time()
                end_time = datetime.strptime(end_time_str.strip(), "%H:%M").time()

                entry = {}
                if comment_part:
                    entry["_comment"] = comment_part
                entry["开始时间"] = start_time.strftime("%H:%M")
                entry["结束时间"] = end_time.strftime("%H:%M")

                new_time_ranges.append(entry)
            except ValueError:
                messagebox.showerror(
                    "格式错误",
                    f"时间段 '{line}' 格式不正确。\n请使用 'HH:MM-HH:MM' 或 '注释: HH:MM-HH:MM' 格式。",
                    parent=self.master,
                )
                log_message(
                    f"时间段 '{line}' 格式不正确，保存设置失败。", level="ERROR"
                )
                return

        new_config_data["禁用时间段"] = new_time_ranges

        disabled_flag_path = get_disabled_flag_path()
        if self.blocking_enabled_var.get():
            if os.path.exists(disabled_flag_path):
                os.remove(disabled_flag_path)
                log_message("应用限制功能已启用。", level="INFO")
        else:
            if not os.path.exists(disabled_flag_path):
                with open(disabled_flag_path, "w") as f:
                    f.write("disabled")
                log_message("应用限制功能已禁用。", level="INFO")

        if save_config(new_config_data):
            self.config_data = new_config_data
            config_reload_event.set()
            messagebox.showinfo("成功", "设置已保存。", parent=self.master)
            log_message("设置已成功保存到文件。", level="INFO")
            self.on_close()
        else:
            messagebox.showerror("错误", "保存设置失败。", parent=self.master)
            log_message("保存设置失败。", level="ERROR")

    def on_close(self):
        self.master.destroy()


# HotkeyThread 类 (无改动，内部已使用 log_message)
class HotkeyThread(threading.Thread):
    def __init__(self, main_tk_root):
        super().__init__()
        self.daemon = True
        self.main_tk_root = main_tk_root

    def run(self):
        log_message("Hotkey Listener: 正在注册热键 'win+ctrl+shift+w'...")
        try:
            keyboard.add_hotkey("win+ctrl+shift+w", self.hotkey_callback)
            log_message("Hotkey Listener: 热键已注册。等待热键按下...")
            keyboard.wait()
            log_message("Hotkey Listener: 热键监听线程已停止。")
        except Exception as e:
            log_message(f"Hotkey Listener: 注册热键时发生错误: {e}", level="ERROR")

    def hotkey_callback(self):
        log_message(
            "Hotkey Listener: 热键 (Win+Ctrl+Shift+W) 已按下! 正在启动设置界面..."
        )
        self.main_tk_root.after_idle(self.launch_settings_ui_safe)

    def launch_settings_ui_safe(self):
        import tkinter as tk  # 确保 Tkinter 在此函数内部导入

        for child in self.main_tk_root.winfo_children():
            if isinstance(child, tk.Toplevel) and child.title() == "ZenSurf 设置":
                child.lift()
                child.focus_force()
                return

        if ask_settings_password(self.main_tk_root, UNLOCK_PASSWORD):
            settings_toplevel = tk.Toplevel(self.main_tk_root)
            SettingsApp(settings_toplevel)
        else:
            log_message(
                "Hotkey Listener: 密码验证失败，设置界面未打开。", level="WARNING"
            )


def handle_stop():
    if getattr(sys, "frozen", False):
        process_name = os.path.basename(sys.executable)
    else:
        process_name = "python.exe"
        script_path_lower = os.path.abspath(__file__).lower()

    current_pid = os.getpid()
    stopped_any = False
    log_message("尝试查找并终止现有 ZenSurf 进程...", level="INFO")
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            is_our_process = False
            if getattr(sys, "frozen", False):
                if (
                    proc.info["name"].lower() == process_name.lower()
                    and proc.info["pid"] != current_pid
                ):
                    is_our_process = True
            else:
                cmdline_str = " ".join(proc.info["cmdline"]).lower()
                if (
                    proc.info["name"].lower() in ["python.exe", "pythonw.exe"]
                    and script_path_lower in cmdline_str
                    and proc.info["pid"] != current_pid
                ):
                    is_our_process = True

            if is_our_process:
                p = psutil.Process(proc.info["pid"])
                log_message(
                    f"发现并尝试终止进程: {proc.info['name']} (PID: {p.pid}, Cmd: {' '.join(p.cmdline())})"
                )
                p.terminate()
                try:
                    p.wait(timeout=3)
                except psutil.TimeoutExpired:
                    log_message(f"进程 {p.pid} 未响应，强制终止。", level="WARNING")
                    p.kill()
                stopped_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            log_message(
                f"处理进程 {proc.info.get('name', 'N/A')} (PID: {proc.info.get('pid', 'N/A')}) 时发生错误: {e}",
                level="ERROR",
            )

    if not stopped_any:
        log_message("未找到运行中的 ZenSurf 进程。", level="INFO")


def handle_enable_disable(command):
    if command == "disable":
        with open(get_disabled_flag_path(), "w") as f:
            f.write("disabled")
        log_message("功能已禁用。受限应用将不再被拦截。", level="INFO")
    elif command == "enable":
        if os.path.exists(get_disabled_flag_path()):
            os.remove(get_disabled_flag_path())
        log_message("功能已启用。", level="INFO")


def print_usage():
    # 此函数专用于命令行帮助，因此应始终输出到原始 stdout
    get_original_stdout().write(
        f"""
用法: python main.py [command]

这是一个应用限制工具。

无参数:
  以静默模式启动并监控应用，并监听快捷键 Win+Ctrl+Shift+W 打开设置界面。

可用命令:
  stop              - 停止正在运行的所有 {APP_NAME} 进程。
  enable            - 启用应用拦截功能。
  disable           - 临时禁用应用拦截功能。
"""
    )


def main():
    args = sys.argv[1:]

    if not args:
        # --- GUI 模式 ---
        # 1. 在导入 tkinter 或任何可能产生输出的模块之前，配置日志重定向
        get_app_data_path()  # 确保应用数据目录存在
        log_dir = get_log_dir_path()

        log_filename = datetime.now().strftime("%Y-%m-%d--%H-%M.log")
        log_filepath = os.path.join(log_dir, log_filename)

        log_file_obj = None
        log_q_instance = deque(maxlen=500)

        try:
            log_file_obj = open(log_filepath, "w", encoding="utf-8")
        except IOError as e:
            # 早期关键错误，直接打印到原始 stderr (控制台)
            get_original_stderr().write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] 无法打开日志文件 {log_filepath} 进行写入: {e}\n"
            )
            log_file_obj = None

        # 现在，初始化日志并完全重定向 stdout/stderr，抑制控制台输出
        # 此后所有 log_message、print() 和警告都将被捕获
        init_logging(log_q_instance, log_file_obj, suppress_console_output=True)

        # 在重定向设置完成后，记录初始消息
        if log_file_obj:
            log_message(f"日志将同时写入: {log_filepath}")
        else:
            log_message(
                "警告: 日志文件未能成功打开，日志将仅在GUI日志栏显示。", level="WARNING"
            )

        initial_config = load_config()
        if not initial_config:
            log_message("无法加载初始配置，程序退出。", level="ERROR")
            import tkinter as tk  # 确保 Tkinter 在此函数内部导入
            from tkinter import messagebox  # 确保 Tkinter 在此函数内部导入

            messagebox.showerror(
                "严重错误", "无法加载初始配置，程序将退出。请检查配置文件或权限。"
            )
            # 在退出前恢复原始流
            sys.stdout = get_original_stdout()
            sys.stderr = get_original_stderr()
            sys.exit(1)
        current_config_wrapper["config"] = initial_config

        # 2. 导入 Tkinter 并继续应用 GUI 逻辑
        import tkinter as tk
        import tkinter.ttk as ttk  # 导入 ttk
        from tkinter import messagebox, scrolledtext  # 导入 messagebox 和 scrolledtext

        root = tk.Tk()  # libpng 警告现在应该被重定向
        root.withdraw()
        root.title(f"{APP_NAME} 后台服务")
        log_message(f"{APP_NAME} 后台服务启动。配置文件: {get_config_path()}")

        def on_exit_cleanup():
            if log_file_obj:
                try:
                    log_message(f"日志文件 {log_filepath} 已关闭。", level="INFO")
                    log_file_obj.close()
                except Exception as e:
                    log_message(f"关闭日志文件时发生错误: {e}", level="ERROR")
            # 退出 GUI 应用时恢复原始 stdout/stderr
            sys.stdout = get_original_stdout()
            sys.stderr = get_original_stderr()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_exit_cleanup)

        blocker_thread = threading.Thread(
            target=start_blocking_loop,
            args=(current_config_wrapper, config_reload_event),
            daemon=True,
        )
        blocker_thread.start()
        log_message("进程拦截器线程已启动。")

        hotkey_thread = HotkeyThread(root)
        hotkey_thread.start()
        log_message("快捷键监听线程已启动。")

        root.mainloop()

        return

    # --- 命令行模式 ---
    # 对于命令行模式，sys.stdout 和 sys.stderr 不会被 init_logging 重定向
    # 因此所有 log_message 调用都将输出到原始控制台
    command = args[0].lower()

    if command == "stop":
        handle_stop()
    elif command in ["enable", "disable"]:
        handle_enable_disable(command)
    else:
        get_original_stderr().write(f"错误: 未知命令 '{command}'\n")
        print_usage()


if __name__ == "__main__":
    main()
