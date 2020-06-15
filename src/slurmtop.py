import urwid
import slurm

UPDATE_INTERVAL = 5


class JobWidget(urwid.Text):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


def exit_on_q(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()


def menu_button(label, callback):
    button = JobWidget(label)
    # button = urwid.Text(label)
    # urwid.connect_signal(button, 'click', callback)
    return urwid.AttrMap(button, None, focus_map="reversed")


class StyledLineBox(urwid.LineBox):
    def __init__(self, original_widget, title):
        super().__init__(
            original_widget,
            title,
            title_align="left",
            tlcorner="╭",
            trcorner="╮",
            blcorner="╰",
            brcorner="╯",
            tline="─",
            bline="─",
            lline="│",
            rline="│",
        )


def menu(title, menu_items):
    return StyledLineBox(urwid.ListBox(urwid.SimpleFocusListWalker(menu_items)), title)


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

    options_panel = StyledLineBox(urwid.Filler(urwid.CheckBox("All")), "Options")

    return StyledLineBox(f, "Options")


def queue_panel():
    jobs = slurm.get_jobs()

    captions = [str(j) for j in jobs]
    print(captions)

    # menu_buttons = []
    # for j in jobs:
    #     c1 = menu_button(j.job_id, job_context_menu)
    #     c2 = menu_button(j.user, job_context_menu)
    #     menu_buttons.append(urwid.Columns([c1, c2]))

    menu_buttons = [menu_button(c, job_context_menu) for c in captions]
    return menu("Queue", menu_buttons)


if __name__ == "__main__":

    qpanel = queue_panel()
    fpanel = filter_panel()

    top_widget = urwid.Columns(
        [("weight", 80, qpanel), ("weight", 20, fpanel)], dividechars=1
    )

    loop = urwid.MainLoop(
        top_widget, palette=[("reversed", "standout", "")], unhandled_input=exit_on_q
    )

    def refresh(_loop, user_data):
        qpanel = queue_panel()
        top_widget.contents[0] = (qpanel, top_widget.options("weight", 80))
        _loop.set_alarm_in(UPDATE_INTERVAL, refresh)

    # loop.set_alarm_in(UPDATE_INTERVAL, refresh)

    loop.run()
