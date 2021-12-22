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

import string
from typing import Optional
from functools import wraps

from gi.repository import Gtk
from gi.repository import Gdk

from pigeonplanner import messages
from pigeonplanner.ui import builder
from pigeonplanner.ui.tools import AddressBook
from pigeonplanner.ui.filechooser import PdfSaver
from pigeonplanner.ui.filechooser import ImageChooser
from pigeonplanner.ui.messagedialog import ErrorDialog
from pigeonplanner.ui.messagedialog import QuestionDialog
from pigeonplanner.ui.pedigreeprintsetup import layout
from pigeonplanner.ui.pedigreeprintsetup import preview
from pigeonplanner.ui.pedigreeprintsetup import reportconfig
from pigeonplanner.core import common
from pigeonplanner.reports import base_pedigree
from pigeonplanner.reportlib import report, PRINT_ACTION_PREVIEW, PRINT_ACTION_EXPORT, PRINT_ACTION_DIALOG
from pigeonplanner.reportlib.styles import PARA_ALIGN_CENTER, PARA_ALIGN_LEFT, PARA_ALIGN_RIGHT
from pigeonplanner.database.models import Pigeon


def location_to_para_align(loc: str) -> int:
    mapping = {"left": PARA_ALIGN_LEFT, "center": PARA_ALIGN_CENTER, "right": PARA_ALIGN_RIGHT}
    return mapping.get(loc, PARA_ALIGN_LEFT)


def setting(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        ret = method(self, *args, **kwargs)
        self._setting_changed()
        return ret

    return wrapper


class PedigreePrintSetupWindow(builder.GtkBuilder):
    def __init__(self, parent: Optional[Gtk.Window], pigeon: Optional[Pigeon]):
        builder.GtkBuilder.__init__(self, "PedigreePrintSetup.ui")

        self._pigeon = pigeon
        self._paper_format = None
        self._layout_loaded = False  # TODO: might want to rename
        self.layout = None

        # TODO: use these existing strings for now. They don't fit here perfectly, but
        #       they're already translated.
        self.widgets.label_address_infobar1.set_text(messages.MSG_NO_INFO[0])
        self.widgets.label_address_infobar2.set_text(messages.MSG_NO_INFO[1])
        self.widgets.infobar_address_info.set_revealed(common.get_own_address() is None)

        self._preview_widget = preview.PrintPreviewWidget.get_instance(self)
        self.widgets.preview_box.pack_start(self._preview_widget, True, True, 0)

        chooser = ImageChooser(self.widgets.window)
        self.widgets.background_image = Gtk.FileChooserButton.new_with_dialog(chooser)  # noqa
        self.widgets.background_image.connect("file-set", self.on_background_image_file_set)
        self.widgets.background_image_box.pack_start(self.widgets.background_image, True, True, 0)

        for layout_name in layout.get_user_layout_names():
            self.widgets.config_layout_combo.append(layout_name, layout_name)
        self.widgets.config_layout_combo.set_active_id("original")

        self.widgets.window.set_transient_for(parent)
        self.widgets.window.show_all()

    def _setting_changed(self):
        if self._layout_loaded:
            self._preview_widget.end_preview()
            self.generate_report(print_action=PRINT_ACTION_PREVIEW)

    def _set_widget_values(self):
        self.widgets.paper_format_combo.set_active_id(self.layout["paper_format"])
        self.widgets.margin_top_spinbutton.set_value(self.layout["margins"]["top"])
        self.widgets.margin_bottom_spinbutton.set_value(self.layout["margins"]["bottom"])
        self.widgets.margin_left_spinbutton.set_value(self.layout["margins"]["left"])
        self.widgets.margin_right_spinbutton.set_value(self.layout["margins"]["right"])

        self.widgets.title_font_size.set_value(self.layout["font_styles"]["Title"]["size"])
        self.widgets.title_color.set_rgba(self.layout["font_styles"]["Title"]["color"])
        self.widgets.title_separator_color.set_rgba(self.layout["graphics_styles"]["TitleSeparator"]["color"])

        self.widgets.user_info_combo.set_active_id(self.layout["options"]["user_info"])
        self.widgets.pigeon_info_combo.set_active_id(self.layout["options"]["pigeon_info"])
        self.widgets.pigeon_image_combo.set_active_id(self.layout["options"]["pigeon_image"])
        self.widgets.header_separator_color.set_rgba(self.layout["graphics_styles"]["HeaderSeparator"]["color"])

        self.widgets.user_name_switch.set_active(self.layout["options"]["user_name"])
        self.widgets.user_address_switch.set_active(self.layout["options"]["user_address"])
        self.widgets.user_phone_switch.set_active(self.layout["options"]["user_phone"])
        self.widgets.user_email_switch.set_active(self.layout["options"]["user_email"])
        self.widgets.user_font_size.set_value(self.layout["font_styles"]["UserInfo"]["size"])
        self.widgets.user_color.set_rgba(self.layout["font_styles"]["UserInfo"]["color"])

        self.widgets.pigeon_name_switch.set_active(self.layout["options"]["pigeon_name"])
        self.widgets.pigeon_sex_switch.set_active(self.layout["options"]["pigeon_sex"])
        self.widgets.pigeon_colour_switch.set_active(self.layout["options"]["pigeon_colour"])
        self.widgets.pigeon_extra_switch.set_active(self.layout["options"]["pigeon_extra"])
        self.widgets.pigeon_font_size.set_value(self.layout["font_styles"]["PigeonInfo"]["size"])
        self.widgets.pigeon_color.set_rgba(self.layout["font_styles"]["PigeonInfo"]["color"])

        if self.layout["options"]["background_image"]:
            self.widgets.background_image.set_filename(self.layout["options"]["background_image"])
        self.widgets.background_width_perc.set_value(self.layout["options"]["background_width_perc"])
        self.widgets.background_height_perc.set_value(self.layout["options"]["background_height_perc"])
        self.widgets.background_x_align_combo.set_active_id(self.layout["options"]["background_x_align"])
        self.widgets.background_y_align_combo.set_active_id(self.layout["options"]["background_y_align"])

        self.widgets.pedigree_layout_pigeon_combo.set_active_id(self.layout["options"]["pedigree_layout_pigeon"])
        self.widgets.gen_1_lines.set_value(self.layout["options"]["pedigree_gen_1_lines"])
        self.widgets.gen_2_lines.set_value(self.layout["options"]["pedigree_gen_2_lines"])
        self.widgets.gen_3_lines.set_value(self.layout["options"]["pedigree_gen_3_lines"])
        self.widgets.gen_4_lines.set_value(self.layout["options"]["pedigree_gen_4_lines"])

        self.widgets.colour_edge_switch.set_active(self.layout["options"]["colour_edge"])
        self.widgets.colour_bg_switch.set_active(self.layout["options"]["colour_bg"])
        self.widgets.pedigree_band_font_size.set_value(self.layout["font_styles"]["PedigreeBoxBand"]["size"])
        self.widgets.pedigree_band_color.set_rgba(self.layout["font_styles"]["PedigreeBoxBand"]["color"])
        self.widgets.pedigree_details_font_size.set_value(
            self.layout["font_styles"]["PedigreeBoxDetailsLeft"]["size"]
        )
        self.widgets.pedigree_details_color.set_rgba(self.layout["font_styles"]["PedigreeBoxDetailsLeft"]["color"])
        self.widgets.pedigree_comments_font_size.set_value(self.layout["font_styles"]["PedigreeBoxComments"]["size"])
        self.widgets.pedigree_comments_color.set_rgba(self.layout["font_styles"]["PedigreeBoxComments"]["color"])

        self.widgets.box_top_right_combo.set_active_id(self.layout["options"]["box_top_right"])
        self.widgets.box_middle_left_combo.set_active_id(self.layout["options"]["box_middle_left"])
        self.widgets.box_middle_right_combo.set_active_id(self.layout["options"]["box_middle_right"])
        self.widgets.box_bottom_left_combo.set_active_id(self.layout["options"]["box_bottom_left"])
        self.widgets.box_comments_switch.set_active(self.layout["options"]["box_comments"])
        self.widgets.pedigree_sex_sign_switch.set_active(self.layout["options"]["pedigree_sex_sign"])

    def load_layout(self, layout_obj: dict):
        self.layout = layout_obj

        self._layout_loaded = False
        self._set_widget_values()

        self._paper_format = layout_obj["paper_format"]
        reportconfig.set_margins(**layout_obj["margins"])
        for style_id, values in layout_obj["font_styles"].items():
            reportconfig.set_font_style(style_id, **values)
        for style_id, values in layout_obj["graphics_styles"].items():
            reportconfig.set_graphics_style(style_id, **values)

        self._layout_loaded = True
        self._preview_widget.end_preview()
        self.generate_report(print_action=PRINT_ACTION_PREVIEW)

    def generate_report(self, print_action: int, filename: Optional[str] = None):
        userinfo = common.get_own_address()
        opts = reportconfig.PedigreeReportOptions(
            self._paper_format,
            print_action=print_action,
            filename=filename,
            parent=self.widgets.window,
            is_pedigree_preview=True,
        )
        report(base_pedigree.PedigreeReport, opts, self._pigeon, userinfo, self.layout)

    def save_pedigree(self):
        if self._pigeon is not None:
            pdfname = "%s_%s.pdf" % (_("Pedigree"), self._pigeon.band.replace(" ", "_").replace("/", "-"))
        else:
            pdfname = "%s.pdf" % _("Pedigree")
        chooser = PdfSaver(self.widgets.window, pdfname)
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            try:
                self.generate_report(print_action=PRINT_ACTION_EXPORT, filename=filename)
            except Exception as exc:
                msg = (_("There was an error saving the pedigree."), str(exc), _("Failed!"))
                ErrorDialog(msg, self.widgets.window)

        chooser.destroy()

    def print_pedigree(self):
        self.generate_report(print_action=PRINT_ACTION_DIALOG)

    def on_window_destroy(self, _widget):
        self._preview_widget.end_preview()
        preview.PrintPreviewWidget.destroy_instance()

    def on_config_layout_combo_changed(self, widget: Gtk.ComboBoxText):
        layout_id = widget.get_active_id()
        if layout_id is None:
            # This happens when removing an item from the combobox
            return
        if layout_id != "custom":
            layout_obj = layout.get_layout(layout_id)
            self.load_layout(layout_obj)
        self.widgets.revealer_config.set_reveal_child(layout_id not in layout.default_layouts)
        self.widgets.button_remove_layout.set_sensitive(layout_id in layout.get_user_layout_names())

    def on_button_remove_layout_clicked(self, _widget):
        layout_id = self.widgets.config_layout_combo.get_active_id()
        msg = _("This will remove layout '%s'.") % layout_id
        response = QuestionDialog((msg, _("Are you sure?"), None), self.widgets.window).run()
        if response:
            layout.remove_layout(layout_id)
            combo_id = self.widgets.config_layout_combo.get_active()
            self.widgets.config_layout_combo.remove(combo_id)
            self.widgets.config_layout_combo.set_active(combo_id - 1)

    def on_button_save_layout_toggled(self, widget: Gtk.MenuButton):
        if widget.get_active():
            layout_id = self.widgets.config_layout_combo.get_active_id()
            self.widgets.entry_config_name.set_text("" if layout_id == "custom" else layout_id)
            self.widgets.entry_config_name.grab_focus()
            self.widgets.entry_config_name.set_position(-1)
            self.widgets.button_save_config.grab_default()

    def _show_error_invalid_layout_name(self, error_msg):
        ErrorDialog((error_msg, None, None), self.widgets.window)
        self.widgets.entry_config_name.grab_focus()
        self.widgets.entry_config_name.set_position(-1)

    def on_button_save_config_clicked(self, _widget):
        valid_characters = string.ascii_letters + string.digits + "-_"
        name = self.widgets.entry_config_name.get_text()
        if not name:
            self._show_error_invalid_layout_name(_("The name is required."))
            return
        if not all(char in valid_characters for char in name):
            error_msg = _("Only the following characters are allowed: %s") % valid_characters
            self._show_error_invalid_layout_name(error_msg)
            return
        if name in layout.default_layouts or name == "custom":
            self._show_error_invalid_layout_name(_("This name is reserved."))
            return

        layout.save_layout(self.layout, name)
        if name not in [row[1] for row in self.widgets.config_layout_combo.get_model()]:
            self.widgets.config_layout_combo.append(name, name)
        self.widgets.config_layout_combo.set_active_id(name)
        self.widgets.save_config_popover.popdown()

    def on_infobar_address_info_response(self, infobar: Gtk.InfoBar, response_id: Gtk.ResponseType):
        if response_id == Gtk.ResponseType.CLOSE:
            infobar.set_revealed(False)
        elif response_id == Gtk.ResponseType.YES:
            book = AddressBook(self.widgets.window)
            book.on_buttonadd_clicked(None)
            book.widgets.checkme.set_active(True)
            book.connect("person-changed", self.on_person_changed)

    def on_person_changed(self, _widget, _person):
        self.widgets.infobar_address_info.set_revealed(common.get_own_address() is None)
        self._setting_changed()

    # ########################################################################
    # Paper

    @setting
    def on_paper_format_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["paper_format"] = widget.get_active_text()
        self._paper_format = widget.get_active_text()

    @setting
    def on_margin_top_spinbutton_value_changed(self, widget: Gtk.SpinButton):
        self.layout["margins"]["top"] = widget.get_value()
        reportconfig.set_margins(top=widget.get_value())

    @setting
    def on_margin_bottom_spinbutton_value_changed(self, widget: Gtk.SpinButton):
        self.layout["margins"]["bottom"] = widget.get_value()
        reportconfig.set_margins(bottom=widget.get_value())

    @setting
    def on_margin_left_spinbutton_value_changed(self, widget: Gtk.SpinButton):
        self.layout["margins"]["left"] = widget.get_value()
        reportconfig.set_margins(left=widget.get_value())

    @setting
    def on_margin_right_spinbutton_value_changed(self, widget: Gtk.SpinButton):
        self.layout["margins"]["right"] = widget.get_value()
        reportconfig.set_margins(right=widget.get_value())

    # ########################################################################
    # Title

    @setting
    def on_title_font_size_value_changed(self, widget: Gtk.SpinButton):
        self.layout["font_styles"]["Title"]["size"] = widget.get_value()
        reportconfig.set_font_style("Title", size=widget.get_value())

    @setting
    def on_title_color_color_set(self, widget: Gtk.ColorButton):
        self.layout["font_styles"]["Title"]["color"] = widget.get_rgba()
        reportconfig.set_font_style("Title", color=widget.get_rgba())

    @setting
    def on_title_separator_color_color_set(self, widget: Gtk.ColorButton):
        self.layout["graphics_styles"]["TitleSeparator"]["color"] = widget.get_rgba()
        reportconfig.set_graphics_style("TitleSeparator", color=widget.get_rgba())

    # ########################################################################
    # Header

    @setting
    def on_user_info_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["user_info"] = widget.get_active_id()
        align = location_to_para_align(widget.get_active_id())
        reportconfig.set_font_style("UserInfo", align=align)

    @setting
    def on_pigeon_info_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["pigeon_info"] = widget.get_active_id()
        align = location_to_para_align(widget.get_active_id())
        reportconfig.set_font_style("PigeonInfo", align=align)

    @setting
    def on_pigeon_image_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["pigeon_image"] = widget.get_active_id()

    @setting
    def on_header_separator_color_color_set(self, widget: Gtk.ColorButton):
        self.layout["graphics_styles"]["HeaderSeparator"]["color"] = widget.get_rgba()
        reportconfig.set_graphics_style("HeaderSeparator", color=widget.get_rgba())

    # ########################################################################
    # User info

    def on_user_details_edit_clicked(self, _widget):
        book = AddressBook(self.widgets.window)
        book.select_user()
        book.connect("person-changed", self.on_person_changed)

    @setting
    def on_user_name_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["user_name"] = widget.get_active()

    @setting
    def on_user_address_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["user_address"] = widget.get_active()

    @setting
    def on_user_phone_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["user_phone"] = widget.get_active()

    @setting
    def on_user_email_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["user_email"] = widget.get_active()

    @setting
    def on_user_font_size_value_changed(self, widget: Gtk.SpinButton):
        self.layout["font_styles"]["UserInfo"]["size"] = widget.get_value()
        reportconfig.set_font_style("UserInfo", size=widget.get_value())

    @setting
    def on_user_color_color_set(self, widget: Gtk.ColorButton):
        self.layout["font_styles"]["UserInfo"]["color"] = widget.get_rgba()
        reportconfig.set_font_style("UserInfo", color=widget.get_rgba())

    # ########################################################################
    # Pigeon info

    @setting
    def on_pigeon_name_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["pigeon_name"] = widget.get_active()

    @setting
    def on_pigeon_sex_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["pigeon_sex"] = widget.get_active()

    @setting
    def on_pigeon_colour_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["pigeon_colour"] = widget.get_active()

    @setting
    def on_pigeon_extra_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["pigeon_extra"] = widget.get_active()

    @setting
    def on_pigeon_font_size_value_changed(self, widget: Gtk.SpinButton):
        self.layout["font_styles"]["PigeonInfo"]["size"] = widget.get_value()
        reportconfig.set_font_style("PigeonInfo", size=widget.get_value())

    @setting
    def on_pigeon_color_color_set(self, widget: Gtk.ColorButton):
        self.layout["font_styles"]["PigeonInfo"]["color"] = widget.get_rgba()
        reportconfig.set_font_style("PigeonInfo", color=widget.get_rgba())

    # ########################################################################
    # Background

    @setting
    def on_background_image_file_set(self, widget: Gtk.FileChooserButton):
        self.layout["options"]["background_image"] = widget.get_filename()

    def on_button_background_image_clear_clicked(self, _widget):
        self.widgets.background_image.unselect_all()
        self.widgets.background_image.emit("file-set")

    @setting
    def on_background_width_perc_value_changed(self, widget: Gtk.SpinButton):
        self.layout["options"]["background_width_perc"] = widget.get_value()

    @setting
    def on_background_height_perc_value_changed(self, widget: Gtk.SpinButton):
        self.layout["options"]["background_height_perc"] = widget.get_value()

    @setting
    def on_background_x_align_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["background_x_align"] = widget.get_active_id()

    @setting
    def on_background_y_align_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["background_y_align"] = widget.get_active_id()

    # ########################################################################
    # Pedigree layout

    @setting
    def on_pedigree_layout_pigeon_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["pedigree_layout_pigeon"] = widget.get_active_id()

    @setting
    def on_gen_1_lines_value_changed(self, widget: Gtk.SpinButton):
        self.layout["options"]["pedigree_gen_1_lines"] = widget.get_value_as_int()

    @setting
    def on_gen_2_lines_value_changed(self, widget: Gtk.SpinButton):
        self.layout["options"]["pedigree_gen_2_lines"] = widget.get_value_as_int()

    @setting
    def on_gen_3_lines_value_changed(self, widget: Gtk.SpinButton):
        self.layout["options"]["pedigree_gen_3_lines"] = widget.get_value_as_int()

    @setting
    def on_gen_4_lines_value_changed(self, widget: Gtk.SpinButton):
        self.layout["options"]["pedigree_gen_4_lines"] = widget.get_value_as_int()

    # ########################################################################
    # Pedigree box

    @setting
    def on_colour_edge_switch_notify(self, widget: Gtk.Switch, _gparam):
        is_active = widget.get_active()
        reportconfig.set_graphics_style(
            "PedigreeBoxCock", color=Gdk.RGBA(0.12, 0.29, 0.53) if is_active else Gdk.RGBA(0, 0, 0)
        )
        reportconfig.set_graphics_style(
            "PedigreeBoxHen", color=Gdk.RGBA(0.53, 0.12, 0.41) if is_active else Gdk.RGBA(0, 0, 0)
        )
        reportconfig.set_graphics_style(
            "PedigreeBoxUnknown", color=Gdk.RGBA(0.39, 0.39, 0.39) if is_active else Gdk.RGBA(0, 0, 0)
        )
        self.layout["options"]["colour_edge"] = is_active

    @setting
    def on_colour_bg_switch_notify(self, widget: Gtk.Switch, _gparam):
        is_active = widget.get_active()
        reportconfig.set_graphics_style(
            "PedigreeBoxCock", fill_color=Gdk.RGBA(0.72, 0.81, 0.90) if is_active else Gdk.RGBA(1, 1, 1)
        )
        reportconfig.set_graphics_style(
            "PedigreeBoxHen", fill_color=Gdk.RGBA(1, 0.80, 0.94) if is_active else Gdk.RGBA(1, 1, 1)
        )
        reportconfig.set_graphics_style(
            "PedigreeBoxUnknown", fill_color=Gdk.RGBA(0.78, 0.78, 0.78) if is_active else Gdk.RGBA(1, 1, 1)
        )
        self.layout["options"]["colour_bg"] = is_active

    @setting
    def on_pedigree_band_font_size_value_changed(self, widget: Gtk.SpinButton):
        self.layout["font_styles"]["PedigreeBoxBand"]["size"] = widget.get_value()
        reportconfig.set_font_style("PedigreeBoxBand", size=widget.get_value())

    @setting
    def on_pedigree_band_color_color_set(self, widget: Gtk.ColorButton):
        self.layout["font_styles"]["PedigreeBoxBand"]["color"] = widget.get_rgba()
        reportconfig.set_font_style("PedigreeBoxBand", color=widget.get_rgba())

    @setting
    def on_pedigree_details_font_size_value_changed(self, widget: Gtk.SpinButton):
        self.layout["font_styles"]["PedigreeBoxDetailsLeft"]["size"] = widget.get_value()
        reportconfig.set_font_style("PedigreeBoxDetailsLeft", size=widget.get_value())
        reportconfig.set_font_style("PedigreeBoxDetailsRight", size=widget.get_value())

    @setting
    def on_pedigree_details_color_color_set(self, widget: Gtk.ColorButton):
        self.layout["font_styles"]["PedigreeBoxDetailsLeft"]["color"] = widget.get_rgba()
        reportconfig.set_font_style("PedigreeBoxDetailsLeft", color=widget.get_rgba())
        reportconfig.set_font_style("PedigreeBoxDetailsRight", color=widget.get_rgba())

    @setting
    def on_pedigree_comments_font_size_value_changed(self, widget: Gtk.SpinButton):
        self.layout["font_styles"]["PedigreeBoxComments"]["size"] = widget.get_value()
        reportconfig.set_font_style("PedigreeBoxComments", size=widget.get_value())

    @setting
    def on_pedigree_comments_color_color_set(self, widget: Gtk.ColorButton):
        self.layout["font_styles"]["PedigreeBoxComments"]["color"] = widget.get_rgba()
        reportconfig.set_font_style("PedigreeBoxComments", color=widget.get_rgba())

    # ########################################################################
    # Pedigree box layout

    @setting
    def on_box_top_right_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["box_top_right"] = widget.get_active_id()

    @setting
    def on_box_middle_left_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["box_middle_left"] = widget.get_active_id()

    @setting
    def on_box_middle_right_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["box_middle_right"] = widget.get_active_id()

    @setting
    def on_box_bottom_left_combo_changed(self, widget: Gtk.ComboBoxText):
        self.layout["options"]["box_bottom_left"] = widget.get_active_id()

    @setting
    def on_box_comments_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["box_comments"] = widget.get_active()

    @setting
    def on_pedigree_sex_sign_switch_notify(self, widget: Gtk.Switch, _gparam):
        self.layout["options"]["pedigree_sex_sign"] = widget.get_active()
