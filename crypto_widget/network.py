"""基于 Qt 事件循环的可取消请求，无工作线程及阻塞式网络操作。"""

from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtGui import QImage
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from .config import ICON_CACHE_DIR, SOURCE_LABELS, normalize_symbol
from .providers import SOURCE_NAMES, SOURCE_ORDER, parse_price, parse_provider_price, price_url, split_symbol


@dataclass
class PriceJob:
    remaining: list[str]
    errors: list[str] = field(default_factory=list)


class MarketClient(QObject):
    price_ready = pyqtSignal(str, object, str, str)
    icon_ready = pyqtSignal(str, QImage)
    icons_finished = pyqtSignal(int, int)

    def __init__(self, cache_dir=ICON_CACHE_DIR, parent=None, manager=None, source="auto"):
        super().__init__(parent)
        self.cache_dir = Path(cache_dir)
        self.manager = manager if manager is not None else QNetworkAccessManager(self)
        self.pending = {}
        self.generations = {"price": 0, "icon": 0}
        self.closed = False
        self.icon_counts = [0, 0]
        self.loading_icons = False
        self.price_jobs = {}
        self.source = "auto"
        self.set_source(source)

    def _request(self, kind, symbol, url, provider=None):
        key = (kind, symbol)
        if self.closed or key in self.pending:
            return
        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(3000 if kind == "price" else 8000)
        request.setRawHeader(b"User-Agent", b"CryptoWidget/2.0")
        reply = self.manager.get(request)
        self.pending[key] = reply
        generation = self.generations[kind]
        reply.finished.connect(lambda: self._finished(key, reply, generation, provider))

    def set_source(self, source):
        if source not in SOURCE_LABELS:
            raise ValueError("不支持的行情数据源")
        if source != self.source:
            self.cancel("price")
            self.source = source

    def refresh_prices(self, symbols):
        if self.closed:
            return
        for symbol in dict.fromkeys(symbols):
            symbol = normalize_symbol(symbol)
            if symbol in self.price_jobs:
                continue
            self.price_jobs[symbol] = PriceJob(list(SOURCE_ORDER) if self.source == "auto" else [self.source])
            self._next_price_source(symbol)

    def _next_price_source(self, symbol):
        job = self.price_jobs.get(symbol)
        if self.closed or job is None:
            return
        while job.remaining:
            provider = job.remaining.pop(0)
            try:
                url = price_url(provider, symbol)
            except ValueError as exc:
                job.errors.append(f"{SOURCE_NAMES[provider]}：{exc}")
                continue
            self._request("price", symbol, url, provider)
            return
        self.price_jobs.pop(symbol)
        self.price_ready.emit(symbol, None, "；".join(job.errors), "")

    def cancel(self, kind):
        self.generations[kind] += 1
        if kind == "price":
            self.price_jobs.clear()
        for key, reply in list(self.pending.items()):
            if key[0] == kind:
                self.pending.pop(key)
                reply.abort()
                reply.deleteLater()

    def reload_icons(self, symbols, clear=False):
        self.cancel("icon")
        if self.closed:
            return
        self.icon_counts = [0, 0]
        if clear and self.cache_dir.exists():
            # 仅删除本应用命名的 PNG，不递归、不跟随目录。
            for path in self.cache_dir.glob("*.png"):
                if path.is_file() and path.stem.isalnum():
                    path.unlink()
        self.loading_icons = True
        for symbol in dict.fromkeys(symbols):
            base, _ = split_symbol(normalize_symbol(symbol))
            path = self.cache_dir / f"{base}.png"
            image = QImage(str(path)) if path.is_file() else QImage()
            if not image.isNull():
                self.icon_ready.emit(symbol, image)
                self.icon_counts[0] += 1
            else:
                self._request("icon", symbol, f"https://bin.bnbstatic.com/static/assets/logos/{base}.png")
        self.loading_icons = False
        self._icons_completed()

    def _icons_completed(self):
        if not self.loading_icons and not any(key[0] == "icon" for key in self.pending):
            self.icons_finished.emit(*self.icon_counts)

    def _finished(self, key, reply, generation, provider=None):
        kind, symbol = key
        try:
            if self.closed or generation != self.generations[kind] or self.pending.get(key) is not reply:
                return
            self.pending.pop(key)
            ok = reply.error() == QNetworkReply.NetworkError.NoError
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            ok = ok and status == 200
            data = bytes(reply.readAll())
            if kind == "price":
                try:
                    if not ok:
                        raise ValueError("交易对无效" if status == 400 else "网络请求失败")
                    price = parse_provider_price(provider, symbol, data)
                except ValueError as exc:
                    self.price_jobs[symbol].errors.append(f"{SOURCE_NAMES[provider]}：{exc}")
                    self._next_price_source(symbol)
                else:
                    self.price_jobs.pop(symbol)
                    self.price_ready.emit(symbol, price, "", provider)
            else:
                image = QImage.fromData(data) if ok and len(data) <= 5_000_000 else QImage()
                valid = not image.isNull() and image.width() <= 2048 and image.height() <= 2048
                self.icon_counts[0 if valid else 1] += 1
                if valid:
                    try:
                        self.cache_dir.mkdir(parents=True, exist_ok=True)
                        base, _ = split_symbol(symbol)
                        image.save(str(self.cache_dir / f"{base}.png"), "PNG")
                    except OSError:
                        pass  # 缓存不可写时仍显示已下载图标。
                    self.icon_ready.emit(symbol, image)
                self._icons_completed()
        finally:
            reply.deleteLater()

    def close(self):
        self.closed = True
        self.cancel("price")
        self.cancel("icon")
