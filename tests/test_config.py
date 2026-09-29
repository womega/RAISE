from importlib.metadata import version

import pytest

from raise_xai import validate_raise_cfg


def test_default_config_is_valid():
    cfg = validate_raise_cfg()
    assert cfg["target"] == "quadrants"
    assert cfg["redundancy"] == "max_improvement"


def test_invalid_threshold_fails():
    with pytest.raises(ValueError):
        validate_raise_cfg({"threshold": 1.1})


def test_version_is_exposed():
    import raise_xai

    assert raise_xai.__version__ == version("raise-xai")
