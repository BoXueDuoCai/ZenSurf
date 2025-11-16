# ZenSurf
软件分时限制使用管理程序。Time-Shared Restriction Usage Management Program.

---

> **中文 & Chinese**
> 
> **English below  英文在下**

# ZenSurf 使用指南

ZenSurf 是一款软件分时限制使用管理程序，可帮助您在指定时间段内限制特定应用程序的使用，提高工作和学习效率。

## 功能介绍

- 按时间段限制指定进程的运行
- 密码保护的设置界面，防止未授权修改
- 详细的操作日志记录
- 进程自动检测与管理（最小化或终止受限进程）

## 安装说明

1. 下载最新版本的 ZenSurf 代码
2. 对所有的库进行一波pip
3. 打开pack.bat进行打包（需要`pyinstall`库）

## 基本使用方法

### 启动程序

- 打开"ZenSurf.exe"（如修改`setup.spec`内的名称，将为`[name].exe`）

### 访问设置界面

通过按快捷键 Win+Ctrl+Shift+W （如修改过程序，则为改后的）可打开设置界面，会先提示要求输入密码，才能打开。

### 配置限制进程

1. 在设置界面的 "设置" 标签页中，找到 "限制进程列表" 区域
2. 每行输入一个需要限制的进程名称（例如：`chrome.exe` 表示限制谷歌浏览器）
3. 系统默认已预设了一些常见进程（chrome.exe、msedge.exe 等）
4. 完成后点击 "保存设置" 按钮

### 配置禁用时间段

1. 在设置界面的 "设置" 标签页中，找到 "禁用时间段" 区域
2. 按照 `[注释:]HH:MM-HH:MM` 格式设置时间段，例如：
   - `09:00-12:00` 表示每天 9 点到 12 点
   - `午休:12:00-13:30` 表示每天 12 点到 13 点 30 分为午休时间
3. 系统默认已预设了一些常见时间段（如课间休息、午休等）
4. 完成后点击 "保存设置" 按钮

### 启用/禁用限制功能

- 在设置界面中，勾选 "启用应用限制功能" 复选框可开启限制功能
- 取消勾选则关闭限制功能，所有进程将不受限制

> [!note]
> 可能有bug

## 密码管理

- 默认解锁密码为 `123456`
- 如需修改密码，请编辑 `blocker.py` 文件中的 `UNLOCK_PASSWORD` 变量

## 日志查看

1. 在设置界面切换到 "日志" 标签页
2. 这里将显示程序的运行日志，包括进程限制记录、密码验证记录等
3. 点击 "清空日志" 按钮可清除当前显示的日志内容

## 高级操作

### 临时解锁受限程序

当程序检测到受限进程在禁用时间段运行时：
1. 会自动最小化相关窗口并弹出密码输入框
2. 输入正确密码可临时解锁该程序
3. 若连续 3 次输入错误密码，将显示提示窗口并终止受限进程

> 其实并不会终止(小声bb 算是一个bug 懒得改了)


## 常见问题

1. **问：程序无法限制某些应用怎么办？**
   答：请确认您输入的进程名称是否正确（可在任务管理器中查看进程名称）

2. **问：忘记密码怎么办？**
   答：您可以重新安装程序或手动编辑 `blocker.py` 文件修改密码

3. **问：如何彻底关闭程序？**
   答：在任务管理器里结束进程即可。

> [!IMPORTANT]
> 1. 若想完全避免被结束进程，可通过使用ppl control以使进程不可被结束
> 2. 这是一个AI编写的程序，bug很多，敬请谅解
> 3. 为了使程序开机自启，请自行配置`任务计划程序`(win+r => taskschd.msc)
> 4. 为防止源程序被重命名以致重启后失效，请自行通过用户组权限或其他方式解决

## 许可证

本软件采用 MIT 许可证开源，详情请查看 LICENSE 文件。

---


> **英文 & English**
>
> **Chinese above  中文在上**
>
> Using AI Translation

# ZenSurf User Guide

ZenSurf is a time-segmented application usage restriction and management program that helps you limit the use of specific applications during designated time periods to enhance work and study efficiency.

## Features
- Restrict the operation of specified processes by time segments
- Password-protected settings interface to prevent unauthorized modifications
- Detailed operation log records
- Automatic process detection and management (minimize or terminate restricted processes)

## Installation Instructions
1. Download the latest version of ZenSurf source code
2. Install all required libraries via pip
3. Run `pack.bat` to package the program (requires the `pyinstaller` library)

## Basic Usage

### Launch the Program
- Open "ZenSurf.exe" (if you modified the name in `setup.spec`, the file will be named `[name].exe`)

### Access the Settings Interface
Press the shortcut key `Win+Ctrl+Shift+W` (or the modified shortcut if you changed it) to open the settings interface. You will be prompted to enter a password to access it.

### Configure Restricted Processes
1. In the settings interface, switch to the "Settings" tab and locate the "Restricted Process List" section.
2. Enter one process name per line (e.g., `chrome.exe` to restrict Google Chrome).
3. The system has preset some common processes by default (such as chrome.exe, msedge.exe, etc.).
4. Click the "Save Settings" button after completion.

### Configure Restricted Time Periods
1. In the settings interface, switch to the "Settings" tab and locate the "Restricted Time Periods" section.
2. Set time periods in the format `[Comment:]HH:MM-HH:MM`. Examples:
   - `09:00-12:00` means 9:00 AM to 12:00 PM daily
   - `Lunch Break:12:00-13:30` means 12:00 PM to 1:30 PM daily for lunch break
3. The system has preset some common time periods by default (such as class breaks, lunch breaks, etc.).
4. Click the "Save Settings" button after completion.

### Enable/Disable Restriction Function
- Check the "Enable Application Restriction" checkbox in the settings interface to activate the restriction function.
- Uncheck it to disable the restriction function, allowing all processes to run without limitations.

> [!note]
> There may be bugs.

## Password Management
- The default unlock password is `123456`.
- To modify the password, edit the `UNLOCK_PASSWORD` variable in the `blocker.py` file.

## View Logs
1. Switch to the "Logs" tab in the settings interface.
2. This section displays the program's operation logs, including process restriction records, password verification records, etc.
3. Click the "Clear Logs" button to delete the currently displayed log content.

## Advanced Operations

### Temporarily Unlock Restricted Programs
When the program detects a restricted process running during a restricted time period:
1. It will automatically minimize the relevant window and pop up a password input box.
2. Enter the correct password to temporarily unlock the program.
3. If the password is entered incorrectly 3 consecutive times, a prompt window will appear and the restricted process will be terminated.

> Actually, it won't terminate (whispers—it's a bug, too lazy to fix)

## Frequently Asked Questions (FAQs)
1. **Q: What if the program fails to restrict certain applications?**
   A: Please confirm that the process name you entered is correct (you can check the process name in Task Manager).

2. **Q: What if I forget the password?**
   A: You can reinstall the program or manually edit the `blocker.py` file to modify the password.

3. **Q: How to completely close the program?**
   A: End the process in Task Manager.

> [!IMPORTANT]
> 1. To completely prevent the process from being terminated, you can use PPL Control (Protected Process Light) to make the process unterminable.
> 2. This is an AI-written program with many bugs—your understanding is appreciated.
> 3. To set the program to run on startup, configure it through Task Scheduler manually (press Win+R, then enter `taskschd.msc`).
> 4. To prevent the original program from being renamed and thus failing after restart, please resolve it through user group permissions or other methods manually.

## License
This software is open-source under the MIT License. For details, please refer to the LICENSE file.
