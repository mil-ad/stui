import argparse
from datetime import datetime

import urwid

from stui import backend
from stui.nodes import NodesTab
from stui.admin import AdminTab
import stui.widgets as widgets

UPDATE_INTERVAL = 1


class JobQueueWidget(urwid.WidgetWrap):

    signals = ["focus_changed"]

    column_widths = [
        (2,),
        (10,),
        ("weight", 1),
        ("weight", 2),
        (14,),
        ("weight", 1),
        ("weight", 1),
        (6,),
        ("weight", 1),
        (11,),
    ]

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

        header_w = [
            (*weight, urwid.Padding(urwid.Text(c, wrap="ellipsis")),)
            for c, weight in zip(column_labels, self.column_widths)
        ]
        header_w = urwid.Columns(header_w)

        self.walker = urwid.SimpleFocusListWalker([])
        w = widgets.FancyListBox(self.walker)
        w = urwid.Frame(w, header_w)
        w = widgets.FancyLineBox(w, "Queue")

        self.walker.set_focus_changed_callback(self._focus_changed)

        super().__init__(w)

    def update_job_widgets(self, job_widgets):
        self.walker[:] = job_widgets

    def get_focused_job_idx(self):
        _, job_idx = self.walker.get_focus()
        return job_idx

    def _focus_changed(self, idx):
        # TODO: Do something smarter with idx
        urwid.emit_signal(self, "focus_changed")

    def render(self, size, focus=False):
        job_widget, _ = self.walker.get_focus()
        if job_widget is not None:
            if not focus:
                job_widget.set_focus_map(
                    {
                        None: "highlight_out_of_focus",
                        "job_state_running": "highlight_out_of_focus",
                        "job_state_pending": "highlight_out_of_focus",
                    },
                )
            else:
                job_widget.set_focus_map(
                    {
                        None: "highlight",
                        "job_state_running": "highlight",
                        "job_state_pending": "highlight",
                    }
                )

        return self._wrapped_widget.render(size, focus=True)


class JobFilterWidget(urwid.WidgetWrap):
    def __init__(self):

        self.filter_all_partitions = widgets.FancyCheckBox("All Partitions")
        self.filter_my_jobs = widgets.FancyCheckBox("My Jobs")
        self.filter_running = widgets.FancyCheckBox("Running")
        self.filter_gpu = widgets.FancyCheckBox("Use GPU")
        self.filter_job_name = urwid.Edit()
        self.filter_node_name = urwid.Edit()
        # self.filter_interactive = widgets.FancyCheckBox("Interactive")

        w = urwid.Pile(
            [
                urwid.Divider(),
                self.filter_all_partitions,
                self.filter_my_jobs,
                self.filter_running,
                self.filter_gpu,
                # self.filter_interactive,
                urwid.Divider(),
                urwid.Text("Job Name:"),
                urwid.LineBox(self.filter_job_name),
                urwid.Divider(),
                urwid.Text("Node Name:"),
                urwid.LineBox(self.filter_node_name),
            ]
        )

        w = widgets.FancyLineBox(w, "Filter")

        super().__init__(w)

    def all_partitions_selected(self):
        return self.filter_all_partitions.get_state()

    def my_jobs_selected(self):
        return self.filter_my_jobs.get_state()

    def running_jobs_selected(self):
        return self.filter_running.get_state()

    def use_gpu_selected(self):
        return self.filter_gpu.get_state()

    def job_name_filter(self):
        return self.filter_job_name.get_edit_text()

    def node_name_filter(self):
        return self.filter_node_name.get_edit_text()


class JobActionsWidget(urwid.WidgetWrap):

    signals = [
        "cancel_all",
        "cancel_newest",
        "cancel_oldest",
        "cancel_selected",
        "attach_to_selected",
    ]

    def __init__(self):

        self.nice_spinbutton = widgets.SpinButton(
            min=None, max=None, start=" ", step=1, label="Nice:"
        )

        self.throttle_spinbutton = widgets.SpinButton(
            min=1, max=None, start=" ", step=1, label="Throttle:"
        )

        self.attach = widgets.FancyButton("Attach", self._relay_signals)
        self.cancel_all = widgets.FancyButton("Cancel All", self._relay_signals)
        self.cancel_mine = widgets.FancyButton("Cancel", self._relay_signals)
        self.cancel_newest = widgets.FancyButton("Cancel Newest", self._relay_signals)
        self.cancel_oldest = widgets.FancyButton("Cancel Oldest", self._relay_signals)

        w = urwid.Pile(
            [
                urwid.Divider(),
                urwid.Text("Selected Job(s):"),
                self.nice_spinbutton,
                self.throttle_spinbutton,
                urwid.Columns(
                    [("pack", self.cancel_mine), ("pack", self.attach)], dividechars=1
                ),
                urwid.Divider(),
                urwid.Text("My Jobs:"),
                urwid.Padding(self.cancel_all, width="pack"),
                urwid.Padding(self.cancel_newest, width="pack"),
                urwid.Padding(self.cancel_oldest, width="pack"),
            ]
        )
        w = urwid.Filler(w, valign="top")
        w = widgets.FancyLineBox(w, "Actions")

        super().__init__(w)

    def set_nice(self, value):
        self.nice_spinbutton.set_value(value)

    def enable_throttle(self):
        self.throttle_spinbutton.enable()

    def disable_throttle(self):
        self.throttle_spinbutton.disable()

    def set_throttle_value(self, value):
        self.throttle_spinbutton.set_value(str(value))

    def _relay_signals(self, src):
        if src is self.attach:
            self._emit("attach_to_selected")
        elif src is self.cancel_all:
            self._emit("cancel_all")
        elif src is self.cancel_mine:
            self._emit("cancel_selected")
        elif src is self.cancel_newest:
            self._emit("cancel_newest")
        elif src is self.cancel_oldest:
            self._emit("cancel_oldest")


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

        self.fpanel = JobFilterWidget()
        self.apanel = JobActionsWidget()
        right_col = urwid.Pile([("pack", self.fpanel), self.apanel])

        self.view = urwid.Columns(
            [("weight", 80, self.qpanel), ("weight", 20, right_col)], dividechars=1
        )

        self.view_placeholder = urwid.WidgetPlaceholder(self.view)

        # TODO: Don't expose walker object directly?
        urwid.connect_signal(self.qpanel, "focus_changed", self.on_jobs_focus_changed)
        urwid.connect_signal(self.apanel, "cancel_all", self.cancel_popup)
        urwid.connect_signal(self.apanel, "cancel_newest", self.cancel_popup)
        urwid.connect_signal(self.apanel, "cancel_oldest", self.cancel_popup)
        urwid.connect_signal(self.apanel, "cancel_selected", self.cancel_popup)
        urwid.connect_signal(self.apanel, "attach_to_selected", self.attach_popup)

    def on_jobs_focus_changed(self):
        job = self.get_focus_job()

        if job is None:
            return

        self.apanel.set_nice(job.nice)

        if job.array_throttle is not None:
            self.apanel.enable_throttle()
            self.apanel.set_throttle_value(job.array_throttle)
        else:
            self.apanel.disable_throttle()

    def filter_jobs(self, jobs):

        all_partitions_filter = (
            lambda j: True
            if self.fpanel.all_partitions_selected()
            else j.partition in self.cluster.my_partitions
        )

        my_job_filter = (
            lambda j: True
            if not self.fpanel.my_jobs_selected()
            else j.user == self.cluster.me
        )

        running_filter = (
            lambda j: True
            if not self.fpanel.running_jobs_selected()
            else j.is_running()
        )

        gpu_filter = (
            lambda j: True if not self.fpanel.use_gpu_selected() else j.uses_gpu()
        )

        job_name_filter = (
            lambda j: True
            if self.fpanel.job_name_filter() == ""
            else self.fpanel.job_name_filter() in j.name
        )

        node_name_filter = (
            lambda j: True
            if self.fpanel.node_name_filter() == ""
            else self.fpanel.node_name_filter() in ",".join(j.nodes)
        )

        filters = (
            all_partitions_filter,
            my_job_filter,
            running_filter,
            gpu_filter,
            job_name_filter,
            node_name_filter,
        )

        for f in filters:
            jobs = filter(f, jobs)
        jobs = list(jobs)

        return jobs

    def create_job_widgets(self, jobs):

        if len(jobs) == 0:
            return []

        jobs = self.filter_jobs(jobs)
        jobs_widgets = []
        for job in jobs:
            texts = [
                urwid.Text("", wrap="ellipsis"),
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

            w = widgets.SelectableColumns(
                [
                    (*weight, urwid.Padding(t))
                    for weight, t in zip(JobQueueWidget.column_widths, texts)
                ]
            )
            w = urwid.AttrMap(w, None)  # Details be handled by the JobQueueWidget

            jobs_widgets.append(w)

        return jobs_widgets

    def get_focus_job(self):
        job_idx = self.qpanel.get_focused_job_idx()

        if job_idx is None:
            return None
        else:
            return self.jobs[job_idx]

    def refresh(self):
        self.jobs = self.cluster.get_jobs()
        job_widgets = self.create_job_widgets(self.jobs)
        self.qpanel.update_job_widgets(job_widgets)

    def cancel_popup(self, arg):

        ok_button = widgets.FancyButton("OK")
        cancel_button = widgets.FancyButton("Cancel")

        buttons_col = urwid.Columns(
            [(10, cancel_button), (10, ok_button)], dividechars=1, focus_column=0
        )

        urwid.connect_signal(ok_button, "click", self.close_popup, None)
        urwid.connect_signal(cancel_button, "click", self.close_popup, None)

        w = widgets.FancyLineBox(
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

        cancel_button = widgets.FancyButton("Cancel")
        urwid.connect_signal(cancel_button, "click", self.close_popup, None)

        t = urwid.Terminal(attach_fn, encoding="utf-8")
        t_height = 40

        w = widgets.FancyLineBox(
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


class StuiWidget(urwid.WidgetWrap):
    def __init__(self, cluster):

        self.cluster = cluster

        self.header_time = urwid.Text(datetime.now().strftime("%X"), align="right")
        header = urwid.Columns(
            [
                urwid.Text("stui", align="left"),
                urwid.Text(
                    [(None, "Cluster:"), ("magenta", self.cluster.get_name())],
                    align="center",
                ),
                self.header_time,
            ]
        )
        header = urwid.AttrMap(header, "bold")

        self.jobs_tab = JobsTab(self.cluster)
        self.nodes_tab = NodesTab(self.cluster)
        self.admin_tab = AdminTab(self.cluster)

        tabbed = widgets.Tabbed(
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
            ("highlight", "black", "yellow", ""),
            ("highlight_out_of_focus", "black", "brown", ""),
        ]

        self.w = StuiWidget(self.cluster)

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
        try:
            self.loop.run()
        except KeyboardInterrupt:
            pass
        finally:
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
