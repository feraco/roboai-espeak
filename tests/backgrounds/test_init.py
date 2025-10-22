from unittest.mock import Mock, mock_open, patch

import pytest

from backgrounds import find_module_with_class, load_background
from backgrounds.base import Background


class MockBackground(Background):
    def run(self):
        pass


def test_load_background_success():
    with (
        patch("backgrounds.find_module_with_class") as mock_find_module,
        patch("importlib.import_module") as mock_import,
    ):
        mock_find_module.return_value = "mock_background"
        mock_module = Mock()
        mock_module.MockBackground = MockBackground
        mock_import.return_value = mock_module

        result = load_background("MockBackground")

        mock_find_module.assert_called_once_with("MockBackground")
        mock_import.assert_called_once_with("backgrounds.plugins.mock_background")
        assert result == MockBackground


def test_load_background_not_found():
    with patch("backgrounds.find_module_with_class") as mock_find_module:
        mock_find_module.return_value = None

        with pytest.raises(
            ValueError,
            match="Class 'NonexistentBackground' not found in any background plugin module",
        ):
            load_background("NonexistentBackground")


def test_load_background_multiple_plugins():
    with (
        patch("backgrounds.find_module_with_class") as mock_find_module,
        patch("importlib.import_module") as mock_import,
    ):
        mock_find_module.return_value = "bg2"
        mock_module2 = Mock()
        mock_module2.Background2 = type("Background2", (Background,), {})
        mock_import.return_value = mock_module2

        result = load_background("Background2")

        mock_find_module.assert_called_once_with("Background2")
        mock_import.assert_called_once_with("backgrounds.plugins.bg2")
        assert result == mock_module2.Background2


def test_load_background_invalid_type():
    with (
        patch("backgrounds.find_module_with_class") as mock_find_module,
        patch("importlib.import_module") as mock_import,
    ):
        mock_find_module.return_value = "invalid_background"

        class InvalidBackground:
            pass

        mock_module = Mock()
        mock_module.InvalidBackground = InvalidBackground
        mock_import.return_value = mock_module

        with pytest.raises(
            ValueError, match="'InvalidBackground' is not a valid background subclass"
        ):
            load_background("InvalidBackground")


def test_find_module_with_class_success():
    with (
        patch("os.path.join") as mock_join,
        patch("os.path.exists") as mock_exists,
        patch("os.listdir") as mock_listdir,
        patch(
            "builtins.open",
            mock_open(read_data="class TestBackground(Background):\n    pass\n"),
        ),
    ):
        mock_join.side_effect = lambda *args: "/".join(args)
        mock_exists.return_value = True
        mock_listdir.return_value = ["test_background.py"]

        result = find_module_with_class("TestBackground")

        assert result == "test_background"


def test_find_module_with_class_not_found():
    with (
        patch("os.path.join") as mock_join,
        patch("os.path.exists") as mock_exists,
        patch("os.listdir") as mock_listdir,
        patch("builtins.open", mock_open(read_data="class OtherClass:\n    pass\n")),
    ):
        mock_join.side_effect = lambda *args: "/".join(args)
        mock_exists.return_value = True
        mock_listdir.return_value = ["other_file.py"]

        result = find_module_with_class("TestBackground")

        assert result is None


def test_find_module_with_class_no_plugins_dir():
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False

        result = find_module_with_class("TestBackground")

        assert result is None
