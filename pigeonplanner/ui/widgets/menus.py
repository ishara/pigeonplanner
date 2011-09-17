# -*- coding: utf-8 -*-

# This file is part of Pigeon Planner.

# Pigeon Planner is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Pigeon Planner is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Pigeon Planner.  If not, see <http://www.gnu.org/licenses/>


import gtk


ui_mainwindow = """
<ui>
   <menubar name="MenuBar">
      <menu action="FileMenu">
         <menuitem action="Add"/>
         <menuitem action="Addrange"/>
         <separator/>
         <menuitem action="Log"/>
         <separator/>
         <menu action="PrintMenu">
            <menuitem action="PrintPedigree"/>
            <menuitem action="PrintBlank"/>
         </menu>
         <separator/>
         <menu action="BackupMenu">
            <menuitem action="Backup"/>
            <menuitem action="Restore"/>
         </menu>
         <separator/>
         <menuitem action="Quit"/>
      </menu>
      <menu action="EditMenu">
         <menuitem action="Search"/>
         <separator/>
         <menuitem action="Preferences"/>
      </menu>
      <menu action="ViewMenu">
         <menuitem action="Filter"/>
         <separator/>
         <menuitem action="Arrows"/>
         <menuitem action="Stats"/>
         <menuitem action="Toolbar"/>
         <menuitem action="Statusbar"/>
      </menu>
      <menu action="PigeonMenu">
         <menuitem action="Edit"/>
         <menuitem action="Remove"/>
         <menuitem action="Pedigree"/>
         <menuitem action="Addresult"/>
      </menu>
      <menu action="ToolsMenu">
         <menuitem action="Velocity"/>
         <menuitem action="Distance"/>
         <menuitem action="Racepoints"/>
         <menuitem action="Album"/>
         <menuitem action="Addresses"/>
         <menuitem action="Calendar"/>
         <menuitem action="Data"/>
      </menu>
      <menu action="HelpMenu">
         <menuitem action="Home"/>
         <menuitem action="Forum"/>
         <separator/>
         <menuitem action="Update"/>
         <separator/>
         <menuitem action="Info"/>
         <separator/>
         <menuitem action="About"/>
      </menu>
   </menubar>

   <toolbar name="Toolbar">
      <toolitem action="Add"/>
      <separator/>
      <toolitem action="Edit"/>
      <toolitem action="Remove"/>
      <toolitem action="Pedigree"/>
      <separator/>
      <toolitem action="Preferences"/>
      <separator/>
      <toolitem action="About"/>
      <toolitem action="Quit"/>
   </toolbar>
</ui>
"""

ui_photoalbum = """
<ui>
   <toolbar name="Toolbar">
      <toolitem action="First"/>
      <toolitem action="Prev"/>
      <toolitem action="Next"/>
      <toolitem action="Last"/>
      <separator/>
      <toolitem action="Slide"/>
      <separator/>
      <toolitem action="Screen"/>
      <separator/>
      <toolitem action="Fit"/>
      <toolitem action="In"/>
      <toolitem action="Out"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
"""

ui_pedigreewindow = """
<ui>
   <toolbar name="Toolbar">
      <toolitem action="Save"/>
      <toolitem action="Mail"/>
      <separator/>
      <toolitem action="Preview"/>
      <toolitem action="Print"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
"""

ui_resultwindow = """
<ui>
   <toolbar name="Toolbar">
      <toolitem action="Save"/>
      <toolitem action="Mail"/>
      <separator/>
      <toolitem action="Preview"/>
      <toolitem action="Print"/>
      <separator/>
      <toolitem action="Filter"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
"""

ui_printpreview = """
<ui>
   <toolbar name="Toolbar">
      <toolitem action="First"/>
      <toolitem action="Prev"/>
      <toolitem action="Next"/>
      <toolitem action="Last"/>
      <separator/>
      <toolitem action="Fit"/>
      <toolitem action="In"/>
      <toolitem action="Out"/>
      <separator/>
      <toolitem action="Close"/>
   </toolbar>
</ui>
"""


def popup_menu(event, entries):
    """
    Make a right click menu

    @param entries: List of wanted menuentries
    """

    menu = gtk.Menu()
    for stock_id, callback, data in entries:
        item = gtk.ImageMenuItem(stock_id)
        if data:
            item.connect("activate", callback, *data)
        else:
            item.connect("activate", callback)
        item.show()
        menu.append(item)
    menu.popup(None, None, None, event.button, event.time)

