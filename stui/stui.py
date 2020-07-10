import argparse
from datetime import datetime

import urwid
from urwid.widget import Divider

from stui import backend
from stui.widgets import *

UPDATE_INTERVAL = 1


global_loop = None  # FIXME


class JobQueueWidget(urwid.WidgetWrap):
    def __init__(self):

        column_labels = [
            "",
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
            (2,),
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

        self.walker = urwid.SimpleFocusListWalker([])
        lb = FancyListBox(self.walker)

        w = urwid.Frame(lb, header_w)

        w = FancyLineBox(w, "Queue",)

        super().__init__(w)


class JobsTab(object):

    STATE_ATTR_MAPPING = {
        "BOOT FAIL": ["", ""],
        "CANCELLED": ["", ""],
        "COMPLETED": ["", ""],
        "CONFIGURING": ["", ""],
        "COMPLETING": ["", ""],
        "DEADLINE": ["", ""],
        "FAILED": ["", ""],
        "NODE FAIL": ["", ""],
        "OUT OF MEMORY": ["", ""],
        "PENDING": ["job_state_pending", ""],
        "PREEMPTED": ["", ""],
        "RUNNING": ["job_state_running", ""],
        "RESV DEL HOLD": ["", ""],
        "REQUEUE FED": ["", ""],
        "REQUEUE HOLD": ["", ""],
        "REQUEUED": ["", ""],
        "RESIZING": ["", ""],
        "REVOKED": ["", ""],
        "SIGNALING": ["", ""],
        "SPECIAL EXIT": ["", ""],
        "STAGE OUT": ["", ""],
        "STOPPED": ["", ""],
        "SUSPENDED": ["", ""],
        "TIMEOUT": ["", ""],
    }

    def __init__(self, cluster):
        super().__init__()

        self.cluster = cluster

        self.qpanel = JobQueueWidget()
        self.walker = self.qpanel.walker  # FIXME

        fpanel = self.filter_panel()
        apanel = self.action_panel()
        right_col = urwid.Pile([("pack", fpanel), apanel])

        self.view = urwid.Columns(
            [("weight", 80, self.qpanel), ("weight", 20, right_col)], dividechars=1
        )

        self.view_placeholder = urwid.WidgetPlaceholder(self.view)

        self.jobs_new = OrderedDict()

        urwid.connect_signal(self.walker, "modified", self.on_jobs_modified)

    def on_jobs_modified(self):
        job = self.get_focus_job()

        if job is None:
            return

        self.nice_spinbutton.set_value(job.nice)

        if job.array_throttle is not None:
            self.throttle_spinbutton.enable()
            self.throttle_spinbutton.set_value(str(job.array_throttle))
        else:
            self.throttle_spinbutton.disable()

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
            jobs = list(filter(f, jobs))

        return jobs

    def get_job_widgets(self, jobs):

        if len(jobs) == 0:
            return []

        jobs = self.filter_jobs(jobs)
        jobs_widgets = []
        for job in jobs:
            texts = [
                urwid.Text(job.job_id, wrap="ellipsis"),
                urwid.Text(job.user, wrap="ellipsis"),
                urwid.Text(job.name, wrap="ellipsis"),
                urwid.AttrMap(
                    urwid.Text(job.state.title(), wrap="ellipsis"),
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
                    for weight, t in zip(self.qpanel.width_weights, texts)  # FIXME
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

        return jobs_widgets

    def get_focus_job(self):
        _, job_idx = self.walker.get_focus()

        if job_idx is None:
            return None
        else:
            return self.jobs[job_idx]

    def refresh(self):
        self.jobs = self.cluster.get_jobs()
        self.walker[:] = self.get_job_widgets(self.jobs)

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

        # FIXME: The fixed height is a hack!

        job = self.get_focus_job()

        if job is None:
            assert False  # FIXME

        attach_fn = self.cluster.get_attach_fn(job)

        cancel_button = FancyButton("Cancel")
        urwid.connect_signal(cancel_button, "click", self.close_popup, None)

        t = urwid.Terminal(attach_fn, encoding="utf-8")
        t_height = 40

        w = FancyLineBox(
            urwid.Pile(
                [
                    urwid.BoxAdapter(t, t_height),
                    urwid.Divider("-"),
                    ("pack", urwid.Padding(cancel_button)),
                ]
            ),
        )
        w = urwid.Filler(w, valign="top")

        overlay = urwid.Overlay(
            w,
            self.view,
            align="center",
            width=("relative", 80),
            valign="middle",
            # height=("relative", 80),
            height=t_height + 6,
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


class StuiWidget(urwid.WidgetWrap):
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
            ["Jobs", "Nodes", "Admin"],
            [self.jobs_tab.get_view(), self.nodes_tab.view, self.admin_tab.view],
        )

        w = urwid.Frame(tabbed, header)
        super().__init__(w)

    def update_time(self):
        time = datetime.now().strftime("%X")
        self.header_time.set_text(time)

    def refresh_jobs(self):
        self.jobs_tab.refresh()


class StuiApp(object):
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

        self.w = StuiWidget(self.cluster)

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
    parser = argparse.ArgumentParser(description="stui")

    parser.add_argument(
        "--remote",
        default=None,
        help="Remote destination where slurm controller is running. Format: --remote {Host name defined in ssh config} or --remote {username@server}. Does _not_ prompt for password and relies on ssh-keys for authentication.",
    )

    args = parser.parse_args()

    return args


def main():
    args = parse_args()
    StuiApp(args).run()


if __name__ == "__main__":
    main()
