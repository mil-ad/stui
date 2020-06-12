import urwid

def exit_on_q(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

def job_context_menu():
    cancel_job = urwid.Button(u"Cancel Job")
    back_button = urwid.Button(u"Back")

    urwid.Pile([cancel_job, back_button])

def job_list():
    jobs = [u"job1", u"job2", u"job3"]

    queue = []
    for job in jobs:
        b = urwid.Button(job)
        queue.append(urwid.AttrWrap(b, None, "reversed"))
        urwid.connect_signal(b, "click", job_context_menu)

    lw = urwid.SimpleFocusListWalker(queue)
    lb = urwid.ListBox(lw)

    return lb

if __name__ == "__main__":

    lb = job_list()

    loop = urwid.MainLoop(lb, palette=[('reversed', 'standout', '')], unhandled_input=exit_on_q)
    loop.run()
