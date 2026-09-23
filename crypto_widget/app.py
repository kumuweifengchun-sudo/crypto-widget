"""应用入口。"""

import argparse
from pathlib import Path
import sys

from PyQt6.QtCore import QLibraryInfo, QLocale, QTimer, QTranslator, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from .config import ICON_CACHE_DIR, SETTINGS_FILE, SettingsStore
from .network import MarketClient
from .hotkey import GlobalHotkey
from .startup import StartupManager
from .visuals import font, resource_path
from .widget import CryptoWidget


def create_application(argv):
    # Qt 6 已启用高 DPI；保留 125%/150% 等真实比例，字号不再手动乘 DPI。
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(argv)
    app.setApplicationName("桌面行情")
    app.setOrganizationName("CryptoWidget")
    app.setStyle("Fusion")
    app.setFont(font(13))
    app.setWindowIcon(QIcon(str(resource_path("cw.ico"))))
    QLocale.setDefault(QLocale("zh_CN"))
    translator = QTranslator(app)
    if translator.load("qtbase_zh_CN", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(translator)
    app.translator = translator
    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description="中文桌面加密货币行情组件", add_help=False)
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息")
    parser.add_argument("--settings", action="store_true", help="启动后打开设置")
    parser.add_argument("--config", type=Path, default=SETTINGS_FILE, help="配置文件路径")
    parser.add_argument("--cache-dir", type=Path, default=ICON_CACHE_DIR, help="图标缓存目录")
    parser.add_argument("--quit-after", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    app = create_application([sys.argv[0]])
    store = SettingsStore(args.config)
    config = store.load()
    client = MarketClient(args.cache_dir, parent=app)
    widget = CryptoWidget(config, store, client, startup=StartupManager(args.config, args.cache_dir))
    startup_warning = store.warning
    try:
        widget.hotkey = GlobalHotkey(widget.toggle_visibility)
        widget.hotkey.change(config["hide_hotkey"])
    except ValueError as exc:
        startup_warning = "\n".join(part for part in (startup_warning, str(exc)) if part)
    widget.show()
    if args.settings:
        QTimer.singleShot(0, widget.open_settings)
    if startup_warning:
        def show_warning():
            message = QMessageBox(widget)
            message.setWindowTitle("启动提示")
            message.setIcon(QMessageBox.Icon.Warning)
            message.setText(startup_warning)
            message.addButton("知道了", QMessageBox.ButtonRole.AcceptRole)
            message.exec()
        QTimer.singleShot(100, show_warning)
    if args.quit_after > 0:
        QTimer.singleShot(args.quit_after, app.quit)
    return app.exec()
