import asyncio
import logging
from datetime import datetime

import urwid

import stui.widgets as widgets
from stui import backend
from stui.views.admin import AdminTab
from stui.views.jobs import JobsTab
from stui.views.nodes import NodesTab


logger = logging.getLogger("stui")
logger.setLevel(logging.DEBUG)
logger_fh = logging.FileHandler("stui.log", delay=True)
logger_fh.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(logger_fh)

UPDATE_INTERVAL = 1


class StuiWidget(urwid.WidgetWrap):
    def __init__(self, cluster):

        self.cluster = cluster

        self.header_time = urwid.Text(datetime.now().strftime("%X"), align="right")
        self.header_cluster_name = urwid.Text("Cluster: N/A", align="center")

        header = urwid.Columns(
            [
                urwid.Text("stui", align="left"),
                self.header_cluster_name,
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

        self.view = urwid.Frame(tabbed, header)

        self.view_placeholder = urwid.WidgetPlaceholder(self.view)

        self.connecting_popup()

        super().__init__(self.view_placeholder)

    def set_cluster_name(self, cluster_name):
        self.header_cluster_name.set_text(
            [(None, "Cluster:"), ("magenta", cluster_name)]
        )

    def update_time(self):
        time = datetime.now().strftime("%X")
        self.header_time.set_text(time)

    def refresh_jobs(self):
        self.jobs_tab.refresh()

    def connecting_popup(self):
        w = urwid.Text("Connecting to Slurm instance ...")
        w = widgets.FancyLineBox(w)

        overlay = urwid.Overlay(
            w,
            self.view,
            align="center",
            width=("relative", 40),
            valign=("relative", 30),
            height="pack",
        )

        self.view_placeholder.original_widget = overlay

    def password_prompt_popup(self, ok_handler, cancel_handler):

        w = widgets.PasswordPrompt(
            cancel_handler,
            title="SSH Connection Failed",
            msg="No authentication methods (SSH keys/agent) found. Enter login details manually:",
        )

        urwid.connect_signal(w, "user_password_provided", ok_handler)

        overlay = urwid.Overlay(
            w,
            self.view,
            align="center",
            width=("relative", 40),
            valign=("relative", 30),
            height="pack",
        )

        self.view_placeholder.original_widget = overlay

    def cluster_connected_callback(self):
        self.set_cluster_name(self.cluster.get_name())
        self.refresh_jobs()
        self.close_popup()

    def close_popup(self, *args, **kwargs):
        # TODO: Assert that there's an active popup
        self.view_placeholder.original_widget = self.view


class StuiApp(object):

    # (name, foreground, background, mono, foreground_high, background_high)
    palette = [
        ("job_state_running", "light cyan", ""),
        ("job_state_pending", "yellow", ""),
        ("job_state_completeing", "light magenta", ""),
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

    def __init__(self, args):
        super().__init__()

        self.backend = backend.Cluster(args.ssh)
        self.topmost_widget = StuiWidget(self.backend)

        self.loop = urwid.MainLoop(
            self.topmost_widget,
            self.palette,
            handle_mouse=True,
            unhandled_input=self.exit_on_q,
            event_loop=urwid.AsyncioEventLoop(loop=asyncio.get_event_loop()),
            pop_ups=False,
        )

        self.fd = self.loop.watch_pipe(self.cluster_connect_callback)
        self.backend.connect(self.fd)

    def ssh_login_provided_callback(self, user, password):
        self.topmost_widget.connecting_popup()
        self.backend.connect(self.fd, user, password)

    def cluster_connect_callback(self, message) -> bool:
        if message == b"need password" or message == b"wrong password":

            def exit(*args, **kwargs):
                raise urwid.ExitMainLoop()

            self.topmost_widget.password_prompt_popup(
                ok_handler=self.ssh_login_provided_callback, cancel_handler=exit
            )
            return True

        elif message == b"connection established":
            self.fd = None  # TODO: delattr?
            self.register_refresh()
            self.topmost_widget.cluster_connected_callback()

            # Return False will remove the watch from the event loop and closes the
            # "read-end" of the pipe. The write-end of the pipe will be closed
            # in the backend thread.
            return False

    def run(self):
        # Current implementation of urwid uses xterm's 47 escape sequences which are not
        # compatible with some modern terminals like alacritty. I'll do a PR to urwid
        # at some point but in the mean time let's manually use the correct escape seq
        ESC = "\x1b"
        SWITCH_TO_ALTERNATE_BUFFER = ESC + "7" + ESC + "[?1049h"
        RESTORE_NORMAL_BUFFER = ESC + "[?1049l" + ESC + "8"

        self.loop.screen.write(SWITCH_TO_ALTERNATE_BUFFER)
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
        self.topmost_widget.update_time()
        self.topmost_widget.refresh_jobs()
        self.register_refresh()

    def register_refresh(self):
        self.loop.set_alarm_in(UPDATE_INTERVAL, self.refresh_time)
