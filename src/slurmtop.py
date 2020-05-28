import urwid

txt = urwid.Text(u"slurmtop")
fill = urwid.Filler(txt, 'top')
loop = urwid.MainLoop(fill)
loop.run()
