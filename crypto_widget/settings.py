"""中文设置对话框；草稿与生效配置分离。"""

from decimal import Decimal

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QAbstractSpinBox, QCheckBox, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QSpinBox, QVBoxLayout, QWidget,
)

from .config import SOURCE_LABELS, normalize_hotkey, normalize_symbol
from .visuals import Quote, draw_ticker, font, render_hints, resource_path, ticker_size


class Preview(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setMinimumHeight(76)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        quote = Quote(self.config["symbol1"] or "BTCUSDT", Decimal("68432.18"))
        precision = self.config["decimals1"]
        mini = self.config.get("mini_mode", True)
        width, height = ticker_size([quote], [precision], self.config["text_size"], mini=mini, device=self)
        painter = QPainter(self)
        render_hints(painter)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#dbe3ef"))
        painter.drawRoundedRect(QRectF(self.rect()), 12, 12)
        if mini:
            painter.setFont(font(10))
            painter.setPen(QColor("#52627a"))
            painter.drawText(QRectF(10, 4, self.width() - 20, 16), Qt.AlignmentFlag.AlignLeft, "示例行情 · 迷你预览")
        scale = min((self.width() - 24) / width, (self.height() - 16) / height, 1)
        painter.translate((self.width() - width * scale) / 2, (self.height() - height * scale) / 2)
        painter.scale(scale, scale)
        draw_ticker(painter, QRectF(0, 0, width, height), quote, precision,
                    self.config["text_size"], self.config["bg_opacity"], sample=True, mini=mini)
        painter.end()


class SettingsDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.draft = owner.config.copy()
        self.symbol_edits = []
        self.decimal_spins = []
        self.number_inputs = {}
        self._full_text_size = self.draft["text_size"]
        self.setWindowTitle("行情组件 · 设置")
        self.setModal(True)
        self.setMinimumSize(320, 320)
        self._build_ui()
        self._load_startup()
        self._apply_style()
        self._refresh_preview()
        self.owner.client.icons_finished.connect(self._icons_finished)
        area = self.screen().availableGeometry()
        self.resize(min(360, area.width() - 32), min(410, area.height() - 64))

    def _card(self, layout, title, toggle=None, extra_toggle=None):
        frame = QFrame()
        frame.setObjectName("card")
        body = QVBoxLayout(frame)
        body.setContentsMargins(10, 6, 10, 6)
        body.setSpacing(4)
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        heading = QHBoxLayout()
        heading.addWidget(label)
        heading.addStretch()
        if extra_toggle is not None:
            heading.addWidget(extra_toggle)
        if toggle is not None:
            heading.addWidget(toggle)
        body.addLayout(heading)
        layout.addWidget(frame)
        return body

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("content")
        body = QVBoxLayout(content)
        body.setContentsMargins(10, 8, 10, 6)
        body.setSpacing(5)
        self.scroll.setWidget(content)
        root.addWidget(self.scroll, 1)

        self.source_combo = QComboBox()
        for source, label in SOURCE_LABELS.items():
            self.source_combo.addItem(label, source)
        self.source_combo.setCurrentIndex(self.source_combo.findData(self.draft.get("price_source", "auto")))
        self.source_combo.setAccessibleName("行情数据源")
        self.source_combo.setToolTip("均为现货报价；自动模式按 Binance、OKX、Bybit 顺序尝试")
        coins = self._card(body, "币种与数据源", toggle=self.source_combo)
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(3)
        for column, text in enumerate(("序号", "交易对", "小数位")):
            label = QLabel(text)
            label.setObjectName("muted")
            grid.addWidget(label, 0, column)
        grid.setColumnStretch(1, 1)
        for i in range(1, 4):
            index = QLabel(f"0{i}")
            index.setObjectName("index")
            edit = QLineEdit(self.draft[f"symbol{i}"])
            edit.setPlaceholderText("例如 BTCUSDT")
            edit.setToolTip("统一填写 BTCUSDT 等现货交易对，系统会自动转换各交易所代码")
            edit.setMaxLength(30)
            edit.setAccessibleName(f"交易对 {i}")
            edit.editingFinished.connect(lambda edit=edit: edit.setText(edit.text().strip().upper()))
            edit.textChanged.connect(self._refresh_preview)
            spin = QSpinBox()
            spin.setRange(0, 8)
            spin.setValue(self.draft[f"decimals{i}"])
            spin.setFixedWidth(56)
            spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin.setAccessibleName(f"交易对 {i} 小数位")
            spin.valueChanged.connect(self._refresh_preview)
            self.symbol_edits.append(edit)
            self.decimal_spins.append(spin)
            grid.addWidget(index, i, 0)
            grid.addWidget(edit, i, 1)
            grid.addWidget(spin, i, 2)
        coins.addLayout(grid)

        self.mini_check = QCheckBox("迷你模式")
        self.mini_check.setChecked(self.draft.get("mini_mode", True))
        self.mini_check.setToolTip("仅显示图标与价格，固定 12 像素字号；关闭后可调节完整模式字号")
        self.preview_check = QCheckBox("预览")
        appearance = self._card(body, "外观设置", toggle=self.mini_check, extra_toggle=self.preview_check)
        self.preview = Preview(self.draft)
        appearance.addWidget(self.preview)
        self.preview.hide()
        self.preview_check.toggled.connect(self.preview.setVisible)
        self.preview.setToolTip("示例行情；预览按可用空间缩放，保存后应用到桌面")
        self._number_input(appearance, "text_size", "字号", 8, 64, "像素", self.draft["text_size"])
        self._number_input(appearance, "bg_opacity", "背景不透明度", 0, 100, "%", round(self.draft["bg_opacity"] * 100))
        self.mini_check.toggled.connect(self._toggle_mini)
        self._toggle_mini(self.mini_check.isChecked())

        self.cycle_check = QCheckBox("自动轮播币种")
        self.cycle_check.setChecked(self.draft["cycle_enabled"])
        self.startup_check = QCheckBox("开机自启动")
        self.startup_check.setToolTip("登录 Windows 后自动启动；保存设置后生效，仅对当前用户有效")
        behavior = self._card(body, "常规设置", toggle=self.cycle_check, extra_toggle=self.startup_check)
        self._number_input(behavior, "update_interval", "行情刷新间隔", 5, 300, "秒", self.draft["update_interval"])
        self._number_input(behavior, "cycle_interval", "币种轮播间隔", 3, 60, "秒", self.draft["cycle_interval"])
        self.cycle_check.toggled.connect(self._toggle_cycle)
        self._toggle_cycle(self.cycle_check.isChecked())
        shortcut_row = QHBoxLayout()
        shortcut_row.addWidget(QLabel("隐藏／显示快捷键"))
        shortcut_row.addStretch()
        self.hotkey_edit = QLineEdit(self.draft.get("hide_hotkey", "Alt+Z"))
        self.hotkey_edit.setFixedWidth(110)
        self.hotkey_edit.setAccessibleName("隐藏／显示快捷键")
        self.hotkey_edit.setToolTip("全局生效；例如 Alt+Z、Ctrl+Shift+H，保存后应用")
        shortcut_row.addWidget(self.hotkey_edit)
        behavior.addLayout(shortcut_row)
        body.addStretch()

        footer = QWidget()
        footer.setObjectName("footer")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(10, 6, 10, 8)
        self.feedback = QLabel("")
        self.feedback.setObjectName("feedback")
        self.feedback.setWordWrap(True)
        self.feedback.hide()
        footer_layout.addWidget(self.feedback)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.refresh_button = QPushButton("重新加载图标")
        self.refresh_button.setObjectName("quiet")
        self.refresh_button.setToolTip("立即清理已保存币种的图标缓存并重新下载")
        self.refresh_button.clicked.connect(self._refresh_icons)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        save = QPushButton("保存设置")
        save.setObjectName("primary")
        save.setDefault(True)
        save.clicked.connect(self._save)
        for button in (self.refresh_button, cancel, save):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setAutoDefault(False)
        cancel.setAutoDefault(False)
        buttons.addWidget(self.refresh_button)
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        footer_layout.addLayout(buttons)
        root.addWidget(footer)

    def _load_startup(self):
        manager = self.owner.startup
        if manager is None or not manager.supported:
            self.startup_check.setEnabled(False)
            self.startup_check.setToolTip("当前运行环境不支持开机自启动")
            return
        try:
            self.startup_check.setChecked(manager.read() is not None)
        except OSError as exc:
            self.startup_check.setEnabled(False)
            self._message(str(exc))

    def _number_input(self, layout, key, title, low, high, unit, initial):
        row = QHBoxLayout()
        label = QLabel(title)
        number = QSpinBox()
        number.setAccessibleName(title)
        number.setRange(low, high)
        number.setSuffix(f" {unit}")
        number.setFixedWidth(90)
        number.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        number.setKeyboardTracking(False)
        number.setValue(initial)
        label.setBuddy(number)
        self.number_inputs[key] = number
        number.valueChanged.connect(self._refresh_preview)
        row.addWidget(label)
        row.addStretch()
        row.addWidget(number)
        layout.addLayout(row)

    def _toggle_mini(self, enabled):
        number = self.number_inputs["text_size"]
        number.interpretText()
        if enabled and number.isEnabled():
            self._full_text_size = number.value()
        number.setEnabled(not enabled)
        number.setValue(12 if enabled else self._full_text_size)
        number.setToolTip("迷你模式使用固定 12 像素字号" if enabled else "完整模式的文字大小")
        self._refresh_preview()

    def _toggle_cycle(self, enabled):
        self.number_inputs["cycle_interval"].setEnabled(enabled)

    def _refresh_preview(self, *_):
        if not hasattr(self, "preview"):
            return
        draft = self.draft.copy()
        draft["mini_mode"] = self.mini_check.isChecked()
        for i, (edit, spin) in enumerate(zip(self.symbol_edits, self.decimal_spins), 1):
            draft[f"symbol{i}"] = edit.text().strip().upper()
            draft[f"decimals{i}"] = spin.value()
        for key, number in self.number_inputs.items():
            draft[key] = number.value() / 100 if key == "bg_opacity" else number.value()
        if draft["mini_mode"]:
            draft["text_size"] = self._full_text_size
        self.preview.config = draft
        self.preview.update()

    def _message(self, text):
        self.feedback.setText(text)
        self.feedback.show()

    def _save(self):
        candidate = self.owner.config.copy()  # 保留对话框打开期间的最新位置。
        for i, (edit, spin) in enumerate(zip(self.symbol_edits, self.decimal_spins), 1):
            try:
                candidate[f"symbol{i}"] = normalize_symbol(edit.text())
            except ValueError as exc:
                self._message(f"第 {i} 个交易对：{exc}")
                edit.setFocus()
                return
            spin.interpretText()
            candidate[f"decimals{i}"] = spin.value()
        for key, number in self.number_inputs.items():
            number.interpretText()
            candidate[key] = number.value() / 100 if key == "bg_opacity" else number.value()
        if self.mini_check.isChecked():
            candidate["text_size"] = self._full_text_size
        candidate["cycle_enabled"] = self.cycle_check.isChecked()
        candidate["mini_mode"] = self.mini_check.isChecked()
        candidate["price_source"] = self.source_combo.currentData()
        try:
            candidate["hide_hotkey"] = normalize_hotkey(self.hotkey_edit.text())
            startup_enabled = self.startup_check.isChecked() if self.startup_check.isEnabled() else None
            self.owner.save_configuration(candidate, startup_enabled=startup_enabled)
        except ValueError as exc:
            self._message(str(exc))
            self.hotkey_edit.setFocus()
            return
        except OSError as exc:
            self._message(f"保存失败，请检查权限后重试。{exc}")
            return
        self.owner.apply_settings(candidate)
        self.accept()

    def _refresh_icons(self):
        self.refresh_button.setEnabled(False)
        self._message("正在重新加载已保存币种的图标…")
        try:
            self.owner.reload_icons(clear=True)
        except OSError as exc:
            self.refresh_button.setEnabled(True)
            self._message(f"无法清理图标缓存：{exc}")

    def _icons_finished(self, success, failure):
        if self.refresh_button.isEnabled():
            return
        self.refresh_button.setEnabled(True)
        self._message(f"图标加载完成：{success} 个成功，{failure} 个使用默认图标。")

    def _apply_style(self):
        assets = resource_path("crypto_widget/assets").as_posix()
        self.setStyleSheet("""
            QDialog, QWidget#content { background: #f3f6fb; }
            QWidget { color: #24324a; font-size: 11px; }
            QLabel { background: transparent; }
            QLabel#sectionTitle { font-size: 12px; font-weight: 600; color: #17243b; }
            QLabel#muted { color: #69788f; font-size: 10px; }
            QLabel#index { color: #8795a8; font-weight: 600; }
            QFrame#card { background: white; border: 1px solid #e4eaf3; border-radius: 10px; }
            QWidget#footer { background: #f3f6fb; border-top: 1px solid #e2e8f1; }
            QLabel#feedback { color: #9b6319; font-size: 11px; }
            QLineEdit, QSpinBox, QComboBox { background: #f9fbfe; border: 1px solid #d9e1ed;
                border-radius: 4px; padding: 3px 6px; min-height: 16px; selection-background-color: #dbe7ff;
                selection-color: #1e3a8a; }
            QLineEdit:hover, QSpinBox:hover, QComboBox:hover { border-color: #a8b9d3; }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #4779ed; background: white; }
            QComboBox { min-width: 90px; padding-right: 18px; }
            QComboBox QAbstractItemView { background: white; color: #24324a; selection-background-color: #dbe7ff; }
            QSpinBox:disabled { color: #8a97aa; background: #edf1f7; }
            QCheckBox { spacing: 5px; min-height: 18px; background: transparent; }
            QCheckBox::indicator { width: 13px; height: 13px; border: 1px solid #c7d3e3;
                border-radius: 3px; background: #f9fbfe; }
            QCheckBox::indicator:hover { border-color: #4779ed; }
            QCheckBox::indicator:checked { background: #4779ed; border-color: #4779ed; image: url(ASSETS/check.svg); }
            QPushButton { min-height: 18px; padding: 3px 9px; border-radius: 5px;
                background: white; border: 1px solid #d9e1ed; font-weight: 500; }
            QPushButton:hover { background: #edf3ff; border-color: #a9bfe9; }
            QPushButton:pressed { background: #dbe7fd; }
            QPushButton:focus { border: 1px solid #4779ed; }
            QPushButton#primary { background: #3569df; border-color: #3569df; color: white; }
            QPushButton#primary:hover { background: #2859c5; }
            QPushButton#primary:pressed { background: #204aa6; }
            QPushButton#quiet { background: transparent; border-color: transparent; color: #526b91; padding-left: 0; }
            QPushButton#quiet:hover { color: #2859c5; }
            QPushButton:disabled { color: #99a6b8; background: #eef2f7; }
            QScrollArea { background: transparent; }
            QScrollBar:vertical { width: 8px; background: transparent; margin: 4px 0; }
            QScrollBar::handle:vertical { background: #cbd5e1; border-radius: 4px; min-height: 36px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        """.replace("ASSETS", assets))
