import unittest

from ui.dialogs.notifications import NotificationCenter


class StubDialog:
    def __init__(self, name: str) -> None:
        self.name = name
        self.open = True


class StubPage:
    def __init__(self) -> None:
        self.dialog = None
        self.updated = False

    def close_dialog(self) -> None:
        self.dialog = None

    def update(self) -> None:
        self.updated = True


class NotificationCenterDialogTests(unittest.TestCase):
    def test_close_dialog_safely_handles_missing_dialog(self) -> None:
        page = StubPage()
        center = NotificationCenter(page, None)

        center._close_dialog_safely()

        self.assertIsNone(page.dialog)

    def test_open_dialog_replaces_previous_dialog(self) -> None:
        page = StubPage()
        center = NotificationCenter(page, None)
        old_dialog = StubDialog("old")
        new_dialog = StubDialog("new")
        page.dialog = old_dialog

        center._open_dialog(new_dialog)

        self.assertIs(page.dialog, new_dialog)
        self.assertTrue(new_dialog.open)
        self.assertFalse(old_dialog.open)


if __name__ == "__main__":
    unittest.main()
