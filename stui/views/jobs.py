import urwid
from collections import OrderedDict

import stui.widgets as widgets


class JobWidget(urwid.WidgetWrap):

    STATE_ATTR_MAPPING = {
        "BOOT FAIL": {None: ""},
        "CANCELLED": {None: ""},
        "COMPLETED": {None: ""},
        "CONFIGURING": {None: ""},
        "COMPLETING": {None: "job_state_completeing"},
        "DEADLINE": {None: ""},
        "FAILED": {None: ""},
        "NODE FAIL": {None: ""},
        "OUT OF MEMORY": {None: ""},
        "PENDING": {None: "job_state_pending"},
        "PREEMPTED": {None: ""},
        "RUNNING": {None: "job_state_running"},
        "RESV DEL HOLD": {None: ""},
        "REQUEUE FED": {None: ""},
        "REQUEUE HOLD": {None: ""},
        "REQUEUED": {None: ""},
        "RESIZING": {None: ""},
        "REVOKED": {None: ""},
        "SIGNALING": {None: ""},
        "SPECIAL EXIT": {None: ""},
        "STAGE OUT": {None: ""},
        "STOPPED": {None: ""},
        "SUSPENDED": {None: ""},
        "TIMEOUT": {None: ""},
    }

    def __init__(self, job):

        self.columns = OrderedDict()
        self.columns["selected"] = urwid.Text("", wrap="ellipsis")
        self.columns["job_id"] = urwid.Text("", wrap="ellipsis")
        self.columns["array"] = urwid.Text("", wrap="ellipsis")
        self.columns["user"] = urwid.Text("", wrap="ellipsis")
        self.columns["name"] = urwid.Text("", wrap="ellipsis")
        self.columns["state"] = urwid.AttrMap(urwid.Text("", wrap="ellipsis"), None)
        self.columns["partition"] = urwid.Text("", wrap="ellipsis")
        self.columns["nodes"] = urwid.Text("", wrap="ellipsis")
        self.columns["cpus"] = urwid.Text("", wrap="ellipsis")
        self.columns["gres"] = urwid.Text("", wrap="ellipsis")
        self.columns["time"] = urwid.Text("", wrap="ellipsis")

        self.update_values(job)

        w = widgets.SelectableColumns(
            [
                (*weight, urwid.Padding(c))
                for weight, c in zip(
                    JobQueueWidget.column_widths, self.columns.values()
                )
            ]
        )
        w = urwid.AttrMap(w, None)  # Details be handled by the JobQueueWidget

        self.selected = False

        super().__init__(w)

    def update_values(self, job):
        self.columns["job_id"].set_text(job.job_id)
        self.columns["array"].set_text(job.array_str())
        self.columns["user"].set_text(job.user)
        self.columns["name"].set_text(job.name)
        self.columns["state"]._original_widget.set_text(job.state.title())
        self.columns["partition"].set_text(job.partition)
        self.columns["nodes"].set_text(job.nodes)
        self.columns["cpus"].set_text(job.cpus)
        self.columns["gres"].set_text(job.gres)
        self.columns["time"].set_text(job.time)

        self.columns["state"].set_attr_map(self.STATE_ATTR_MAPPING[job.state])

    def set_selected_attr(self, in_focus):
        if in_focus:
            attr = "highlight"
        else:
            attr = "highlight_out_of_focus"

        self._w.set_focus_map(
            {
                None: attr,
                "job_state_running": attr,
                "job_state_pending": attr,
                "job_state_completeing": attr,
            }
        )

    def keypress(self, size, key):
        if key == " ":
            self.toggle_select()
        else:
            return super().keypress(size, key)

    def toggle_select(self):
        if not self.selected:
            self.columns["selected"].set_text("✘")
        else:
            self.columns["selected"].set_text("")
        self.selected = not self.selected

    def is_selected(self):
        return self.selected


class JobQueueWidget(urwid.WidgetWrap):

    signals = ["focus_changed"]

    column_widths = [
        (2,),
        (10,),
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
            "Job Array",
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

    def get_selected_job_idices(self):
        indices = [idx for idx, w in enumerate(self.walker) if w.is_selected()]
        return indices

    def _focus_changed(self, idx):
        # TODO: Do something smarter with idx
        urwid.emit_signal(self, "focus_changed")

    def render(self, size, focus=False):
        job_widget, _ = self.walker.get_focus()
        if job_widget is not None:
            job_widget.set_selected_attr(focus)

        # Force the focus to True even when it's not so that there's always a job
        # highlighted.
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
        # self.select_all = widgets.FancyButton("Select All")
        # self.deselect_all = widgets.FancyButton("Deselect All")

        self.pile = urwid.Pile(
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
                urwid.Divider(),
                # urwid.Columns(
                #     [("pack", self.select_all), ("pack", self.deselect_all)],
                #     dividechars=1,
                # ),
            ]
        )

        w = widgets.FancyLineBox(self.pile, "Filter")

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

    def set_focus_to_job_name_box(self):
        # TODO: This looks very hacky!
        self.pile.focus_position = 7


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

        self.attach = widgets.FancyButton(
            "Attach", self._relay_signals, underline_char=1
        )
        self.cancel_all = widgets.FancyButton(
            "Cancel All", self._relay_signals, underline_char=8
        )
        self.cancel_mine = widgets.FancyButton(
            "Cancel", self._relay_signals, underline_char=1
        )
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

    def set_nice_value(self, value):
        self.nice_spinbutton.set_value(value)

    def enable_nice(self):
        self.nice_spinbutton.enable()

    def disable_nice(self):
        self.nice_spinbutton.disable()

    def enable_throttle(self):
        self.throttle_spinbutton.enable()

    def disable_throttle(self):
        self.throttle_spinbutton.disable()

    def set_throttle_value(self, value):
        self.throttle_spinbutton.set_value(str(value))

    def _relay_signals(self, src):
        if src is self.attach:
            urwid.emit_signal(self, "attach_to_selected")
        elif src is self.cancel_all:
            urwid.emit_signal(self, "cancel_all")
        elif src is self.cancel_mine:
            urwid.emit_signal(self, "cancel_selected")
        elif src is self.cancel_newest:
            urwid.emit_signal(self, "cancel_newest")
        elif src is self.cancel_oldest:
            urwid.emit_signal(self, "cancel_oldest")


class JobTabWidget(urwid.WidgetWrap):
    def __init__(self):

        self.qpanel = JobQueueWidget()
        self.fpanel = JobFilterWidget()
        self.apanel = JobActionsWidget()
        right_col = urwid.Pile([("pack", self.fpanel), self.apanel])

        w = urwid.Columns(
            [("weight", 80, self.qpanel), ("weight", 20, right_col)], dividechars=1
        )

        super().__init__(w)

    def keypress(self, size, key):
        if key == "/":
            # TODO: This looks very hacky.
            self.fpanel.set_focus_to_job_name_box()
            self._wrapped_widget.set_focus_path([1, 0])
        else:
            return super().keypress(size, key)


class JobsTab(object):
    def __init__(self, cluster):
        super().__init__()

        self.cluster = cluster

        # self.qpanel = JobQueueWidget()
        # self.fpanel = JobFilterWidget()
        # self.apanel = JobActionsWidget()
        # right_col = urwid.Pile([("pack", self.fpanel), self.apanel])

        # self.view = urwid.Columns(
        #     [("weight", 80, self.qpanel), ("weight", 20, right_col)], dividechars=1
        # )

        self.view = JobTabWidget()
        # TODO: This is hacky - I don't like it
        self.qpanel = self.view.qpanel
        self.fpanel = self.view.fpanel
        self.apanel = self.view.apanel

        self.view_placeholder = urwid.WidgetPlaceholder(self.view)

        self.job_widgets_dict = {}

        urwid.connect_signal(self.qpanel, "focus_changed", self.on_jobs_focus_changed)
        urwid.connect_signal(self.apanel, "cancel_all", self.cancel_all_init)
        urwid.connect_signal(self.apanel, "cancel_newest", self.cancel_newest_init)
        urwid.connect_signal(self.apanel, "cancel_oldest", self.cancel_oldest_init)
        urwid.connect_signal(self.apanel, "cancel_selected", self.cancel_selected_init)
        urwid.connect_signal(self.apanel, "attach_to_selected", self.attach_popup)

    def on_jobs_focus_changed(self):
        job = self.get_focus_job()

        if job is None:
            return

        self.apanel.set_nice_value(job.nice)

        if job.is_running():
            self.apanel.disable_nice()
            self.apanel.disable_throttle()
        else:
            self.apanel.enable_nice()
            if job.is_array_job_f():
                self.apanel.enable_throttle()
                self.apanel.set_throttle_value(job.array_throttle)

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
        jobs_widgets = [JobWidget(j) for j in jobs]
        return jobs_widgets

    def get_focus_job(self):
        job_idx = self.qpanel.get_focused_job_idx()

        if job_idx is None:
            return None
        else:
            return self.jobs[job_idx]

    def refresh(self):
        self.jobs = self.filter_jobs(self.cluster.get_jobs())
        # job_widgets = self.create_job_widgets(self.jobs)

        job_widgets_ordered = []
        job_widgets_dict = {}
        for job in self.jobs:
            try:
                w = self.job_widgets_dict[job.job_id]
                w.update_values(job)
                job_widgets_ordered.append(w)
                job_widgets_dict[job.job_id] = w
            except KeyError:
                w = JobWidget(job)
                job_widgets_ordered.append(w)
                job_widgets_dict[job.job_id] = w

        # I have to confirm this but I assume that the widgets living in
        # self.job_widgets_dict in previous rounds for jobs that don't exist this time
        # around will be garbage collected as soon as I set the self.job_widgets_dict to
        # the new dictionary created in this function.
        self.job_widgets_dict = job_widgets_dict

        self.qpanel.update_job_widgets(job_widgets_ordered)

    def show_popup(self, w):
        overlay = urwid.Overlay(
            urwid.Filler(w, valign="top"),
            self.view,
            align="center",
            width=("relative", 30),
            valign="middle",
            height=("relative", 30),
        )

        self.view_placeholder.original_widget = overlay

    def close_popup(self, *args, **kwargs):
        self.view_placeholder.original_widget = self.view

    def show_message(self, msg, title=""):
        w = widgets.MessageWidget(msg, self.close_popup, title)
        self.show_popup(w)

    def cancel_all_init(self):
        w = widgets.ConfirmationWidget(
            "Are you sure you want to cancel all your job(s)?",
            self.cancel_all_finish,
            self.close_popup,
        )
        self.show_popup(w)

    def cancel_all_finish(self, *args, **kwargs):
        self.cluster.cancel_my_jobs()
        self.close_popup()

    def cancel_newest_init(self):
        w = widgets.ConfirmationWidget(
            "Are you sure you want to cancel your newest job?",
            self.cancel_newest_finish,
            self.close_popup,
        )
        self.show_popup(w)

    def cancel_newest_finish(self, *args, **kwargs):
        self.cluster.cancel_my_newest_job()
        self.close_popup()

    def cancel_oldest_init(self):
        w = widgets.ConfirmationWidget(
            "Are you sure you want to cancel your oldest job?",
            self.cancel_oldest_finish,
            self.close_popup,
        )
        self.show_popup(w)

    def cancel_oldest_finish(self, *args, **kwargs):
        self.cluster.cancel_my_oldest_job()
        self.close_popup()

    def cancel_selected_init(self):
        job_indices = self.qpanel.get_selected_job_idices()

        if len(job_indices) == 0:
            self.show_message("No jobs have been selected!", "Error")
        else:
            selected_jobs = [self.jobs[idx] for idx in job_indices]
            w = widgets.ConfirmationWidget(
                f"Are you sure you want to cancel selected {len(job_indices)} job(s)?",
                self.cancel_selected_jobs_finish,
                self.close_popup,
                selected_jobs,
            )
            self.show_popup(w)

    def cancel_selected_jobs_finish(self, event_origin, selected_jobs):
        self.cluster.cancel_jobs(selected_jobs)
        self.close_popup()

    def attach_popup(self):

        # FIXME: The fixed height is a hack!

        job = self.get_focus_job()

        if job is None:
            assert False  # FIXME

        cmd = f"sattach {job.job_id}.0"
        if self.cluster.remote:
            cmd = f"ssh -T {self.cluster.remote} " + cmd

        cancel_button = widgets.FancyButton("Cancel")
        urwid.connect_signal(cancel_button, "click", self.close_popup, None)

        t = urwid.Terminal(cmd.split(), encoding="utf-8")
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

    def get_view(self):
        return self.view_placeholder
