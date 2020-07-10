import urwid

import stui.widgets as widgets


class AdminTab(object):
    def __init__(self, cluster):
        super().__init__()

        self.cluster = cluster

        w = urwid.Text("Admin: Under Construction ...")
        w = urwid.Filler(w)

        self.view = widgets.FancyLineBox(w, "Admin")
