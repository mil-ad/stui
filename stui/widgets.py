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


class FancyButton(urwid.WidgetWrap):
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

        self.text = urwid.Text("")
        w = urwid.LineBox(self.text)
        self.linebox = urwid.AttrMap(w, "inactive_tab_label")

        plus = FancyButton("+", padding_len=0)
        minus = FancyButton("-", padding_len=0)

        self.plus = urwid.AttrMap(plus, "inactive_tab_label", "active_tab_label")
        self.minus = urwid.AttrMap(minus, "inactive_tab_label", "active_tab_label")

        cols = [self.linebox, (3, self.plus), (3, self.minus)]

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
        # TODO: Why do I have to pass "" in one case and None in another? A bug in urwid?
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
