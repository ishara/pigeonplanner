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
import gtk.glade

import const
import widgets
import messages
from printing import PrintResults
from toolswindow import ToolsWindow


class ResultWindow:
    def __init__(self, main, pigeons, database):
        self.wTree = gtk.glade.XML(const.GLADERESULT)
        self.wTree.signal_autoconnect(self)

        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            setattr(self, name, w)

        self.main = main
        self.database = database
        self.pigeons = pigeons

        self.resultwindow.set_transient_for(self.main.main)

        self.build_toolbar()
        self.build_treeview()
        self.fill_treeview()

        self.resultwindow.show()

    def build_toolbar(self):
        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(widgets.resultui)
        uimanager.insert_action_group(self.create_action_group(), 0)
        accelgroup = uimanager.get_accel_group()
        self.resultwindow.add_accel_group(accelgroup)

        # Just for now...
        uimanager.get_widget('/Toolbar/Filter').hide()

        toolbar = uimanager.get_widget('/Toolbar')
        self.vbox.pack_start(toolbar, False, False)
        self.vbox.reorder_child(toolbar, 0)

    def create_action_group(self):
        action_group = gtk.ActionGroup("ResultWindowActions")
        action_group.add_actions((
            ("Save", gtk.STOCK_SAVE, None, None,
                    _("Save these results"), self.on_save_clicked),
            ("Preview", gtk.STOCK_PRINT_PREVIEW, None, None,
                    _("View these results"), self.on_preview_clicked),
            ("Print", gtk.STOCK_PRINT, None, None,
                    _("Print these results"), self.on_print_clicked),
            ("Filter", gtk.STOCK_CLEAR, _("_Filter..."), None,
                    _("Set filter options"), self.on_filter_clicked),
            ("Close", gtk.STOCK_CLOSE, None, None,
                    _("Close this window"), self.on_close_window),
           ))

        return action_group

    def build_treeview(self):
        columns = [_("Band no."), _("Year"), _("Date"), _("Racepoint"), _("Placed"), _("Out of"), _("Coefficient"), _("Sector"), _("Type"), _("Category"), _("Weather"), _("Wind"), _("Comment")]
        types = [str, str, str, str, str, int, int, float, str, str, str, str, str, str]

        self.liststore, self.selection = widgets.setup_treeview(self.treeviewres,
                                                                columns, types,
                                                                None, True, True, True)

    def fill_treeview(self):
        self.liststore.clear()

        for result in self.database.get_all_results():
            pindex = result[1]
            date = result[2]
            point = result[3]
            place = result[4]
            out = result[5]
            sector = result[6]
            ftype = result[7]
            category = result[8]
            wind = result[9]
            weather = result[10]
            comment = result[15]

            cof = (float(place)/float(out))*100
            try:
                year = self.pigeons[pindex].year
                ring = self.pigeons[pindex].ring
            except KeyError:
                # HACK Pigeon is removed but results are kept.
                #      Make the band with the pindex.
                ring = pindex[:-4]
                year = pindex[-4:]

            self.liststore.append([pindex, ring, year, date, point, place, out, cof, sector, ftype, category, weather, wind, comment])

        self.liststore.set_sort_column_id(2, gtk.SORT_ASCENDING)

    def on_close_window(self, widget, event=None):
        self.resultwindow.destroy()

    def on_dialog_delete(self, widget, event=None):
        self.filterdialog.hide()
        return True

    def on_filter_clicked(self, widget):
        self.filterdialog.show()

    def on_apply_clicked(self, widget):
        pass

    def on_save_clicked(self, widget):
        self.do_operation('save')

    def on_preview_clicked(self, widget):
        self.do_operation('preview')

    def on_print_clicked(self, widget):
        self.do_operation('print')

    def do_operation(self, op):
        #TODO: put this in module, same code as pedigree
        userinfo = {}

        for address in self.main.database.get_all_addresses():
            if address[9]:
                userinfo['name'] = address[1]
                userinfo['street'] = address[2]
                userinfo['code'] = address[3]
                userinfo['city'] = address[4]
                userinfo['phone'] = address[6]
                userinfo['email'] = address[7]
                break

        if not userinfo.has_key('name'):
            if widgets.message_dialog('question', messages.MSG_NO_INFO, self.resultwindow):
                tw = ToolsWindow(self.main)
                tw.toolsdialog.set_keep_above(True)
                tw.treeview.set_cursor(2)
                tw.on_adadd_clicked(None, pedigree_call=True)
                tw.chkme.set_active(True)

                return
            else:
                userinfo['name'] = ""
                userinfo['street'] = ""
                userinfo['code'] = ""
                userinfo['city'] = ""
                userinfo['phone'] = ""
                userinfo['email'] = ""

        results = []
        for item in self.liststore:
            values = []
            for x in range(2, 14):
                value = self.liststore.get_value(item.iter, x)
                if value == None:
                    value = ''
                if x == 2:
                    value = "%s / %s" %(self.liststore.get_value(item.iter, 1), value[2:])
                if x == 7:
                    value = '%3.2f' %value
                values.append(str(value))
            results.append(values)

        PrintResults(self.resultwindow, results, userinfo, self.main.options.optionList, op)
