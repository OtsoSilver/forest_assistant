import unittest
from types import SimpleNamespace

from core.theme import ThemePreference
from ui.layouts.main_layout import MainLayout


class DummyRouter:
    def __init__(self):
        self.current_tool_id = None
        self.current_tool = None
        self.listeners = []

    def add_listener(self, listener):
        self.listeners.append(listener)

    def navigate(self, tool_id):
        self.current_tool_id = tool_id

    def navigate_to_first(self):
        self.current_tool_id = "glr_to_gpx"


class DummyTheme:
    def __init__(self):
        self.preference = ThemePreference.LIGHT
        self.palette = SimpleNamespace(
            content_bg="#fff",
            sidebar_bg="#fff",
            card_bg="#fff",
            divider="#ddd",
            text_primary="#000",
            text_secondary="#444",
            text_hint="#888",
            accent="#0f0",
            on_accent="#fff",
            accent_container="#eef",
            accent_container_text="#000",
            nav_item_hover_bg="#eee",
            nav_item_selected_bg="#e0e0e0",
            nav_item_selected_text="#000",
            dropzone_border="#ccc",
            dropzone_bg="#fafafa",
            dropzone_active_bg="#e8f5e9",
            dropzone_active_border="#2e7d32",
            shadow="#00000022",
        )

    def add_listener(self, listener):
        return None


class DummySettings:
    def __init__(self):
        self.current = SimpleNamespace(sidebar=SimpleNamespace(collapsed=False), theme_mode="system")

    def update(self, mutation):
        return None


class DummyRegistry:
    def __init__(self):
        self.tools = []

    def add_listener(self, listener):
        return None


class DummyContext:
    def __init__(self):
        self.router = DummyRouter()
        self.theme = DummyTheme()
        self.settings = DummySettings()
        self.registry = DummyRegistry()
        self.notifications = SimpleNamespace(show_error=lambda *args, **kwargs: None)


class MainLayoutBootstrapTests(unittest.TestCase):
    def test_layout_switchers_expand_to_fill_available_space(self):
        layout = MainLayout(DummyContext())

        self.assertTrue(layout._page_switcher.expand)
        self.assertTrue(layout._theme_switcher.expand)


if __name__ == "__main__":
    unittest.main()
