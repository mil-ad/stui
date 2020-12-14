from typing import Optional
import urwid
from urwid.command_map import ACTIVATE

__all__ = [
    "FancyLineBox",
    "FancyCheckBox",
    "FancyButton",
    "SpinButton",
    "SelectableColumns",
    "TabLineBox",
    "FancyListBox",
    "Tabbed",
    "Tab",
    "MessageWidget",
    "ConfirmationWidget",
    "PasswordPrompt",
]


class FancyLineBox(urwid.LineBox):
    def __init__(self, original_widget, title=""):

        original_widget = urwid.Padding(original_widget, left=1, right=1)
        # FIXME: I don't know why I should pass height here
        # original_widget = urwid.Filler(
        #     original_widget, height=("relative", 100), top=1, bottom=0
        # )

        super().__init__(
            original_widget,
            title,
            title_align="left",
            tline="─",
            trcorner="╮",
            tlcorner="╭",
            bline="─",
            blcorner="╰",
            brcorner="╯",
            lline="│",
            rline="│",
        )


class FancyCheckBox(urwid.CheckBox):
    states = {
        # ☐☒▣▢✓✘
        True: urwid.SelectableIcon("[✘]", 1),
        False: urwid.SelectableIcon("[ ]", 1),
        "mixed": urwid.SelectableIcon("[-]", 1),
    }
    reserve_columns = 4


class FancyButton(urwid.WidgetWrap):
    signals = ["click"]

    def __init__(
        self,
        label,
        on_press=None,
        user_data=None,
        padding_len=1,
        underline_char: Optional[int] = None,
    ):

        padding = " " * padding_len
        border = "─" * (len(label) + padding_len * 2)
        # cursor_position = len(border) + padding_size

        # TODO: Make this cleaner
        label_text = []
        if underline_char:
            assert underline_char <= len(label)

            if underline_char > 1:
                label_text.append((None, label[: underline_char - 1]))

            label_text.append(("underline", label[underline_char - 1]))

            if underline_char < len(label):
                label_text.append((None, label[underline_char:]))
        else:
            label_text.append((None, label))

        w = urwid.Text(
            # ["╭", border, "╮\n│", padding, label, padding, "│\n╰", border, "╯"]
            [
                (None, "╭" + border + "╮\n│" + padding),
                # ("underline", label[0]),
                # (None, label[1:]),
                *label_text,
                (None, padding + "│\n╰" + border + "╯"),
            ]
        )
        w = urwid.AttrMap(
            w,
            attr_map="",
            focus_map={
                None: "active_tab_label",
                "underline": "focus_and_active_tab_label",
            },
        )

        # The old way of listening for a change was to pass the callback
        # in to the constructor.  Just convert it to the new way:
        if on_press:
            urwid.connect_signal(self, "click", on_press, user_data)

        super().__init__(w)

    def sizing(self):
        return frozenset(["flow"])

    def set_label(self, label):
        self._label.set_text(label)

    def selectable(self):
        return True

    def get_label(self):
        return self._label.text

    label = property(get_label)

    def keypress(self, size, key):
        """
        Send 'click' signal on 'activate' command.

        >>> assert Button._command_map[' '] == 'activate'
        >>> assert Button._command_map['enter'] == 'activate'
        >>> size = (15,)
        >>> b = Button(u"Cancel")
        >>> clicked_buttons = []
        >>> def handle_click(button):
        ...     clicked_buttons.append(button.label)
        >>> key = connect_signal(b, 'click', handle_click)
        >>> b.keypress(size, 'enter')
        >>> b.keypress(size, ' ')
        >>> clicked_buttons # ... = u in Python 2
        [...'Cancel', ...'Cancel']
        """

        if self._command_map[key] != ACTIVATE:
            return key

        self._emit("click")

    def mouse_event(self, size, event, button, x, y, focus):
        """
        Send 'click' signal on button 1 press.

        >>> size = (15,)
        >>> b = Button(u"Ok")
        >>> clicked_buttons = []
        >>> def handle_click(button):
        ...     clicked_buttons.append(button.label)
        >>> key = connect_signal(b, 'click', handle_click)
        >>> b.mouse_event(size, 'mouse press', 1, 4, 0, True)
        True
        >>> b.mouse_event(size, 'mouse press', 2, 4, 0, True) # ignored
        False
        >>> clicked_buttons # ... = u in Python 2
        [...'Ok']
        """
        if button != 1 or not urwid.util.is_mouse_press(event):
            return False

        self._emit("click")
        return True


class SpinButton(urwid.WidgetWrap):
    def __init__(self, min, max, start, step, label=None):

        self.text = urwid.Text("")
        w = urwid.LineBox(self.text)
        self.linebox = urwid.AttrMap(w, "inactive_tab_label")

        plus = FancyButton("+", padding_len=0)
        minus = FancyButton("-", padding_len=0)

        self.plus = urwid.AttrMap(plus, "inactive_tab_label", "active_tab_label")
        self.minus = urwid.AttrMap(minus, "inactive_tab_label", "active_tab_label")

        cols = [self.linebox, (3, self.plus), (3, self.minus)]

        if label is not None:
            # FIXME: Remove the \n hack. Not sure why Filler doesn't work
            cols = [("weight", 1, urwid.Text(f"\n{label} "))] + cols

        w = urwid.Columns(cols)
        super().__init__(w)

    def set_value(self, x):
        x = str(x)
        self.text.set_text(x)

    def disable(self):
        # TODO: Why do I have to pass "" in one case and None in another?
        #       Is this a bug in urwid?
        self.plus.set_attr_map({"": "disabled_tab_label"})
        self.minus.set_attr_map({"": "disabled_tab_label"})
        self.linebox.set_attr_map({None: "disabled_tab_label"})
        self.set_value("-")

    def enable(self):
        self.plus.set_attr_map({"": "inactive_tab_label"})
        self.minus.set_attr_map({"": "inactive_tab_label"})
        self.linebox.set_attr_map({"": "inactive_tab_label"})


class SelectableColumns(urwid.Columns):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return super().keypress(size, key)


class TabLineBox(urwid.LineBox):
    def __init__(self, original_widget):
        super().__init__(
            original_widget,
            title="",
            tline="",
            trcorner="",
            tlcorner="",
            bline="─",
            blcorner="╰",
            brcorner="╯",
            lline="│",
            rline="│",
        )


class FancyListBox(urwid.ListBox):
    def keypress(self, size, key):
        if key == "j":
            return super().keypress(size, "down")
        if key == "k":
            return super().keypress(size, "up")
        else:
            return super().keypress(size, key)


class Tab(urwid.WidgetWrap):

    signals = ["click"]

    def __init__(self, label, view):

        self.view = view

        w = urwid.Text(label)
        w = urwid.AttrMap(w, None, focus_map="focus_and_inactive_tab_label")
        self.text_attrmap = w
        w = TabLineBox(w)
        w = urwid.AttrMap(w, attr_map="inactive_tab_label")
        super().__init__(w)

    def selectable(self):
        return True

    def pack(self, size, focus=False):
        return (15, 2)

    def keypress(self, size, key):
        if key == "enter" or key == " ":
            self._emit("click")
        else:
            return super().keypress(size, key)

    def mouse_event(self, size, event, button, col, row, focus):
        if button == 1:
            self._emit("click")

    def set_attr_active(self):
        self._w.set_attr_map({None: "active_tab_label"})
        self.text_attrmap.set_focus_map({None: "focus_and_active_tab_label"})

    def set_attr_inactive(self):
        self._w.set_attr_map({None: "inactive_tab_label"})
        self.text_attrmap.set_focus_map({None: "focus_and_inactive_tab_label"})


class Tabbed(urwid.WidgetWrap):
    def __init__(self, labels, views):

        self.tabs = [Tab(label, view) for label, view in zip(labels, views)]

        for tab in self.tabs:
            urwid.connect_signal(tab, "click", self.set_active_tab)

        self.tab_bar = urwid.Columns([("pack", t) for t in self.tabs], dividechars=0)

        empty_body = urwid.Filler(urwid.Text("test"))
        empty_body = self.tabs[0].view
        w = urwid.Pile([("weight", 1, empty_body), ("pack", self.tab_bar)])
        super().__init__(w)

        self.set_active_tab(self.tabs[0])

    def set_active_tab(self, tab):
        current_options = self._w.contents[0][1]  # TODO: What is this again?
        self._w.contents[0] = (tab.view, current_options)

        self.tab_bar.focus_position = self.tabs.index(tab)
        for t in self.tabs:
            if t is tab:
                t.set_attr_active()
            else:
                t.set_attr_inactive()

    def set_active_next(self):
        next_idx = (self.tab_bar.focus_position + 1) % len(self.tabs)
        self.set_active_tab(self.tabs[next_idx])

    def set_active_prev(self):
        next_idx = (self.tab_bar.focus_position - 1) % len(self.tabs)
        self.set_active_tab(self.tabs[next_idx])

    def active_tab_idx(self):
        return self.tabs.index(self._w.contents[0])

    def keypress(self, size, key):
        if key == "tab":
            self.set_active_next()
        elif key == "shift tab":
            self.set_active_prev()
        else:
            return super().keypress(size, key)


class ConfirmationWidget(urwid.WidgetWrap):
    def __init__(self, msg, ok_handler, cancel_handler, user_data=None):

        ok_button = FancyButton(
            "OK", on_press=ok_handler, padding_len=3, user_data=user_data
        )
        cancel_button = FancyButton("Cancel", on_press=cancel_handler)

        # TODO: I don't understand why I can't apply one Padding with align="center" to
        # align the whole Columns object.
        buttons_col = urwid.Columns(
            [
                urwid.Padding(cancel_button, width="pack", align="right"),
                urwid.Padding(ok_button, width="pack", align="left"),
            ],
            dividechars=1,
            focus_column=0,
        )

        w = urwid.Pile(
            [
                ("pack", urwid.Text(msg)),
                ("pack", urwid.Divider(" ")),
                urwid.Padding(buttons_col, width="pack", align="center"),
            ]
        )

        w = FancyLineBox(w)

        super().__init__(w)


# TODO: Disable the "OK" button when fields' content are invalid
class PasswordPrompt(urwid.WidgetWrap):
    signals = ["user_password_provided"]

    def __init__(self, cancel_handler, title="", msg=None, show_username_field=True):

        self.cancel_handler = cancel_handler  # need to store for processing ESC key
        self.user = urwid.Edit()
        self.password = urwid.Edit(mask="*")

        self.user_row = urwid.Columns(
            [
                ("weight", 1, urwid.Text("\nUsername:")),
                ("weight", 2, urwid.LineBox(self.user)),
            ]
        )

        self.password_row = urwid.Columns(
            [
                ("weight", 1, urwid.Text("\nPassword:")),
                ("weight", 2, urwid.LineBox(self.password)),
            ]
        )

        ok_button = FancyButton(
            "OK", on_press=self.user_password_provided, padding_len=3, user_data=None
        )
        cancel_button = FancyButton("Cancel", on_press=cancel_handler)

        # TODO: Same hack as in ConfirmationWidget.
        buttons_col = urwid.Columns(
            [
                urwid.Padding(cancel_button, width="pack", align="right"),
                urwid.Padding(ok_button, width="pack", align="left"),
            ],
            dividechars=1,
        )

        rows = [
            urwid.Divider(),
            self.user_row,
            self.password_row,
            buttons_col,
        ]

        if msg is not None:
            rows = [urwid.Divider(), urwid.Text(msg)] + rows

        self.pile = urwid.Pile(rows)
        w = FancyLineBox(self.pile, title)

        super().__init__(w)

    def user_password_provided(self, *args, **kwargs):
        u = self.user.get_edit_text()
        p = self.password.get_edit_text()

        if u != "" and p != "":
            urwid.emit_signal(self, "user_password_provided", u, p)

    def keypress(self, size, key):

        # urwid doesn't seem to provide support for Tab/Shift+Tab for next/previous
        # selectable item out of the box hence the inelegant function below
        def cycle_focus(step):
            # TODO: focus_order must be adaptive based on "msg" and
            # "show_username_field" arguments
            focus_order = [[3, 1], [4, 1], [5, 0], [5, 1]]
            focus_path = self.pile.get_focus_path()
            self.pile.set_focus_path(
                focus_order[(focus_order.index(focus_path) + step) % len(focus_order)]
            )

        if key == "tab":
            cycle_focus(1)
        elif key == "shift tab":
            cycle_focus(-1)
        elif key == "enter":
            self.user_password_provided()
        elif key == "esc":
            self.cancel_handler()
        else:
            return super().keypress(size, key)


class MessageWidget(urwid.WidgetWrap):
    def __init__(self, msg, ok_handler, title=""):
        ok_button = FancyButton("OK", on_press=ok_handler, padding_len=3)

        w = urwid.Pile(
            [
                ("pack", urwid.Divider(" ")),
                ("pack", urwid.Text(msg)),
                ("pack", urwid.Divider(" ")),
                urwid.Padding(ok_button, width="pack", align="center"),
            ]
        )

        w = FancyLineBox(w, title)

        super().__init__(w)
