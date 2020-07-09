import argparse
from datetime import datetime

import urwid
from urwid.widget import Divider

from stui import backend
from stui.widgets import *

UPDATE_INTERVAL = 1


global_loop = None #FIXME


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


def job_context_menu():
    cancel_job = urwid.Button("Cancel Job")
    back_button = urwid.Button("Back")

    x = urwid.Pile([cancel_job, back_button])

    x = urwid.Overlay(
        x,
        urwid.SolidFill("\N{MEDIUM SHADE}"),
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

        self.view_placeholder = urwid.WidgetPlaceholder(self.view)

        # TODO FIXME
        # urwid.connect_signal(self.walker, "modified", self.on_job_selected)

    def on_job_selected(self):
        _, job_idx = self.walker.get_focus()
        job = self.jobs[job_idx]

        self.nice_spinbutton.set_value(job.nice)

        if job.array_throttle is not None:
            self.throttle_spinbutton.enable()
            self.throttle_spinbutton.set_value(str(job.array_throttle))
        else:
            self.throttle_spinbutton.disable()

    def queue_panel(self):

        column_labels = [
            "Job ID",
            "User",
            "Name",
            "State",
            "Partition",
            "Node(s)",
            "CPUs",
            "GRES",
            "Time",
        ]
        self.width_weights = [
            (10,),
            ("weight", 1),
            ("weight", 3),
            (14,),
            ("weight", 1),
            ("weight", 1),
            (5,),
            ("weight", 1),
            (11,),
        ]

        header_w = [
            (
                *weight,
                urwid.Padding(urwid.AttrMap(urwid.Text(c, wrap="ellipsis"), "bold")),
            )
            for c, weight in zip(column_labels, self.width_weights)
        ]
        header_w = urwid.Columns(header_w)

        job_widgets, self.jobs = self.get_job_widgets()

        self.walker = urwid.SimpleFocusListWalker(job_widgets)
        lb = FancyListBox(self.walker)

        w = urwid.Frame(lb, header_w)

        return FancyLineBox(w, "Queue",)

    def action_panel(self):

        self.nice_spinbutton = SpinButton(
            min=None, max=None, start=" ", step=1, label="Nice:"
        )

        self.throttle_spinbutton = SpinButton(
            min=1, max=None, start=" ", step=1, label="Throttle:"
        )

        attach = FancyButton("Attach")

        cancel_all = FancyButton("Cancel All")
        cancel_mine = FancyButton("Cancel")
        cancel_newest = FancyButton("Cancel Newest")
        cancel_oldest = FancyButton("Cancel Oldest")

        urwid.connect_signal(cancel_mine, "click", self.cancel_popup, None)
        urwid.connect_signal(attach, "click", self.attach_popup, None)
        urwid.connect_signal(cancel_all, "click", self.cancel_popup, None)
        urwid.connect_signal(cancel_newest, "click", self.cancel_popup, None)
        urwid.connect_signal(cancel_oldest, "click", self.cancel_popup, None)

        f = urwid.Pile(
            [
                urwid.Divider(),
                urwid.Text("Selected Job(s):"),
                self.nice_spinbutton,
                self.throttle_spinbutton,
                # urwid.Padding(urwid.Columns([("pack", cancel_mine), attach]), width="pack"),
                urwid.Padding(cancel_mine, width="pack"),
                urwid.Padding(attach, width="pack"),
                urwid.Divider(),
                urwid.Text("My Jobs:"),
                urwid.Padding(cancel_all, width="pack"),
                urwid.Padding(cancel_newest, width="pack"),
                urwid.Padding(cancel_oldest, width="pack"),
            ]
        )
        f = urwid.Filler(f, valign="top")

        return FancyLineBox(f, "Actions")

    def filter_panel(self):

        self.filter_all_partitions = FancyCheckBox("All Partitions")
        self.filter_my_jobs = FancyCheckBox("My Jobs")
        self.filter_running = FancyCheckBox("Running")
        self.filter_job_name = urwid.Edit()
        self.filter_node_name = urwid.Edit()

        f = urwid.Pile(
            [
                urwid.Divider(),
                self.filter_all_partitions,
                self.filter_my_jobs,
                self.filter_running,
                FancyCheckBox("Use GPU"),
                FancyCheckBox("Interactive"),
                urwid.Divider(),
                urwid.Text("Job Name:"),
                urwid.LineBox(self.filter_job_name),
                urwid.Divider(),
                urwid.Text("Node Name:"),
                urwid.LineBox(self.filter_node_name),
            ]
        )
        # f = urwid.Filler(f, valign="top")

        return FancyLineBox(f, "Filter")

    def filter_jobs(self, jobs):

        all_partitions_filter = (
            lambda j: True
            if self.filter_all_partitions.get_state()
            else j.partition in self.cluster.my_partitions
        )  ## TODO: should be a method in backend

        my_job_filter = (
            lambda j: True
            if not self.filter_my_jobs.get_state()
            else j.user == self.cluster.me
        )

        running_filter = (
            lambda j: True if not self.filter_running.get_state() else j.is_running()
        )

        job_name_filter = (
            lambda j: True
            if self.filter_job_name.get_edit_text() == ""
            else self.filter_job_name.get_edit_text() in j.name
        )

        node_name_filter = (
            lambda j: True
            if self.filter_node_name.get_edit_text() == ""
            else self.filter_node_name.get_edit_text() in ",".join(j.nodes)
        )

        filters = (
            all_partitions_filter,
            my_job_filter,
            running_filter,
            job_name_filter,
            node_name_filter,
        )

        for f in filters:
            jobs = filter(f, jobs)

        return jobs

    def get_job_widgets(self):

        jobs = self.cluster.get_jobs()

        if len(jobs) == 0:
            return [], []

        jobs = self.filter_jobs(jobs)
        jobs_widgets = []
        for job in jobs:
            texts = [
                urwid.Text(job.job_id, wrap="ellipsis"),
                urwid.Text(job.user, wrap="ellipsis"),
                urwid.Text(job.name, wrap="ellipsis"),
                urwid.AttrMap(
                    urwid.Text(job.state, wrap="ellipsis"),
                    *self.STATE_ATTR_MAPPING[job.state],
                ),
                urwid.Text(job.partition, wrap="ellipsis"),
                urwid.Text(job.nodes, wrap="ellipsis"),
                urwid.Text(job.cpus, wrap="ellipsis"),
                urwid.Text(job.gres, wrap="ellipsis"),
                urwid.Text(job.time, wrap="ellipsis"),
            ]

            w = SelectableColumns(
                [
                    (*weight, urwid.Padding(t))
                    for weight, t in zip(self.width_weights, texts)
                ]
            )

            w = urwid.AttrMap(
                w,
                None,
                focus_map={
                    None: "reversed",
                    "job_state_running": "reversed",
                    "job_state_pending": "reversed",
                },
            )  # FIXME

            jobs_widgets.append(w)

        return jobs_widgets, jobs

    def refresh(self):
        self.walker[:], self.jobs = self.get_job_widgets()

    def cancel_popup(self, arg):

        ok_button = FancyButton("OK")
        cancel_button = FancyButton("Cancel")

        buttons_col = urwid.Columns(
            [(10, cancel_button), (10, ok_button)], dividechars=1, focus_column=0
        )

        urwid.connect_signal(ok_button, "click", self.close_popup, None)
        urwid.connect_signal(cancel_button, "click", self.close_popup, None)

        w = FancyLineBox(
            urwid.Pile(
                [
                    urwid.Text("Are you sure you want to cancel selected job(s)?"),
                    urwid.Divider(" "),
                    urwid.Padding(buttons_col, align="center"),
                ]
            )
        )

        overlay = urwid.Overlay(
            urwid.Filler(w, valign="top"),
            self.view,
            align="center",
            width=("relative", 30),
            valign="middle",
            height=("relative", 30),
        )

        self.view_placeholder.original_widget = overlay

    def attach_popup(self, arg):

        cancel_button = FancyButton("Cancel")
        urwid.connect_signal(cancel_button, "click", self.close_popup, None)

        w = FancyLineBox(
            # urwid.Filler(
            urwid.Pile(
                [
                    urwid.Terminal(None, main_loop=global_loop, encoding="utf-8"),
                    urwid.Divider(" "),
                    urwid.Padding(cancel_button, align="center"),
                ]
            ),
            # valign="top",
            # )
        )

        w = urwid.Terminal("ls -l")

        overlay = urwid.Overlay(
            # urwid.Filler(w, valign="top"),
            w,
            self.view,
            align="center",
            width=("relative", 80),
            valign="middle",
            height=("relative", 80),
        )

        self.view_placeholder.original_widget = overlay

    def close_popup(self, cancel):
        if cancel:
            pass

        self.view_placeholder.original_widget = self.view

    def get_view(self):
        return self.view_placeholder


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
                ("Jobs", self.jobs_tab.get_view()),
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

        # TODO: Do this in the background? makes startup slow
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
        global global_loop
        global_loop = self.loop

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
