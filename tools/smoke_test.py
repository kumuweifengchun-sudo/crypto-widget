"""从独立工作目录启动源码与 EXE，验证资源路径和有请求时退出。"""

from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def main():
    commands = [
        ("源码悬浮窗", [sys.executable, str(ROOT / "crypto-widget.py")], []),
        ("源码设置页", [sys.executable, str(ROOT / "crypto-widget.py")], ["--settings"]),
        ("EXE 悬浮窗", [str(ROOT / "dist" / "crypto-widget.exe")], []),
        ("EXE 设置页", [str(ROOT / "dist" / "crypto-widget.exe")], ["--settings"]),
    ]
    with tempfile.TemporaryDirectory(prefix="crypto-widget-smoke-") as directory:
        env = dict(os.environ)
        for key in ("PYTHONHOME", "PYTHONPATH", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM", "QT_SCALE_FACTOR", "QT_SCREEN_SCALE_FACTORS"):
            env.pop(key, None)
        windows = Path(os.environ["SystemRoot"])
        env["PATH"] = os.pathsep.join((str(windows / "System32"), str(windows)))
        for title, command, extra in commands:
            result = subprocess.run(
                command + extra + ["--config", str(Path(directory) / "settings.json"),
                                    "--cache-dir", str(Path(directory) / "icons"), "--quit-after", "300"],
                cwd=directory, env=env, capture_output=True, timeout=30,
            )
            if result.returncode != 0 or b"Traceback" in result.stderr:
                raise RuntimeError(f"{title}启动失败：{result.returncode} {result.stderr!r}")
            print(f"{title}：启动及退出成功")


if __name__ == "__main__":
    main()
