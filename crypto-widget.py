"""兼容原有启动方式：uv run crypto-widget.py。"""

from crypto_widget.app import main


if __name__ == "__main__":
    raise SystemExit(main())
