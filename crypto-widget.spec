# 使用 uv run --group build pyinstaller --clean --noconfirm crypto-widget.spec
from pathlib import Path
import os
import sys

from PyQt6.QtCore import QLibraryInfo

root = Path(SPECPATH)
# 隔离构建机的第三方 DLL 搜索路径，仅保留 Python、Qt 与 Windows。
# Qt 在 Windows 使用系统 TLS 后端，不依赖 PATH 中偶然存在的 OpenSSL。
windows = Path(os.environ["SystemRoot"])
os.environ["PATH"] = os.pathsep.join([
    str(Path(sys.executable).parent), sys.base_prefix,
    QLibraryInfo.path(QLibraryInfo.LibraryPath.BinariesPath),
    str(windows / "System32"), str(windows),
])
a = Analysis(
    [str(root / "crypto-widget.py")],
    pathex=[str(root)], binaries=[],
    datas=[(str(root / "cw.ico"), "."), (str(root / "crypto_widget" / "assets"), "crypto_widget/assets")],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
# Windows 10/11 自带 UCRT。避免从构建机 PATH 中混入第三方旧版
# ucrtbase.dll，否则 Qt 可能因缺失系统导出函数而无法启动。
a.binaries = [entry for entry in a.binaries
              if Path(entry[0]).name.lower() != "ucrtbase.dll"
              and not Path(entry[0]).name.lower().startswith("api-ms-win-")]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="crypto-widget", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False, icon=str(root / "cw.ico"),
    manifest=str(root / "crypto-widget.manifest"),
)
