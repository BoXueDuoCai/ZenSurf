# setup.spec
import sys
import os
from PyInstaller.building.api import EXE, PYZ  # 新增导入 PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['src/main.py'],  # 入口文件路径
    pathex=[os.path.abspath('.')],  # 项目根目录
    binaries=[],
    datas=[('WebRestrictSetting.json', '.')],  # 包含配置文件
    hiddenimports=collect_submodules('psutil'),  # 确保psutil正常导入
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 显式创建 PYZ 对象（关键修正）
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ZenSurf',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',
)