import urwid
import slurm


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
    return urwid.AttrMap(button, None, focus_map='reversed')

def menu(title, menu_items):
    body = [urwid.Text(title), urwid.Divider()]
    body.extend(menu_items)
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))

def job_context_menu():
    cancel_job = urwid.Button(u"Cancel Job")
    back_button = urwid.Button(u"Back")

    urwid.Pile([cancel_job, back_button])

def job_list():
    jobs = slurm.get_jobs()

    captions = [str(j) for j in jobs]
    print(captions)

    # menu_buttons = []
    # for j in jobs:
    #     c1 = menu_button(j.job_id, job_context_menu)
    #     c2 = menu_button(j.user, job_context_menu)
    #     menu_buttons.append(urwid.Columns([c1, c2]))

    menu_buttons = [menu_button(c, job_context_menu) for c in captions]
    return menu("Job List", menu_buttons)

if __name__ == "__main__":

    lb = job_list()

    loop = urwid.MainLoop(lb, palette=[('reversed', 'standout', '')], unhandled_input=exit_on_q)
    loop.run()
