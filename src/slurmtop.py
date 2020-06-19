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
    button = JobRow([urwid.Text(label), urwid.Text(("key", u"running")),])
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

    f = urwid.Pile([urwid.CheckBox("All Partitions"), urwid.CheckBox("Mine")])
    f = urwid.Filler(f, valign="top")

    options_panel = FancyLineBox(urwid.Filler(urwid.CheckBox("All")), "Options")

    return FancyLineBox(f, "Options")


class SlurmtopApp(object):
    def __init__(self):
        super().__init__()

        self.cluster = slurm.Cluster()

        # (name, foreground, background, mono, foreground_high, background_high)
        self.palette = [
            # ("body", "black", "dark cyan", "standout"),
            # ("foot", "light gray", "black"),
            ("key", "light cyan,bold", "", ""),
            # ("title", "white", "black",),
            ("reversed", "standout", ""),
            ("bold", "bold", ""),
        ]

        self.header = urwid.AttrMap(
            urwid.Text(self.cluster.config["ClusterName"], align="center"), "bold"
        )

        self.footer = urwid.Columns(
            [
                (20, TabLineBox(urwid.Text("Queue"))),
                (20, TabLineBox(urwid.Text("Nodes"))),
                (20, TabLineBox(urwid.Text("Admin"))),
                (20, TabLineBox(urwid.Text("Settings"))),
            ]
        )

        qpanel = queue_panel(self.cluster)
        fpanel = filter_panel()

        self.body = urwid.Columns(
            [("weight", 80, qpanel), ("weight", 20, fpanel)], dividechars=1
        )

        self.view = urwid.Frame(
            urwid.AttrWrap(self.body, "body"),
            header=urwid.AttrWrap(self.header, "head"),
            footer=urwid.AttrWrap(self.footer, "foot"),
        )

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
        self.loop.run()
        self.loop.screen.write(RESTORE_NORMAL_BUFFER)

    def exit_on_q(self, key):
        if key in ("q", "Q"):
            raise urwid.ExitMainLoop()

    # def refresh(_loop, user_data):
    #     qpanel = queue_panel()
    #     top_widget.contents[0] = (qpanel, top_widget.options("weight", 80))
    #     _loop.set_alarm_in(UPDATE_INTERVAL, refresh)

    # loop.set_alarm_in(UPDATE_INTERVAL, refresh)


if __name__ == "__main__":
    SlurmtopApp().run()
