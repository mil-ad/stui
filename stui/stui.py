import argparse
from datetime import datetime

import urwid

from stui import backend

UPDATE_INTERVAL = 1


class FancyLineBox(urwid.LineBox):
    def __init__(self, original_widget, title):

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


class SpinButton(urwid.WidgetWrap):
    def __init__(self, min, max, start, step, label=None):

        # w = urwid.Edit()
        w = urwid.Text("")
        self.text = w
        w = urwid.LineBox(w)
        w = urwid.AttrMap(w, "disabled_tab_label")

        self.plus = Fancy2Button("+", padding_len=0)
        self.minus = Fancy2Button("-", padding_len=0)

        plus = urwid.AttrMap(self.plus, "", "active_tab_label")
        minus = urwid.AttrMap(self.minus, "", "active_tab_label")

        cols = [w, (3, plus), (3, minus)]

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


class Tab(urwid.WidgetWrap):
    def __init__(
        self, label, view, set_active_fn, set_active_next_fn, set_active_prev_fn
    ):

        self.view = view

        self.set_active_fn = set_active_fn
        self.set_active_next_fn = set_active_next_fn
        self.set_active_prev_fn = set_active_prev_fn

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
            self.set_active_fn(self)
        elif key == "tab":
            self.set_active_next_fn()
        elif key == "shift tab":
            self.set_active_prev_fn()
        else:
            return key

    def mouse_event(self, size, event, button, col, row, focus):
        if button == 1:
            self.set_active_fn(self)

    def set_attr_active(self):
        self._w.set_attr_map({None: "active_tab_label"})
        self.text_attrmap.set_focus_map({None: "focus_and_active_tab_label"})

    def set_attr_inactive(self):
        self._w.set_attr_map({None: "inactive_tab_label"})
        self.text_attrmap.set_focus_map({None: "focus_and_inactive_tab_label"})


class Tabbed(urwid.WidgetWrap):
    def __init__(self, tabs):

        self.tabs = [
            Tab(
                label,
                view,
                self.set_active_tab,
                self.set_active_next,
                self.set_active_prev,
            )
            for label, view in tabs
        ]

        self.tab_bar = urwid.Columns([("pack", t) for t in self.tabs], dividechars=0)

        empty_body = urwid.Filler(urwid.Text("test"))
        empty_body = self.tabs[0].view
        w = urwid.Pile([("weight", 1, empty_body), ("pack", self.tab_bar)])
        super().__init__(w)

        self.set_active_tab(self.tabs[0])

    def set_active_tab(self, tab):
        current_options = self._w.contents[0][1]
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


class JobText(urwid.Text):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class SelectableColumns(urwid.Columns):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


def job_context_menu():
    cancel_job = urwid.Button(u"Cancel Job")
    back_button = urwid.Button(u"Back")

    x = urwid.Pile([cancel_job, back_button])

    x = urwid.Overlay(
        x,
        urwid.SolidFill(u"\N{MEDIUM SHADE}"),
        align="center",
        width=("relative", 60),
        valign="middle",
        height=("relative", 60),
        min_width=20,
        min_height=9,
    )

    return x


class JobsTab(object):

    STATE_ATTR_MAPPING = {
        "Boot Fail": ["", ""],
        "Cancelled": ["", ""],
        "Completed": ["", ""],
        "Configuring": ["", ""],
        "Completing": ["", ""],
        "Deadline": ["", ""],
        "Failed": ["", ""],
        "Node Fail": ["", ""],
        "Out Of Memory": ["", ""],
        "Pending": ["job_state_pending", ""],
        "Preempted": ["", ""],
        "Running": ["job_state_running", ""],
        "Resv Del Hold": ["", ""],
        "Requeue Fed": ["", ""],
        "Requeue Hold": ["", ""],
        "Requeued": ["", ""],
        "Resizing": ["", ""],
        "Revoked": ["", ""],
        "Signaling": ["", ""],
        "Special Exit": ["", ""],
        "Stage Out": ["", ""],
        "Stopped": ["", ""],
        "Suspended": ["", ""],
        "Timeout": ["", ""],
}

    def __init__(self, cluster):
        super().__init__()

        self.cluster = cluster

        self.qpanel = self.queue_panel()
        fpanel = self.filter_panel()
        apanel = self.action_panel()
        right_col = urwid.Pile([("pack", fpanel), apanel])

        self.view = urwid.Columns(
            [("weight", 80, self.qpanel), ("weight", 20, right_col)], dividechars=1
        )

        urwid.connect_signal(self.walker, "modified", self.on_job_selected)

    def on_job_selected(self):
        _, job_idx = self.walker.get_focus()
        job = self.jobs[job_idx]

        self.nice_spinbutton.set_value(job.nice)

        throttle = "-" if job.array_throttle is None else str(job.array_throttle)
        self.throttle_spinbutton.set_value(throttle)

        # array_throttle

    def queue_panel(self):

        column_labels = ["Job ID", "User", "Name", "State", "Partition", "Time"]
        width_weights = [1, 1, 4, 2, 1, 2]
        self.width_weights = width_weights

        header_w = [
            (
                "weight",
                weight,
                urwid.Padding(urwid.AttrMap(urwid.Text(c), "bold")),
            )
            for c, weight in zip(column_labels, width_weights)
        ]
        header_w = urwid.Columns(header_w)

        job_widgets = self.get_job_widgets()

        self.walker = urwid.SimpleFocusListWalker(job_widgets)
        lb = urwid.ListBox(self.walker)

        w = urwid.Frame(lb, header_w)

        return FancyLineBox(w, "Queue",)

    def action_panel(self):

        self.nice_spinbutton = SpinButton(
            min=None, max=None, start=" ", step=1, label="Nice:"
        )

        self.throttle_spinbutton = SpinButton(
            min=1, max=None, start=" ", step=1, label="Throttle:"
        )

        f = urwid.Pile(
            [
                urwid.Divider(),
                urwid.Text("Selected Job(s):"),
                self.nice_spinbutton,
                self.throttle_spinbutton,
                urwid.Padding(Fancy2Button("Cancel"), width="pack"),
                urwid.Divider(),
                urwid.Text("All My Jobs:"),
                urwid.Padding(Fancy2Button("Cancel All"), width="pack"),
                urwid.Padding(Fancy2Button("Cancel Newest"), width="pack"),
                urwid.Padding(Fancy2Button("Cancel Oldest"), width="pack"),
            ]
        )
        f = urwid.Filler(f, valign="top")

        return FancyLineBox(f, "Actions")

    def filter_panel(self):

        f = urwid.Pile(
            [
                urwid.Divider(),
                FancyCheckBox("All Partitions"),
                FancyCheckBox("My Jobs"),
                FancyCheckBox("Running"),
                FancyCheckBox("Use GPU"),
                FancyCheckBox("Interactive"),
                urwid.Divider(),
                urwid.Text("Job Name:"),
                urwid.LineBox(urwid.Edit()),
                urwid.Divider(),
                urwid.Text("Node Name:"),
                urwid.LineBox(urwid.Edit()),
            ]
        )
        # f = urwid.Filler(f, valign="top")

        return FancyLineBox(f, "Filter")


    def get_job_widgets(self):

        jobs_widgets = []
        for job in self.cluster.get_jobs():
            texts = [
                urwid.Text(job.job_id, wrap="ellipsis"),
                urwid.Text(job.user, wrap="ellipsis"),
                urwid.Text(job.name, wrap="ellipsis"),
                urwid.AttrMap(
                    urwid.Text(job.state, wrap="ellipsis"),
                    *self.STATE_ATTR_MAPPING[job.state]
                ),
                urwid.Text(job.partition, wrap="ellipsis"),
                urwid.Text(job.time, wrap="ellipsis"),
            ]

            w = SelectableColumns(
                [
                    ("weight", weight, urwid.Padding(t))
                    for weight, t in zip(self.width_weights, texts)
                ]
            )

            w = urwid.AttrMap(w, None, focus_map={None: "reversed", "job_state_running": "reversed"}) #FIXME

            jobs_widgets.append(w)

        return jobs_widgets

    def refresh(self):
        self.walker[:] = self.get_job_widgets()


class NodesTab(object):
    def __init__(self, cluster):
        super().__init__()

        self.cluster = cluster

        w = urwid.Text("Nodes: Under Construction ...")
        w = urwid.Filler(w)

        self.view = FancyLineBox(w, "Nodes")


class AdminsTab(object):
    def __init__(self, cluster):
        super().__init__()

        self.cluster = cluster

        w = urwid.Text("Admin: Under Construction ...")
        w = urwid.Filler(w)

        self.view = FancyLineBox(w, "Admin")


class AppWidget(urwid.WidgetWrap):
    def __init__(self, cluster):

        self.cluster = cluster

        self.header_time = urwid.Text(datetime.now().strftime("%X"), align="right")
        header = urwid.Columns(
            [
                urwid.Text("stui", align="left"),
                urwid.Text(
                    [
                        (None, "Cluster:"),
                        ("magenta", self.cluster.config["ClusterName"]),
                    ],
                    align="center",
                ),
                # urwid.Text(self.cluster.config["ClusterName"], align="center"),
                self.header_time,
            ]
        )
        header = urwid.AttrMap(header, "bold")

        self.jobs_tab = JobsTab(self.cluster)
        self.nodes_tab = NodesTab(self.cluster)
        self.admin_tab = AdminsTab(self.cluster)

        tabbed = Tabbed(
            [
                ("Jobs", self.jobs_tab.view),
                ("Nodes", self.nodes_tab.view),
                ("Admin", self.admin_tab.view),
            ]
        )

        w = urwid.Frame(tabbed, header)
        super().__init__(w)

    def update_time(self):
        time = datetime.now().strftime("%X")
        self.header_time.set_text(time)

    def refresh_jobs(self):
        self.jobs_tab.refresh()


class SlurmtopApp(object):
    def __init__(self, args):
        super().__init__()

        self.cluster = backend.Cluster(args.remote)

        # (name, foreground, background, mono, foreground_high, background_high)
        self.palette = [
            ("job_state_running", "light cyan", ""),
            ("job_state_pending", "yellow", ""),
            ("active_tab_label", "yellow", ""),
            ("focus_and_active_tab_label", "yellow,underline", ""),
            ("focus_and_inactive_tab_label", "underline", ""),
            ("inactive_tab_label", "", ""),
            ("disabled_tab_label", "dark gray", ""),
            ("magenta", "light magenta", ""),
            ("dark_gray", "dark gray", ""),
            ("test_A", "light cyan,bold", "", ""),
            ("reversed", "standout", ""),
            ("bold", "bold", ""),
            ("underline", "underline", ""),
            ("highlight", "black", "dark blue"),
        ]

        self.w = AppWidget(self.cluster)

    def run(self):

        self.loop = urwid.MainLoop(
            self.w, self.palette, unhandled_input=self.exit_on_q,
        )

        # self.loop.screen.set_terminal_properties(bright_is_bold=False)

        # Current implementation of urwid uses xterm's 47 escape sequences which are not
        # compatible with some modern terminals like alacritty. I'll do a PR to urwid
        # at some point but in the mean time let's manually use the correct escape seq
        ESC = "\x1b"
        SWITCH_TO_ALTERNATE_BUFFER = ESC + "7" + ESC + "[?1049h"
        RESTORE_NORMAL_BUFFER = ESC + "[?1049l" + ESC + "8"

        self.loop.screen.write(SWITCH_TO_ALTERNATE_BUFFER)
        self.register_refresh()
        self.loop.run()
        self.loop.screen.write(RESTORE_NORMAL_BUFFER)

    def exit_on_q(self, key):
        if key in ("q", "Q"):
            raise urwid.ExitMainLoop()

    def refresh_time(self, loop, user_data):
        self.w.update_time()
        self.w.refresh_jobs()
        self.register_refresh()

    def register_refresh(self):
        self.loop.set_alarm_in(UPDATE_INTERVAL, self.refresh_time)


def parse_args():
    parser = argparse.ArgumentParser(description="slurm-tui")

    parser.add_argument(
        "--remote",
        default=None,
        help="Remote destination where slurm controller is running. Format: --remote {Host name defined in ssh config} or --remote {username@server}. Does _not_ prompt for password and relies on ssh-keys for authentication.",
    )

    args = parser.parse_args()

    return args


def main():
    args = parse_args()
    SlurmtopApp(args).run()

if __name__ == "__main__":
    main()
