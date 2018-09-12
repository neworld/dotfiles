#!/bin/python2

import gtk
import sys

def create_window():
    window = gtk.Window()
    window.set_default_size(200, 200)
    window.connect('destroy', gtk.main_quit)
    color = gtk.gdk.color_parse(str(sys.argv[1]))
    window.modify_bg(gtk.STATE_NORMAL, color)

    window.maximize()
    window.show()

create_window()
gtk.main()
