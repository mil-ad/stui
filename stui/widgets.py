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


class Fancy1Button(urwid.WidgetWrap):
    def __init__(self, label, on_press=None, user_data=None):

        w = urwid.Text(label, "center")
        w = FancyLineBox(w, title="")
        # w = urwid.Padding(w, "center", "pack")
        # w = urwid.AttrMap(w, "highlight")
        super().__init__(w)

    def selectable(self):
        return True


class Fancy2Button(urwid.WidgetWrap):
    def __init__(self, label, on_press=None, user_data=None, padding_len=1):
        padding = " " * padding_len
        border = "─" * (len(label) + padding_len * 2)
        # cursor_position = len(border) + padding_size

        w = urwid.Text(
            "╭" + border + "╮\n│" + padding + label + padding + "│\n╰" + border + "╯"
        )
        w = urwid.AttrMap(w, "", "active_tab_label")

        # here is a lil hack: use a hidden button for evt handling
        # TODO:
        self._hidden_btn = urwid.Button("hidden %s" % label, on_press, user_data)

        super().__init__(w)

    def selectable(self):
        return True

    def keypress(self, *args, **kw):
        return self._hidden_btn.keypress(*args, **kw)

    def mouse_event(self, *args, **kw):
        return self._hidden_btn.mouse_event(*args, **kw)


class FancyButton(urwid.WidgetWrap):
    signals = ["click"]

    def __init__(self, label, on_press=None, user_data=None, padding_len=1):

        padding = " " * padding_len
        border = "─" * (len(label) + padding_len * 2)
        # cursor_position = len(border) + padding_size

        w = urwid.Text(
            "╭" + border + "╮\n│" + padding + label + padding + "│\n╰" + border + "╯"
        )
        w = urwid.AttrMap(w, "", "active_tab_label")

        # The old way of listening for a change was to pass the callback
        # in to the constructor.  Just convert it to the new way:
        if on_press:
            urwid.connect_signal(self, "click", on_press, user_data)

        super().__init__(w)

    def sizing(self):
        return frozenset([FLOW])

    def _repr_words(self):
        # include button.label in repr(button)
        return self.__super._repr_words() + [python3_repr(self.label)]

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

        # w = urwid.Edit()
        w = urwid.Text("")
        self.text = w
        w = urwid.LineBox(w)
        w = urwid.AttrMap(w, "inactive_tab_label")
        self.linebox = w

        self.plus = Fancy2Button("+", padding_len=0)
        self.minus = Fancy2Button("-", padding_len=0)

        self.plus = urwid.AttrMap(self.plus, "", "active_tab_label")
        self.minus = urwid.AttrMap(self.minus, "", "active_tab_label")

        cols = [w, (3, self.plus), (3, self.minus)]

        if label is not None:
            l = urwid.Text(
                "\n" + label + " "
            )  # FIXME: Remove the \n hack. Not sure why Filler doesn't work
            # l = urwid.Filler(l, height=3)
            cols = [("weight", 1, l)] + cols

        w = urwid.Columns(cols)
        super().__init__(w)

    def set_value(self, x):
        x = str(x)
        self.text.set_text(x)

    def disable(self):
        self.plus.set_attr_map({"": "disabled_tab_label"})
        self.minus.set_attr_map({"": "disabled_tab_label"})
        self.linebox.set_attr_map({"": "disabled_tab_label"})
        self.set_value("-")

    def enable(self):
        self.plus.set_attr_map({"": "active_tab_label"})
        self.minus.set_attr_map({"": "active_tab_label"})
        self.linebox.set_attr_map({"": "active_tab_label"})


class SelectableColumns(urwid.Columns):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


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
