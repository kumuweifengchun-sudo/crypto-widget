# 桌面行情组件

一个适用于 Windows 10/11 的中文加密货币行情悬浮窗，使用 Python 3.13 和 PyQt6。依赖安装、开发、测试与打包统一使用 **uv**。

## 界面预览

![深色行情悬浮窗](docs/screenshots/widget.png)

![中文设置页](docs/screenshots/settings.png)

[完整模式](docs/screenshots/widget-full.png) · [网络失败状态](docs/screenshots/widget-error.png)

## 功能

- 三个自定义现货交易对，分别设置 0～8 位小数。
- Binance、OKX、Bybit 三个公开行情源，支持自动故障切换和固定数据源。
- 深色半透明悬浮窗，支持拖动、置顶、自动保存位置和流畅轮播。
- 默认启用迷你模式：28 像素高，仅显示图标和价格；支持切换回完整模式。
- 全局快捷键默认 `Alt+Z`，一键隐藏／恢复显示，可在设置中修改。
- 可选开机自启动，登录 Windows 后自动运行，支持源码和打包后的 EXE。
- 小尺寸浅色中文设置页（默认 360×410，正文 11 像素），数值直接输入，外观预览按需展开。
- 后台异步获取行情，同一交易对的在途请求自动去重。
- 网络失败保留最近成功价格并明确提示，下一轮刷新成功后自动恢复。
- 图标本地缓存，下载失败使用首字母图标。
- 兼容旧版配置；损坏文件备份、参数校验、原子保存。
- 中文 Qt 菜单与提示，支持高分屏和可滚动设置页。
- 价格使用 Segoe UI 半粗字体及等宽数字列，中文使用微软雅黑；支持分数 DPI 与逐显示器 DPI 切换。

本项目显示交易所公开现货接口的报价，不需要 API Key，不提供交易、合约报价、走势图或系统托盘功能。

## 安装与运行

先安装 uv（参见 [uv 安装说明](https://docs.astral.sh/uv/getting-started/installation/)）。在项目目录打开 PowerShell：

```powershell
uv sync --locked
uv run --locked crypto-widget.py
```

uv 会根据 `.python-version` 选择 Python 3.13，并在项目的 `.venv` 内安装锁定依赖，无需手动激活虚拟环境。

直接打开设置页：

```powershell
uv run --locked crypto-widget.py --settings
```

使用已构建的程序时，直接运行 `dist/crypto-widget.exe`，无需另外安装 Python 或 uv。

## 使用说明

- **单击悬浮窗**：立即刷新行情；请求进行中不会重复发送。
- **拖动悬浮窗**：按住鼠标左键约 0.35 秒，光标变为抓手后移动；释放后保存位置，拖动不会触发刷新。
- **右键菜单**：迷你模式、行情数据源、设置、退出；菜单及子菜单统一使用紧凑的 11 像素字号。
- **行情数据源**：默认“自动（三源）”，也可以在右键菜单或设置页固定选择 Binance、OKX、Bybit。选择会保存，下次启动继续使用。
- **隐藏／显示**：在任何应用中按 `Alt+Z` 隐藏悬浮窗，再按一次恢复；打开的设置页也会一并隐藏，未保存内容保留。隐藏期间行情继续刷新。可在设置中输入其他组合，例如 `Ctrl+Shift+H`；保存后生效，快捷键被占用时会提示并保留原组合。快捷键需包含 Ctrl、Alt 或 Win，搭配字母、数字或 F1～F24，可另加 Shift。
- **迷你模式**：默认启用，仅显示图标与价格，固定 12 像素字号，宽度随价格内容适配。右键菜单或设置页可关闭，恢复原来的完整布局与字号。鼠标悬停可查看完整交易对和更新时间；更新失败时价格变为黄色并显示感叹号，详细状态显示在悬停提示中。尺寸以逻辑像素计，会随 Windows 显示缩放变化。
- **交易对**：统一填写 `BTCUSDT`、`ETHUSDT`、`SOLUSDT` 等代码，输入自动去除首尾空格并转大写；OKX 会自动转换为 `BTC-USDT` 等格式。代码格式合法不代表各交易所都支持该交易对，不支持时自动模式会继续尝试下一源。
- **数值设置**：字号、背景不透明度、刷新间隔、轮播间隔和小数位均使用数值输入框，支持直接键入，单位显示在框内。迷你模式字号固定为 12 像素，关闭迷你模式后可编辑完整模式字号。
- **外观预览**：默认折叠，勾选“预览”后显示固定示例行情，根据可用空间缩放。保存才会应用到桌面，取消不会更改原配置。
- **重新加载图标**：立即清除图标缓存并重新获取当前已保存的币种图标；此操作独立于设置保存和取消。
- **关闭轮播**：固定显示第一个交易对。
- **开机自启动**：在设置页的“常规设置”中勾选并保存，当前用户下次登录 Windows 后自动启动；取消勾选并保存即可关闭，默认关闭，无需管理员权限。开关读取当前用户注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 中的 `CryptoWidget` 启动项，不写入 JSON 配置。源码模式使用当前环境的 `pythonw.exe`，请保留项目与 `.venv`；EXE 模式请保留程序位置。移动程序后重新打开并勾选保存，以更新启动路径。自启动沿用当前配置文件和图标缓存的绝对路径，不会自动打开设置页。每个 Windows 用户共用一个启动项，多份程序以最后保存启用的路径为准。如果在 Windows 任务管理器中禁用了此启动项，需在那里重新启用。
- **报价单位**：显示交易对的计价币种，例如 USDT、USDC 或 BTC，不将其统一当作美元。

| 参数 | 范围 | 默认值 |
| --- | --- | --- |
| 小数位 | 0～8 | 2 |
| 字号 | 8～64 像素 | 24 像素 |
| 背景不透明度 | 0～100% | 70% |
| 行情刷新间隔 | 5～300 秒 | 10 秒 |
| 币种轮播间隔 | 3～60 秒 | 3 秒 |

## 配置与缓存

继续使用旧版路径：

- 配置：`%USERPROFILE%\crypto_widget_settings.json`
- 图标：`%USERPROFILE%\crypto_widget_icons`

原有 `symbol1`～`symbol3`、小数位、透明度、间隔与位置等字段保持兼容。无效类型恢复默认值，超出范围的参数限制到支持范围。损坏配置在同目录保留带时间戳的 `.bak` 文件，并显示中文提示；保存失败不会应用设置或关闭设置页。

独立测试或多份配置可指定路径：

```powershell
uv run --locked crypto-widget.py --config .\local-settings.json --cache-dir .\local-icons
```

首次请求期间显示“加载中”；网络异常且尚无成功价格时显示“暂无数据”。已有价格时保留原值并标记“更新失败 · 保留上次价格”，因此此时显示的不是最新报价。行情单源请求设有 3 秒网络传输超时，图标请求为 8 秒；图标失败不影响行情。

## 三源现货行情

| 数据源 | 公开接口 | 请求方式 |
| --- | --- | --- |
| Binance | `https://api.binance.com/api/v3/ticker/price` | `symbol=BTCUSDT` |
| OKX | `https://www.okx.com/api/v5/market/ticker` | `instId=BTC-USDT` |
| Bybit | `https://api.bybit.com/v5/market/tickers` | `category=spot&symbol=BTCUSDT` |

自动模式对每个交易对分别按 **Binance → OKX → Bybit** 顺序请求，首个有效报价即结束本轮。超时、网络或交易所业务错误、空数据、交易对不匹配都会触发下一源；所有源失败才显示错误。下一轮仍从 Binance 开始，以便主源恢复后自动回切。在途请求整条重试链去重，避免刷新周期重叠。固定源模式仅访问所选交易所。

三个源均使用**现货**，Bybit 使用 `spot`，不混用 `linear` 合约行情。OKX 响应也会检查 `SPOT` 类型及交易对代码；不能识别计价币种时跳过 OKX，不猜测交易对。各交易所价格本身可能有差异，组件不取均价、不同时显示三份报价。

鼠标悬停可查看当前选择模式、**最近一次成功报价的真实来源**以及失败原因。切换源后请求尚未成功或三源均失败时，保留的旧价格仍标注其原来源。迷你窗口仍只显示图标与价格。

网络连接、服务地区限制或交易所未上架该交易对可能影响访问。图标继续使用原有缓存与下载渠道，图标来源与行情选择独立。

## 开发与测试

```powershell
uv sync --locked --group dev
uv run --locked --group dev pytest -q
```

自动化测试使用临时配置目录与模拟请求，不读写真实用户配置，也不依赖公网。

生成 Windows 下实际 100%、125%、150%、175%、200% 缩放的截图与检查报告：

```powershell
uv run --locked --group dev python tools/verify_ui.py --all
```

输出位于 `artifacts/screenshots/`，包括设置页顶部、底部、大字号预览、正常行情及失败状态。脚本会抵消本机系统缩放的叠加，并检查实际设备像素比、字体与数字列宽。截图中的行情为示例数据。

字体直接通过 QPainter 绘制，开启文字抗锯齿，价格基线与数字位置对齐到设备像素，不缓存价格文字位图。Qt 6 使用 PassThrough 缩放策略，保留 125% 等比例，不再额外按 DPI 乘一次字号；迷你模式仍为 12 像素、28 像素高，设置页仍为 11 像素正文。

默认背景保持 70% 不透明度，价格使用柔和近白色；已有透明度设置继续生效。完全透明时的文字对比度取决于桌面背景。使用 Windows 自带字体，无需额外下载字体文件。

单独检查真实网络连通性：

```powershell
uv run --locked python tools/check_network.py
uv run --locked python tools/check_network.py --source auto
```

第一条命令分别检查三个交易所的 BTC、ETH、SOL 现货行情，第二条验证自动模式。检查只读取公开行情接口，将图标写入临时目录，不使用现有用户缓存。

## Windows 打包

```powershell
uv sync --locked --group build
uv run --locked --group build pyinstaller --clean --noconfirm crypto-widget.spec
```

生成单文件、无控制台的 `dist/crypto-widget.exe`。打包配置包含应用图标、界面 SVG 和 Qt 中文翻译资源。首次启动需要解压 Qt 运行库，可能比源码启动稍慢。

`crypto-widget.manifest` 随 EXE 内嵌，声明 PerMonitorV2 DPI 感知，避免 Windows 将程序按普通位图缩放。

构建过程会隔离第三方 DLL 搜索路径，并使用 Windows 自带的 UCRT，防止构建机上其他软件的旧版 DLL 混入产物。

构建后验证源码和 EXE 的悬浮窗、设置页启动与请求进行中退出：

```powershell
uv run --locked python tools/smoke_test.py
```

## 项目结构

```text
crypto-widget.py       兼容启动入口
crypto_widget/         配置、异步网络、中文界面与绘制模块
crypto_widget/assets/  控件矢量图标
crypto-widget.spec     Windows 单文件构建配置
crypto-widget.manifest Windows 高 DPI 声明
pyproject.toml         uv 项目及依赖分组
uv.lock                精确依赖锁文件
.python-version        Python 版本
tests/                自动化测试
tools/                界面截图、联网检查与启动验证
docs/                 当前界面截图
```

调整依赖时使用 `uv add`，测试依赖使用 `uv add --group dev`，构建依赖使用 `uv add --group build`；一并维护 `pyproject.toml` 和 `uv.lock`。

## 许可

本项目沿用 [MIT 许可证](LICENSE)。
