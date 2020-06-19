from datetime import datetime

import urwid
from urwid import Text, Columns, Pile, Filler

import slurm

UPDATE_INTERVAL = 5


class FancyLineBox(urwid.LineBox):
    def __init__(self, original_widget, title):
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


class JobText(urwid.Text):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class JobRow(urwid.Columns):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


def create_job_widget(job, callback):
    label = str(job)
    button = JobRow([urwid.Text(label), urwid.Text(("test_A", u"running")),])
    return urwid.AttrMap(button, None, focus_map="reversed")


def queue_panel(cluster):
    header = Columns([Text("Job ID"), Text("Foo")])

    jobs_widgets = [
        create_job_widget(job, job_context_menu) for job in cluster.get_jobs()
    ]

    return FancyLineBox(
        urwid.ListBox(urwid.SimpleFocusListWalker(jobs_widgets)), "Queue",
    )


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


def filter_panel():

    f = urwid.Pile(
        [
            urwid.CheckBox("All Partitions"),
            urwid.CheckBox("My Jobs"),
            urwid.CheckBox("Running"),
            urwid.Divider(),
            urwid.Text("Job Name:"),
            urwid.LineBox(urwid.Edit()),
        ]
    )
    f = urwid.Filler(f, valign="top")

    return FancyLineBox(f, "Filter")


def action_panel():

    f = urwid.Pile(
        [
            urwid.Text("Selected Jobs:"),
            urwid.Button("Cancel"),
            urwid.Button("Nice"),
            urwid.Button("Throttle"),
            urwid.Divider(),
            urwid.Text("All My Jobs:"),
            urwid.Button("Cancel All"),
            urwid.Button("Cancel Newest"),
            urwid.Button("Cancel Oldest"),
        ]
    )
    f = urwid.Filler(f, valign="top")

    return FancyLineBox(f, "Actions")


class Tab(object):
    def __init__(self):
        super().__init__()


class QueueTab(Tab):
    def __init__(self, cluster):
        super().__init__()

        self.cluster = cluster

        qpanel = queue_panel(self.cluster)
        fpanel = filter_panel()

        label = urwid.AttrMap(urwid.Text("Queue"), "active_tab_label")
        self.tab_label = urwid.AttrMap(TabLineBox(label), "active_tab_label")

        self.body = urwid.Columns(
            [("weight", 80, qpanel), ("weight", 20, fpanel)], dividechars=1
        )


class SlurmtopApp(object):
    def __init__(self):
        super().__init__()

        self.cluster = slurm.Cluster()

        # (name, foreground, background, mono, foreground_high, background_high)
        self.palette = [
            ("redbg", "", "light red"),
            ("yellowfg", "yellow", ""),
            ("active_tab_label", "yellow,bold", ""),
            # ("inactive_tab_label", "light gray", ""),
            ("magenta", "light magenta", ""),
            ("dark_gray", "dark gray", ""),
            ("grenbg", "", "light green"),
            ("bluebg", "", "light blue"),
            ("test_A", "light cyan,bold", "", ""),
            ("reversed", "standout", ""),
            ("bold", "bold", ""),
        ]

        queue_tab = QueueTab(self.cluster)

        self.header_time = urwid.Text(datetime.now().strftime("%X"), align="right")
        header = urwid.Columns(
            [
                urwid.Text("slurm-tui", align="left"),
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

        self.footer = urwid.Columns(
            [
                (20, queue_tab.tab_label),
                (20, TabLineBox(urwid.Text("Nodes"))),
                (20, TabLineBox(urwid.Text("Admin"))),
                (20, TabLineBox(urwid.Text("Settings"))),
            ],
            dividechars=0,
        )

        self.view = urwid.Frame(queue_tab.body, header=header, footer=self.footer,)

    def run(self):

        self.loop = urwid.MainLoop(
            self.view, self.palette, unhandled_input=self.exit_on_q,
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
        time = datetime.now().strftime("%X")
        self.header_time.set_text(time)
        self.register_refresh()

    def register_refresh(self):
        self.loop.set_alarm_in(1, self.refresh_time)


if __name__ == "__main__":
    SlurmtopApp().run()
