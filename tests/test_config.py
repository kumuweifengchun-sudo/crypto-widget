import json

import pytest

from crypto_widget.config import DEFAULT_CONFIG, SettingsStore, normalize_symbol, validate_config


def test_legacy_configuration_and_missing_fields(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"symbol1": " hypeusdt ", "pos_x": -500, "decimals1": 5}), encoding="utf-8")
    store = SettingsStore(path)
    result = store.load()
    assert result["symbol1"] == "HYPEUSDT"
    assert result["pos_x"] == -500
    assert result["decimals1"] == 5
    assert result["symbol2"] == DEFAULT_CONFIG["symbol2"]
    assert not store.warning


@pytest.mark.parametrize("content", ["{invalid", "[]", "null", b"\xff\xfe\xff"])
def test_damaged_config_is_preserved(tmp_path, content):
    path = tmp_path / "settings.json"
    data = content if isinstance(content, bytes) else content.encode()
    path.write_bytes(data)
    store = SettingsStore(path)
    assert store.load() == DEFAULT_CONFIG
    assert "损坏" in store.warning
    backups = list(tmp_path.glob("*.bak"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == data
    assert path.read_bytes() == data


def test_invalid_types_and_bounds():
    result, corrected = validate_config({
        "symbol1": "../../escape", "text_size": 100, "bg_opacity": -1,
        "cycle_enabled": "false", "update_interval": 1, "cycle_interval": 0,
        "decimals1": True, "decimals2": 2.5, "pos_x": float("inf"),
    })
    assert result["text_size"] == 64
    assert result["bg_opacity"] == 0
    assert result["update_interval"] == 5
    assert result["cycle_interval"] == 3
    assert result["cycle_enabled"] is True
    assert result["symbol1"] == "BTCUSDT"
    assert result["decimals1"] == result["decimals2"] == 2
    assert len(corrected) == 9


@pytest.mark.parametrize("symbol", ["", " ", "BTC/USDT", "比特币", "../BTC", "A" * 31])
def test_bad_symbols_are_rejected(symbol):
    with pytest.raises(ValueError):
        normalize_symbol(symbol)


def test_atomic_save_preserves_original_on_failure(tmp_path, monkeypatch):
    import crypto_widget.config as module
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    store.save(DEFAULT_CONFIG)
    original = path.read_bytes()
    def fail_replace(*_):
        raise PermissionError("测试写入失败")
    monkeypatch.setattr(module.os, "replace", fail_replace)
    with pytest.raises(PermissionError):
        store.save({**DEFAULT_CONFIG, "symbol1": "HYPEUSDT"})
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_save_roundtrip(tmp_path):
    store = SettingsStore(tmp_path / "nested" / "settings.json")
    config = {**DEFAULT_CONFIG, "symbol1": "HYPEUSDT", "bg_opacity": 0, "cycle_enabled": False}
    store.save(config)
    assert store.load() == config
    assert not list(store.path.parent.glob("*.tmp"))
