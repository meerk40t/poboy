import os
import sys

import wx

from assets import icons8_translation_50
from src.translation_project import TranslationProject
from src.utils import (
    HEADER,
    PRINTF_RE,
    PUNCTUATION,
    TEMPLATE,
    delete_orphans,
    fuzzy_match,
    move_new_to_general,
    obsolete_orphans,
    save,
    save_as_patch,
)

_ = wx.GetTranslation


INTERFACE = {
    "new": {
        "description": """New messages are those items found in the template but not found Portable Object file.

Messages within new are not part of the general population of messages.""",
        "commands": [
            {
                "name": _("Save as patch.po"),
                "command": save_as_patch,
            },
            {
                "name": _("Move new to general"),
                "command": move_new_to_general,
            },
            {
                "name": _("Fuzzy Match"),
                "command": fuzzy_match,
            },
        ],
    },
    "added": {
        "description": """Added messages are those items which are newly found for this template.""",
        "commands": [],
    },
    "removed": {
        "description": """Removed messages are those messages which were included, but no longer are included in this template.""",
        "commands": [],
    },
    "orphan": {
        "description": """Orphan messages are those items found in the Portable Object file but not found in the template.

Messages in orphan are within the general population of messages.""",
        "commands": [
            {"name": _("Obsolete Orphans"), "command": obsolete_orphans},
            {"name": _("Delete Orphans"), "command": delete_orphans},
        ],
    },
    "obsolete": {
        "description": """Obsolete messages are these items commented out in the Portable Object file. This could be because they were moved disabled by a previous update or because they were merely placed in the disabled group.

Messages in obsolete are not part of the general population of messages. However they are saved with the Portable Object file.""",
        "commands": [],
    },
    "issues": {
        "description": """Messages which have issues may be fine. However, their usage is highlighted in order to help avoid potential inconsistencies. They may be minor problems or the issues themselves may be defective and the current translation is correct.""",
        "commands": [],
    },
    "issue-equal": {
        "description": """Messages with this issue are effectively worthless. The default operation of a translation is to do no translation. However this message explicitly does no work. This takes up additional  time and resources to perform no action over the default.        """,
        "commands": [],
    },
    "issue-capitals": {
        "description": """Messages with this issue have different initial capitalizations. This may be because an error was made or simply be flagged in error.

For example, translating "percent" from English to German may be translated "Prozent" and be flagged for inconsistent capitalization. However, "percent" is a noun and all nouns are capitalized in German.""",
        "commands": [],
    },
    "issue-punctuation": {
        "description": """Messages with this issue have different terminal punctuation. The translated item has a different amount final punctuation mark.""",
        "commands": [],
    },
    "issue-ending-whitespace": {
        "description": """This issue occurs when the amount of white space differs between the translated string and original string.""",
        "commands": [],
    },
    "issue-double-space": {
        "description": """This issue occurs when a double space is used within a string. This may be for effect or simply in error.""",
        "commands": [],
    },
    "errors": {
        "description": """Messages which are in error should be fixed. Errors are functional defects in the messages that would prevent these messages from working within the program. Attempting to use them can produce crashes in the program and these should be carefully and effectively eliminated.""",
        "commands": [],
    },
    "error-printf": {
        "description": """Messages with this error have different or inconsistent printf commands too many or too few %s, %f, %d commands or these commands in the wrong order.

Printf commands intend to have values inserted for the printf tokens. If these are not present or if they occur in the wrong order this may cause the program to crash.""",
        "commands": [],
    },
    "error_catalog-locale": {
        "description": """Locale and the base directory are not equal.""",
        "commands": [],
    },
    "fuzzy": {
        "description": """Fuzzy Messages are translated but suspect. These could be close matches during an update process or automatically translated by a machine. The fuzziness of the translation is an indication of the trust we should not have in the utility of this translation.""",
        "commands": [],
    },
    "translated": {
        "description": """Translated messages are those messages for which any value appears in the message string.""",
        "commands": [],
    },
    "untranslated": {
        "description": """Untranslated messages are those messages which have no value in the message string.""",
        "commands": [],
    },
    "all": {
        "description": """List of every message within the current catalog.

Note: All includes only those messages which are actively in the catalog. This will not include, obsolete, or new messages but shall include orphans.""",
        "commands": [],
    },
}


supported_languages = (
    ("en", "English", wx.LANGUAGE_ENGLISH),
    ("it", "italiano", wx.LANGUAGE_ITALIAN),
    ("fr", "français", wx.LANGUAGE_FRENCH),
    ("de", "Deutsch", wx.LANGUAGE_GERMAN),
    ("es", "español", wx.LANGUAGE_SPANISH),
    ("zh", "中文", wx.LANGUAGE_CHINESE),
    ("hu", "Magyar", wx.LANGUAGE_HUNGARIAN),
)


class TranslationPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: TranslationPanel.__init__
        kwds["style"] = kwds.get("style", 0) | wx.WANTS_CHARS
        wx.Panel.__init__(self, *args, **kwds)
        self.catalog = ""
        self.project = TranslationProject()

        self.do_not_update = False

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.tree = wx.TreeCtrl(
            self,
            wx.ID_ANY,
            style=wx.TR_HAS_BUTTONS
            | wx.TR_HAS_VARIABLE_ROW_HEIGHT
            | wx.TR_NO_LINES
            | wx.TR_SINGLE
            | wx.TR_TWIST_BUTTONS,
        )
        main_sizer.Add(self.tree, 1, wx.EXPAND, 0)

        self.panel_message_single = SingleMessagePanel(
            self, wx.ID_ANY, translation_panel=self
        )
        main_sizer.Add(self.panel_message_single, 3, wx.EXPAND, 0)

        sizer_catalog_statistics = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(sizer_catalog_statistics, 3, wx.EXPAND, 0)

        self.panel_catalog = CatalogPanel(self, wx.ID_ANY, translation_panel=self)
        sizer_catalog_statistics.Add(self.panel_catalog, 3, wx.EXPAND, 0)

        self.panel_statistics = StatisticsPanel(self, wx.ID_ANY, translation_panel=self)
        sizer_catalog_statistics.Add(self.panel_statistics, 3, wx.EXPAND, 0)

        self.panel_file_information = FileInformationPanel(
            self, wx.ID_ANY, translation_panel=self
        )
        sizer_catalog_statistics.Add(self.panel_file_information, 3, wx.EXPAND, 0)

        sizer_template_statistics = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(sizer_template_statistics, 3, wx.EXPAND, 0)

        self.panel_template = TemplatePanel(self, wx.ID_ANY, translation_panel=self)
        sizer_template_statistics.Add(self.panel_template, 3, wx.EXPAND, 0)

        self.panel_template_file_information = FileInformationPanel(
            self, wx.ID_ANY, translation_panel=self
        )
        sizer_template_statistics.Add(
            self.panel_template_file_information, 3, wx.EXPAND, 0
        )

        self.panel_project = ProjectPanel(self, wx.ID_ANY, translation_panel=self)
        main_sizer.Add(self.panel_project, 3, wx.EXPAND, 0)

        self.panel_info = InfoPanel(self, wx.ID_ANY, translation_panel=self)
        main_sizer.Add(self.panel_info, 3, wx.EXPAND, 0)

        self.SetSizer(main_sizer)

        self.Layout()

        self.color_translated = wx.Colour((0, 127, 0))
        self.color_untranslated = wx.Colour((127, 0, 0))
        self.color_template = wx.Colour((0, 0, 127))
        self.color_template_translated = wx.Colour((0, 127, 127))

        self.show_project_panel()

        self.root = self.tree.AddRoot(_("Project"), data=(None, "project"))

        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_selection)
        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_tree_menu)

    def _build_menu_file(self):
        wxglade_tmp_menu = wx.Menu()
        root = self.Parent
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "New\tCtrl+N", "")
        root.Bind(wx.EVT_MENU, self.on_menu_new, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Open Project Directory\tCtrl+O", "")
        root.Bind(wx.EVT_MENU, self.on_menu_open, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Save All Project Files\tCtrl+S", "")
        root.Bind(wx.EVT_MENU, self.on_menu_open, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Save Translation\tCtrl+T", "")
        root.Bind(wx.EVT_MENU, self.on_menu_save_translation, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Save Template\tCtrl+M", "")
        root.Bind(wx.EVT_MENU, self.on_menu_save_template, item)
        item = wxglade_tmp_menu.Append(
            wx.ID_ANY, "Save Translation as\tCtrl+Shift+T", ""
        )
        root.Bind(wx.EVT_MENU, self.on_menu_save_as_translation, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Save Template as\tCtrl+Shift+M", "")
        root.Bind(wx.EVT_MENU, self.on_menu_save_as_template, item)
        return wxglade_tmp_menu

    def on_menu_new(self, event):
        self.clear_project()

    def on_menu_open(self, event):
        self.open_project_directory()

    def on_menu_save_as_translation(self, event):
        self.open_save_translation_dialog()

    def on_menu_save_as_template(self, event):
        self.open_save_template_dialog()

    def on_menu_save_translation(self, event):
        self.try_save_working_file_translation()

    def on_menu_save_template(self, event):
        self.try_save_working_file_template()

    def _build_menu_actions(self):
        root = self.Parent
        wxglade_tmp_menu = wx.Menu()
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Compile MO", "")
        root.Bind(wx.EVT_MENU, self.on_menu_action_compile, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Extract Sources\tCtrl+G", "")
        root.Bind(wx.EVT_MENU, self.on_menu_action_extract, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Init New Translation\tCtrl+I", "")
        root.Bind(wx.EVT_MENU, self.on_menu_action_init, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Update Catalogs\tCtrl+U", "")
        root.Bind(wx.EVT_MENU, self.on_menu_action_update, item)
        return wxglade_tmp_menu

    def on_menu_action_update(self, event):
        with wx.BusyInfo("Updating all translations with current template."):
            self.action_update()

    def on_menu_action_extract(self, event):
        with wx.BusyInfo("Extracting sources to generate new template."):
            self.action_extract()

    def on_menu_action_init(self, event):
        self.action_init()

    def on_menu_action_compile(self, event):
        self.action_compile()

    def _build_menu_navigate(self):
        root = self.Parent
        wxglade_tmp_menu = wx.Menu()
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Previous Entry\tCtrl+Up", "")
        root.Bind(wx.EVT_MENU, self.on_menu_previous, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Next Entry\tCtrl+Down", "")
        root.Bind(wx.EVT_MENU, self.on_menu_next, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Copy Source\tAlt+Down", "")
        root.Bind(wx.EVT_MENU, self.on_menu_source, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "New Line\tShift+Enter", "")
        root.Bind(wx.EVT_MENU, self.on_menu_new_line, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Mark Fuzzy\tCtrl+F", "")
        root.Bind(wx.EVT_MENU, self.on_menu_fuzzy, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "Mark Not Fuzzy\tAlt+F", "")
        root.Bind(wx.EVT_MENU, self.on_menu_unfuzzy, item)
        return wxglade_tmp_menu

    def on_menu_previous(self, event):
        self.tree_move_to_previous()

    def on_menu_next(self, event):
        self.tree_move_to_next()

    def on_menu_source(self, event):
        self.translation_copy_original_to_translated()

    def on_menu_new_line(self, event):
        self.force_new_line()

    def on_menu_fuzzy(self, event):
        self.force_fuzzy()

    def on_menu_unfuzzy(self, event):
        self.force_unfuzzy()

    def build_menu(self, menu_bar):
        menu_bar.Append(self._build_menu_file(), "File")
        menu_bar.Append(self._build_menu_actions(), "Actions")
        menu_bar.Append(self._build_menu_navigate(), "Navigate")

    def open_project_directory(self):
        directory = None
        dlg = wx.DirDialog(
            self,
            message=_("Choose python sources directory"),
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            directory = os.path.abspath(dlg.GetPath())
            self.project.directory = directory
            self.panel_project.update_pane()
        else:
            return
        dlg.Destroy()
        self.open_project()
        return directory

    def open_save_translation_dialog(self):
        if self.catalog is None:
            return
        with wx.FileDialog(
            self,
            _("Save Translation"),
            wildcard="*.po",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return None
            pathname = fileDialog.GetPath()
            if not pathname.lower().endswith(".po"):
                pathname += ".po"
            catalog = self.project.catalogs[self.catalog]
            save(catalog, filename=pathname)
            return pathname

    def open_save_template_dialog(self):
        with wx.FileDialog(
            self,
            _("Save Template"),
            wildcard="*.pot|*.po",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return None
            pathname = fileDialog.GetPath()
            if not pathname.lower().endswith(".pot"):
                pathname += ".pot"
            catalog = self.project.catalogs[TEMPLATE]

            self.project.save(catalog)
            return pathname

    def open_load_translation_dialog(self):
        with wx.FileDialog(
            self,
            _("Open"),
            wildcard="*.po",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            # fileDialog.SetFilename(default_file)
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return None
            pathname = fileDialog.GetPath()
            self.project.load(pathname)
            self.tree_rebuild_tree()
            return pathname

    def open_load_template_dialog(self):
        with wx.FileDialog(
            self,
            _("Open"),
            wildcard="*.pot",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            # fileDialog.SetFilename(default_file)
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return None
            pathname = fileDialog.GetPath()
            self.project.load(pathname)
            self.tree_rebuild_tree()
            return pathname

    def open_project(self):
        with wx.BusyInfo(_("Loading all translations files.")):
            self.project.load_all_translations()
        with wx.BusyInfo(_("Calculating Differences...")):
            self.project.calculate_updates()
        self.tree_rebuild_tree()

    def delete_equals(self):
        for catalog in self.project.catalogs.values():
            for message in catalog:
                if message.id == message.string:
                    message.string = None
                    self.message_revalidate(catalog, message)

    def move_orphans_to_obsolete(self):
        for catalog in self.project.catalogs.values():
            for m in list(catalog.orphans.values()):
                m.modified = True
                catalog.obsolete[m.id] = m
                del catalog.orphans[m.id]
                self.message_revalidate(catalog, m)

    def action_init(self):
        dlg = wx.TextEntryDialog(
            None,
            _("Provide the Translation locale"),
            _("Initializing Template"),
            "",
        )
        dlg.SetValue("")

        if dlg.ShowModal() == wx.ID_OK:
            locale = dlg.GetValue()
            self.project.init(locale=locale)
        dlg.Destroy()
        self.tree_rebuild_tree()

    def action_update(self):
        self.project.babel_update()
        self.tree_rebuild_tree()

    def action_extract(self):
        with wx.BusyInfo(_("Generating template from sources.")):
            self.project.babel_extract()
            self.tree_rebuild_tree()

    def action_compile(self):
        self.project.compile_all()

    def update_translations(self):
        self.project.perform_updates()
        self.project.mark_all_orphans_obsolete()
        self.tree_rebuild_tree()

    def clear_project(self):
        self.project.clear()
        self.tree_rebuild_tree()

    def try_save_working_file_translation(self):
        if self.catalog is None:
            return
        catalog = self.project.catalogs[self.catalog]
        try:
            save(catalog)
        except FileNotFoundError:
            self.open_save_translation_dialog()

    def try_save_working_file_template(self):
        catalog = self.project.catalogs[TEMPLATE]
        try:
            save(catalog)
        except FileNotFoundError:
            self.open_save_template_dialog()

    def tree_rebuild_tree(self):
        self.do_not_update = True
        with wx.BusyInfo(_("Rebuilding Tree...")):
            self._tree_rebuild()
        self.do_not_update = False
        self.tree.SelectItem(self.root)

    def _tree_build_template(self):
        tree = self.tree
        try:
            catalog = self.project.catalogs[TEMPLATE]
            catalog.item = tree.AppendItem(
                self.root, _("Template"), data=(catalog, "template")
            )
            if len(catalog.new):
                catalog.workflow_added = tree.AppendItem(
                    catalog.item, _("Added"), data=(catalog, "added")
                )
                tree.SetItemTextColour(catalog.workflow_added, wx.GREEN)
                for message in catalog.new.values():
                    msgid = str(message.id)
                    name = msgid.strip()
                    if name == HEADER:
                        name = _("HEADER")
                    message.item = tree.AppendItem(
                        catalog.workflow_added, name, data=(catalog, message)
                    )
            if len(catalog.orphans):
                catalog.workflow_removed = tree.AppendItem(
                    catalog.item, _("Removed"), data=(catalog, "removed")
                )
                tree.SetItemTextColour(catalog.workflow_removed, wx.RED)
                for message in catalog.orphans.values():
                    msgid = str(message.id)
                    name = msgid.strip()
                    if name == HEADER:
                        name = _("HEADER")
                    message.item = tree.AppendItem(
                        catalog.workflow_removed, name, data=(catalog, message)
                    )
            for message in catalog:
                msgid = str(message.id)
                name = msgid.strip()
                if name == HEADER:
                    name = _("HEADER")
                message.item = tree.AppendItem(
                    catalog.item, name, data=(catalog, message)
                )
            self.template = catalog
        except KeyError:
            self.template = None

    def _tree_build_catalog(self, locale, catalog):
        tree = self.tree
        catalog.item = tree.AppendItem(self.root, locale, data=(catalog, "root"))
        if str(catalog.locale) != locale:
            catalog.item = tree.AppendItem(
                catalog.item,
                _("%s, locale != directory") % str(catalog.locale),
                data=(catalog, "error_catalog-locale"),
            )
            tree.SetItemTextColour(catalog.item, wx.RED)

        catalog.errors = tree.AppendItem(
            catalog.item, _("Errors"), data=(catalog, "errors")
        )
        tree.SetItemTextColour(catalog.errors, wx.RED)

        catalog.error_printf = tree.AppendItem(
            catalog.errors, _("printf-tokens"), data=(catalog, "error-printf")
        )

        catalog.issues = tree.AppendItem(
            catalog.item, _("Issues"), data=(catalog, "issues")
        )
        tree.SetItemTextColour(catalog.issues, wx.Colour(127, 127, 0))

        catalog.warning_equal = tree.AppendItem(
            catalog.issues, _("msgid==msgstr"), data=(catalog, "issue-equal")
        )
        catalog.warning_start_capital = tree.AppendItem(
            catalog.issues, _("capitalization"), data=(catalog, "issue-capitals")
        )
        catalog.warning_end_punct = tree.AppendItem(
            catalog.issues,
            _("ending punctuation"),
            data=(catalog, "issue-punctuation"),
        )
        catalog.warning_end_space = tree.AppendItem(
            catalog.issues,
            _("ending whitespace"),
            data=(catalog, "issue-ending-whitespace"),
        )
        catalog.warning_double_space = tree.AppendItem(
            catalog.issues, _("double space"), data=(catalog, "issue-double-space")
        )

        catalog.workflow_new = tree.AppendItem(
            catalog.item, _("New"), data=(catalog, "new")
        )
        catalog.workflow_orphans = tree.AppendItem(
            catalog.item, _("Orphans"), data=(catalog, "orphan")
        )
        catalog.workflow_obsolete = tree.AppendItem(
            catalog.item, _("Obsolete"), data=(catalog, "obsolete")
        )
        catalog.workflow_fuzzy = tree.AppendItem(
            catalog.item, _("Fuzzy"), data=(catalog, "fuzzy")
        )
        catalog.workflow_untranslated = tree.AppendItem(
            catalog.item, _("Untranslated"), data=(catalog, "untranslated")
        )
        catalog.workflow_translated = tree.AppendItem(
            catalog.item, _("Translated"), data=(catalog, "translated")
        )
        catalog.workflow_all = tree.AppendItem(
            catalog.item, _("All"), data=(catalog, "all")
        )
        for message in catalog:
            msgid = str(message.id)
            name = msgid.strip()
            if name == HEADER:
                name = _("HEADER")
            message.item = tree.AppendItem(
                catalog.workflow_all, name, data=(catalog, message)
            )
            self.message_revalidate(catalog, message)
        for m in catalog.obsolete:
            message = catalog.obsolete[m]
            msgid = str(message.id)
            name = msgid.strip()
            if name == HEADER:
                continue
            message.item = tree.AppendItem(
                catalog.workflow_obsolete, name, data=(catalog, message)
            )
        for m in catalog.new:
            message = catalog.new[m]
            msgid = str(message.id)
            name = msgid.strip()
            if name == HEADER:
                continue
            message.item = tree.AppendItem(
                catalog.workflow_new, name, data=(catalog, message)
            )
            if message.item and message.item.IsOk():
                tree.SetItemTextColour(
                    message.item,
                    self.color_template_translated
                    if message.string
                    else self.color_template,
                )

    def _tree_rebuild(self):
        tree = self.tree
        tree.DeleteChildren(self.root)
        self._tree_build_template()
        for m in self.project.catalogs:
            if m == TEMPLATE:
                continue
            catalog = self.project.catalogs[m]
            self._tree_build_catalog(m, catalog)
        tree.ExpandAllChildren(self.root)
        self.depth_first_tree(self._tree_recolor, self.root)

    def _tree_recolor(self, item):
        catalog, info = self.tree.GetItemData(item)
        if not isinstance(info, str):
            if catalog.locale is None:
                c1 = self.color_template_translated
                c2 = self.color_template
            else:
                c1 = self.color_translated
                c2 = self.color_untranslated
            self.tree.SetItemTextColour(item, c1 if info.string else c2)

    def depth_first_tree(self, funct, item):
        (child, cookie) = self.tree.GetFirstChild(item)
        while child.IsOk():
            self.depth_first_tree(funct, child)
            funct(child)
            (child, cookie) = self.tree.GetNextChild(item, cookie)

    def tree_move_to_next(self):
        t = None
        for item in list(self.tree.GetSelections()):
            t = item
            break
        if t is None:
            return
        n = self.tree.GetNextSibling(t)
        catalog = self.project.catalogs[self.catalog]
        self.message_revalidate(
            catalog, self.panel_message_single.selected_message
        )
        if n.IsOk():
            self.tree.SelectItem(n)

    def tree_move_to_previous(self):
        t = None
        for item in list(self.tree.GetSelections()):
            t = item
            break
        if t is None:
            return
        n = self.tree.GetPrevSibling(t)
        catalog = self.project.catalogs[self.catalog]
        self.message_revalidate(
            catalog, self.panel_message_single.selected_message
        )
        if n.IsOk():
            self.tree.SelectItem(n)

    def message_revalidate(self, catalog, message):
        """
        Find the message's current classification and the message's qualified classifications and remove the message
        from those sections it does not qualify for anymore, and add it to those sections it has started to qualify for,
        those sections which are still qualified remain unchanged.

        This permits the tree to remove untranslated or error messages from those section as those are translated and
        the errors are corrected.

        :param message:
        :return:
        """
        tree = self.tree

        comment = message.auto_comments
        msgid = message.id
        msgstr = message.string
        items = message.items

        old_parents = []
        for item in items:
            old_parents.append(tree.GetItemParent(item))
        new_parents = self.message_classify(catalog, message)

        name = msgid.strip()
        if name == HEADER:
            name = _("HEADER")

        removing = []
        for i, itm in enumerate(old_parents):
            if itm not in new_parents:
                # removing contains actual items, not parents.
                removing.append(items[i])
        adding = []
        for itm in new_parents:
            if itm not in old_parents:
                # Adding contains parents to be added to.
                adding.append(itm)
        for item in removing:
            self.tree.Delete(item)
            items.remove(item)
        for item in adding:
            new_item = self.tree.AppendItem(item, name, data=(catalog, message))
            items.append(new_item)

    def message_classify(self, catalog, message):
        """
        Find all sections for which the current message qualifies.

        :param message: message to classify.
        :return:
        """
        classes = []
        comment = message.auto_comments
        msgid = message.id
        msgstr = message.string
        items = message.items
        if msgid == HEADER:
            return classes
        if message.fuzzy:
            classes.append(catalog.workflow_fuzzy)
        if not msgstr:
            classes.append(catalog.workflow_untranslated)
            return classes
        else:
            classes.append(catalog.workflow_translated)

        template = self.template
        if template is not None:
            if message.id not in template._messages:
                # Orphan
                catalog.orphans[message.id] = message
                classes.append(catalog.workflow_orphans)

        if msgid == msgstr:
            classes.append(catalog.warning_equal)
        if msgid[-1] != msgstr[-1]:
            if msgid[-1] in PUNCTUATION or msgstr[-1] in PUNCTUATION:
                classes.append(catalog.warning_end_punct)
            if msgid[-1] == " " or msgstr[-1] == " ":
                classes.append(catalog.warning_end_space)

        p0 = list(PRINTF_RE.findall(msgid))
        p1 = list(PRINTF_RE.findall(msgstr))
        if len(p0) == len(p1):
            for a, b in zip(p0, p1):
                if a != b:
                    classes.append(catalog.error_printf)
                    break
        else:
            classes.append(catalog.error_printf)

        if msgid[0].isupper() != msgstr[0].isupper():
            classes.append(catalog.warning_start_capital)
        if "  " in msgstr and "  " not in msgid:
            classes.append(catalog.warning_double_space)
        return classes

    def show_project_panel(self):
        self.panel_message_single.Hide()
        self.panel_statistics.Hide()
        self.panel_template.Hide()
        self.panel_catalog.Hide()
        self.panel_file_information.Hide()
        self.panel_template_file_information.Hide()
        self.panel_info.Hide()
        self.panel_project.Show()
        self.Layout()

    def show_info_panel(self):
        self.panel_message_single.Hide()
        self.panel_statistics.Hide()
        self.panel_template.Hide()
        self.panel_catalog.Hide()
        self.panel_file_information.Hide()
        self.panel_template_file_information.Hide()
        self.panel_info.Show()
        self.panel_project.Hide()
        self.Layout()

    def show_message_panel(self):
        self.panel_message_single.Show()
        self.panel_statistics.Hide()
        self.panel_template.Hide()
        self.panel_catalog.Hide()
        self.panel_file_information.Hide()
        self.panel_template_file_information.Hide()
        self.panel_info.Hide()
        self.panel_project.Hide()
        self.Layout()

    def show_catalog_panel(self):
        self.panel_message_single.Hide()
        self.panel_statistics.Show()
        self.panel_catalog.Show()
        self.panel_template.Hide()
        self.panel_file_information.Show()
        self.panel_template_file_information.Hide()
        self.panel_info.Hide()
        self.panel_project.Hide()
        self.Layout()

    def show_template_panel(self):
        self.panel_message_single.Hide()
        self.panel_statistics.Hide()
        self.panel_catalog.Hide()
        self.panel_template.Show()
        self.panel_file_information.Hide()
        self.panel_template_file_information.Show()
        self.panel_info.Hide()
        self.panel_project.Hide()
        self.Layout()

    def on_tree_selection(self, event):
        if self.do_not_update:
            return
        try:
            data = [
                self.tree.GetItemData(item)
                for item in self.tree.GetSelections()
                if self.tree.GetItemData(item) is not None
            ]
            print(data)
            if len(data) > 0:
                catalog, info = data[0]
                if catalog is not None:
                    for key, value in self.project.catalogs.items():
                        if catalog is value:
                            self.catalog = key
                self.panel_message_single.selected_catalog = catalog
                if isinstance(info, str):
                    if info == "root":
                        self.show_catalog_panel()
                        self.panel_catalog.catalog = catalog
                        self.panel_statistics.catalog = catalog
                        self.panel_file_information.catalog = catalog

                        self.panel_catalog.update_pane()
                        self.panel_statistics.update_pane()
                        self.panel_file_information.update_pane()
                    elif info == "template":
                        self.show_template_panel()
                        self.panel_template_file_information.catalog = catalog
                        self.panel_template.template = catalog

                        self.panel_template.update_pane()
                        self.panel_template_file_information.update_pane()
                    elif info == "project":
                        self.show_project_panel()
                        self.panel_project.project = self.project

                        self.panel_project.update_pane()
                    else:
                        self.show_info_panel()
                        self.panel_info.catalog = catalog
                        self.panel_info.info = info

                        self.panel_info.update_pane()
                else:
                    self.show_message_panel()
                    self.panel_message_single.update_pane(info)
        except RuntimeError:
            pass

    def on_tree_menu(self, event):
        item = event.GetItem()
        if item is None:
            return
        catalog, data = self.tree.GetItemData(item)
        if not isinstance(data, str):
            return
        menu = wx.Menu()
        context = menu
        if menu.MenuItemCount != 0:
            self.PopupMenu(menu)
            menu.Destroy()

    def translation_copy_original_to_translated(self):
        self.panel_message_single.text_translated_text.SetValue(
            self.panel_message_single.text_original_text.GetValue()
        )

    def force_new_line(self):
        text = self.panel_message_single.text_translated_text
        text.AppendText("\n")

    def force_fuzzy(self):
        fuzzy = self.panel_message_single.checkbox_fuzzy
        fuzzy.SetValue(True)
        self.panel_message_single.on_check_message_fuzzy()

    def force_unfuzzy(self):
        fuzzy = self.panel_message_single.checkbox_fuzzy
        fuzzy.SetValue(False)
        self.panel_message_single.on_check_message_fuzzy()


class SingleMessagePanel(wx.Panel):
    def __init__(self, *args, translation_panel=None, **kwds):
        # begin wxGlade: SingleMessagePanel.__init__
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)

        self.translation_panel = translation_panel

        sizer_comment = wx.BoxSizer(wx.VERTICAL)

        self.text_comment = wx.TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.text_comment.SetFont(
            wx.Font(
                14,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Segoe UI",
            )
        )
        sizer_comment.Add(self.text_comment, 3, wx.EXPAND, 0)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_comment.Add(sizer_3, 1, wx.EXPAND, 0)

        self.checkbox_fuzzy = wx.CheckBox(self, wx.ID_ANY, "Fuzzy")
        self.checkbox_fuzzy.SetFont(
            wx.Font(
                15,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Segoe UI",
            )
        )
        sizer_3.Add(self.checkbox_fuzzy, 0, 0, 0)

        self.text_original_text = wx.TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.text_original_text.SetFont(
            wx.Font(
                14,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Segoe UI",
            )
        )
        sizer_comment.Add(self.text_original_text, 6, wx.EXPAND, 0)

        self.text_translated_text = wx.TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER
        )
        self.text_translated_text.SetFont(
            wx.Font(
                14,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Segoe UI",
            )
        )
        sizer_comment.Add(self.text_translated_text, 6, wx.EXPAND, 0)

        self.SetSizer(sizer_comment)

        self.Layout()

        self.Bind(wx.EVT_CHECKBOX, self.on_check_message_fuzzy, self.checkbox_fuzzy)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.text_translated_text)
        self.Bind(wx.EVT_TEXT, self.on_text_translated, self.text_translated_text)
        self.text_translated_text.SetFocus()
        # end wxGlade
        self.selected_message = None
        self.selected_catalog = None

    def on_check_message_fuzzy(self, event=None):
        if self.selected_message is not None:
            self.selected_message.fuzzy = self.checkbox_fuzzy.GetValue()
            self.selected_message.modified = True
            self.translation_panel.message_revalidate(
                self.selected_catalog, self.selected_message
            )

    def update_pane(self, message):
        self.selected_message = None

        if message is not None:
            msgid = message.id
            if msgid is None:
                msgid = ""
            msgstr = message.string
            if msgstr is None:
                msgstr = ""
            comments = list(message.auto_comments)
            comments.extend(message.user_comments)
            print(message.locations)
            # comments.extend(message.locations)
            self.text_comment.SetValue("\n".join(comments))
            self.text_original_text.SetValue(str(msgid))
            self.text_translated_text.SetValue(str(msgstr))
            self.text_comment.Enable(True)
            self.text_original_text.Enable(True)
            self.text_translated_text.Enable(True)
            self.checkbox_fuzzy.SetValue(message.fuzzy)
        else:
            self.text_comment.SetValue("")
            self.text_original_text.SetValue("")
            self.text_translated_text.SetValue("")
            self.text_comment.Enable(False)
            self.text_original_text.Enable(False)
            self.text_translated_text.Enable(False)
        self.selected_message = message

    def on_text_translated(self, event):
        if self.selected_message:
            if not self.selected_message.pluralizable:
                self.selected_message.string = self.text_translated_text.GetValue()
                self.selected_message.modified = True
            else:
                self.selected_message.string[0] = self.text_translated_text.GetValue()
                self.selected_message.modified = True

    def on_text_enter(self, event):
        t = None
        for item in list(self.translation_panel.tree.GetSelections()):
            t = self.translation_panel.tree.GetNextSibling(item)
        if self.selected_message is not None and self.selected_catalog is not None:
            self.translation_panel.message_revalidate(
                self.selected_catalog, self.selected_message
            )
        if t is not None and t.IsOk():
            self.translation_panel.tree.SelectItem(t)
        self.text_translated_text.SetFocus()


class CatalogPanel(wx.Panel):
    def __init__(self, *args, translation_panel=None, **kwds):
        # begin wxGlade: CatalogPanel.__init__
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)
        self.translation_panel = translation_panel

        sizer_catalog = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Catalog"), wx.VERTICAL
        )

        sizer_7 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Project name and version"), wx.VERTICAL
        )
        sizer_catalog.Add(sizer_7, 0, wx.EXPAND, 0)

        self.text_catalog_project_name = wx.TextCtrl(self, wx.ID_ANY, "")
        sizer_7.Add(self.text_catalog_project_name, 0, wx.EXPAND, 0)

        sizer_6 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Language Team"), wx.VERTICAL
        )
        sizer_catalog.Add(sizer_6, 0, wx.EXPAND, 0)

        self.text_catalog_language_team = wx.TextCtrl(self, wx.ID_ANY, "")
        sizer_6.Add(self.text_catalog_language_team, 0, wx.EXPAND, 0)

        sizer_5 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Language"), wx.VERTICAL
        )
        sizer_catalog.Add(sizer_5, 0, wx.EXPAND, 0)

        self.combo_catalog_language = wx.ComboBox(
            self, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN
        )
        sizer_5.Add(self.combo_catalog_language, 0, wx.EXPAND, 0)

        sizer_8 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Plurals"), wx.VERTICAL
        )
        sizer_catalog.Add(sizer_8, 0, wx.EXPAND, 0)

        self.radio_button_rules_default = wx.RadioButton(
            self, wx.ID_ANY, "Default Language Rules", style=wx.RB_GROUP
        )
        self.radio_button_rules_default.SetValue(1)
        sizer_8.Add(self.radio_button_rules_default, 0, 0, 0)

        self.radio_button_rules_custom = wx.RadioButton(
            self, wx.ID_ANY, "Use custom rules"
        )
        sizer_8.Add(self.radio_button_rules_custom, 0, 0, 0)

        self.text_custom_rules = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_custom_rules.Enable(False)
        sizer_8.Add(self.text_custom_rules, 0, wx.EXPAND, 0)

        sizer_9 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Charset"), wx.VERTICAL
        )
        sizer_catalog.Add(sizer_9, 0, wx.EXPAND, 0)

        self.combo_catalog_charset = wx.ComboBox(
            self, wx.ID_ANY, choices=["UTF-8", ""], style=wx.CB_DROPDOWN
        )
        self.combo_catalog_charset.SetSelection(0)
        sizer_9.Add(self.combo_catalog_charset, 0, wx.EXPAND, 0)

        self.SetSizer(sizer_catalog)

        self.Layout()

        self.Bind(
            wx.EVT_TEXT,
            self.on_text_catalog_project_name,
            self.text_catalog_project_name,
        )
        self.Bind(
            wx.EVT_TEXT_ENTER,
            self.on_text_catalog_project_name,
            self.text_catalog_project_name,
        )
        self.Bind(
            wx.EVT_TEXT,
            self.on_text_catalog_project_team,
            self.text_catalog_language_team,
        )
        self.Bind(
            wx.EVT_TEXT_ENTER,
            self.on_text_catalog_project_name,
            self.text_catalog_language_team,
        )
        self.Bind(
            wx.EVT_COMBOBOX, self.on_combo_catalog_language, self.combo_catalog_language
        )
        self.Bind(
            wx.EVT_RADIOBUTTON,
            self.on_radio_catalog_plural,
            self.radio_button_rules_default,
        )
        self.Bind(
            wx.EVT_RADIOBUTTON,
            self.on_radio_catalog_plural,
            self.radio_button_rules_custom,
        )
        self.Bind(
            wx.EVT_TEXT, self.on_text_catalog_custom_rules, self.text_custom_rules
        )
        self.Bind(
            wx.EVT_TEXT_ENTER, self.on_text_catalog_custom_rules, self.text_custom_rules
        )
        self.Bind(
            wx.EVT_COMBOBOX, self.on_combo_catalog_charset, self.combo_catalog_charset
        )
        # end wxGlade
        self.catalog = None

    def on_text_catalog_project_name(
        self, event
    ):  # wxGlade: CatalogPanel.<event_handler>
        print("Event handler 'on_text_catalog_project_name' not implemented!")
        event.Skip()

    def on_text_catalog_project_team(
        self, event
    ):  # wxGlade: CatalogPanel.<event_handler>
        print("Event handler 'on_text_catalog_project_team' not implemented!")
        event.Skip()

    def on_combo_catalog_language(self, event):  # wxGlade: CatalogPanel.<event_handler>
        print("Event handler 'on_combo_catalog_language' not implemented!")
        event.Skip()

    def on_radio_catalog_plural(self, event):  # wxGlade: CatalogPanel.<event_handler>
        print("Event handler 'on_radio_catalog_plural' not implemented!")
        event.Skip()

    def on_text_catalog_custom_rules(
        self, event
    ):  # wxGlade: CatalogPanel.<event_handler>
        print("Event handler 'on_text_catalog_custom_rules' not implemented!")
        event.Skip()

    def on_combo_catalog_charset(self, event):  # wxGlade: CatalogPanel.<event_handler>
        print("Event handler 'on_combo_catalog_charset' not implemented!")
        event.Skip()

    def update_pane(self):
        self.text_catalog_project_name.SetLabelText(self.catalog.project)
        self.text_custom_rules.SetLabelText(str(self.catalog.plural_expr))
        self.text_catalog_language_team.SetLabelText(self.catalog.language_team)


class StatisticsPanel(wx.Panel):
    def __init__(self, *args, translation_panel=None, **kwds):
        # begin wxGlade: StatisticsPanel.__init__
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)
        self.translation_panel = translation_panel

        sizer_statistics = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Statistics"), wx.VERTICAL
        )

        sizer_messages_statistics = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Messages Translated"), wx.VERTICAL
        )
        sizer_statistics.Add(sizer_messages_statistics, 0, wx.EXPAND, 0)

        sizer_13 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_messages_statistics.Add(sizer_13, 1, wx.EXPAND, 0)

        self.text_messages_translated = wx.TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_READONLY
        )
        sizer_13.Add(self.text_messages_translated, 0, 0, 0)

        label_2 = wx.StaticText(self, wx.ID_ANY, "/")
        sizer_13.Add(label_2, 0, 0, 0)

        self.text_messages_total = wx.TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_READONLY
        )
        sizer_13.Add(self.text_messages_total, 0, 0, 0)

        self.gauge_messages = wx.Gauge(self, wx.ID_ANY, 10)
        sizer_messages_statistics.Add(self.gauge_messages, 0, wx.EXPAND, 0)

        sizer_fuzzy_statistics = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Fuzzy Translated"), wx.VERTICAL
        )
        sizer_statistics.Add(sizer_fuzzy_statistics, 0, wx.EXPAND, 0)

        sizer_20 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_fuzzy_statistics.Add(sizer_20, 1, wx.EXPAND, 0)

        self.text_fuzzy_translated = wx.TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_READONLY
        )
        sizer_20.Add(self.text_fuzzy_translated, 0, 0, 0)

        label_7 = wx.StaticText(self, wx.ID_ANY, "/")
        sizer_20.Add(label_7, 0, 0, 0)

        self.text_fuzzy_total = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        sizer_20.Add(self.text_fuzzy_total, 0, 0, 0)

        self.gauge_fuzzy = wx.Gauge(self, wx.ID_ANY, 10)
        sizer_fuzzy_statistics.Add(self.gauge_fuzzy, 0, wx.EXPAND, 0)

        sizer_words_statistics = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Words Translated"), wx.VERTICAL
        )
        sizer_statistics.Add(sizer_words_statistics, 0, wx.EXPAND, 0)

        sizer_12 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_words_statistics.Add(sizer_12, 1, wx.EXPAND, 0)

        self.text_words_translated = wx.TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_READONLY
        )
        sizer_12.Add(self.text_words_translated, 0, 0, 0)

        label_1 = wx.StaticText(self, wx.ID_ANY, "/")
        sizer_12.Add(label_1, 0, 0, 0)

        self.text_words_total = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        sizer_12.Add(self.text_words_total, 0, 0, 0)

        self.gauge_words = wx.Gauge(self, wx.ID_ANY, 10)
        sizer_words_statistics.Add(self.gauge_words, 0, wx.EXPAND, 0)

        self.SetSizer(sizer_statistics)

        self.Layout()
        # end wxGlade
        self.catalog = None

    def update_pane(self):

        total = len(self.catalog._messages)
        self.text_messages_total.SetLabelText(str(total))
        translated = [
            m
            for m in self.catalog._messages.values()
            if m.string != "" and m.string is not None
        ]
        trans = len(translated)
        self.text_messages_translated.SetLabelText(str(trans))
        self.gauge_messages.SetRange(total)
        self.gauge_messages.SetValue(trans)

        total_words = 0
        trans_words = 0
        for message in self.catalog._messages.values():
            words = len(message.id.split(" "))
            total_words += words
            if message.string is not None and message.string != "":
                trans_words += words
        self.text_words_total.SetLabelText(str(total_words))
        self.text_words_translated.SetLabelText(str(trans_words))
        self.gauge_words.SetRange(total_words)
        self.gauge_words.SetValue(trans_words)

        total = len(self.catalog._messages)
        self.text_fuzzy_total.SetLabelText(str(total))
        fuzzy = [m for m in self.catalog._messages.values() if m.fuzzy]
        fuzz = len(fuzzy)
        self.text_fuzzy_translated.SetLabelText(str(fuzz))
        self.gauge_fuzzy.SetRange(total)
        self.gauge_fuzzy.SetValue(fuzz)


class FileInformationPanel(wx.Panel):
    def __init__(self, *args, translation_panel=None, **kwds):
        # begin wxGlade: FileInformationPanel.__init__
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)
        self.translation_panel = translation_panel

        sizer_file_info = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "File Information"), wx.VERTICAL
        )

        sizer_14 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "File Type:"), wx.VERTICAL
        )
        sizer_file_info.Add(sizer_14, 0, wx.EXPAND, 0)

        self.text_file_type = wx.TextCtrl(
            self, wx.ID_ANY, "Gettext Portable Object File", style=wx.TE_READONLY
        )
        sizer_14.Add(self.text_file_type, 0, wx.EXPAND, 0)

        sizer_15 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "File Size:"), wx.VERTICAL
        )
        sizer_file_info.Add(sizer_15, 0, wx.EXPAND, 0)

        self.text_file_size = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        sizer_15.Add(self.text_file_size, 0, wx.EXPAND, 0)

        sizer_16 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Location:"), wx.VERTICAL
        )
        sizer_file_info.Add(sizer_16, 0, wx.EXPAND, 0)

        self.text_file_location = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        sizer_16.Add(self.text_file_location, 0, wx.EXPAND, 0)

        self.SetSizer(sizer_file_info)

        self.Layout()
        # end wxGlade
        self.catalog = None

    def update_pane(self):
        filename = self.catalog.filename
        self.text_file_location.SetLabelText(str(filename))
        filesize = 0
        if filename is not None:
            if os.path.exists(filename):
                filesize = os.path.getsize(filename)
        self.text_file_size.SetLabelText(str(filesize))
        if filename is None or filename.endswith(".pot"):
            self.text_file_type.SetLabelText("Gettext Portable Object Template")
        else:
            self.text_file_type.SetLabelText("Gettext Portable Object File")


class TemplatePanel(wx.Panel):
    def __init__(self, *args, translation_panel=None, **kwds):
        # begin wxGlade: TemplatePanel.__init__
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)
        self.translation_panel = translation_panel

        sizer_11 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Template"), wx.VERTICAL
        )

        sizer_17 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Project Name"), wx.VERTICAL
        )
        sizer_11.Add(sizer_17, 0, wx.EXPAND, 0)

        self.text_template_project_name = wx.TextCtrl(self, wx.ID_ANY, "")
        sizer_17.Add(self.text_template_project_name, 0, wx.EXPAND, 0)

        sizer_18 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Default Team"), wx.VERTICAL
        )
        sizer_11.Add(sizer_18, 0, wx.EXPAND, 0)

        self.text_project_language_team = wx.TextCtrl(self, wx.ID_ANY, "")
        sizer_18.Add(self.text_project_language_team, 0, wx.EXPAND, 0)

        sizer_21 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Charset"), wx.VERTICAL
        )
        sizer_11.Add(sizer_21, 0, wx.EXPAND, 0)

        self.combo_template_charset = wx.ComboBox(
            self, wx.ID_ANY, choices=["UTF-8", ""], style=wx.CB_DROPDOWN
        )
        self.combo_template_charset.SetSelection(0)
        sizer_21.Add(self.combo_template_charset, 0, wx.EXPAND, 0)

        self.SetSizer(sizer_11)

        self.Layout()

        self.Bind(
            wx.EVT_TEXT, self.on_text_template_name, self.text_template_project_name
        )
        self.Bind(
            wx.EVT_TEXT_ENTER,
            self.on_text_template_name,
            self.text_template_project_name,
        )
        self.Bind(
            wx.EVT_TEXT, self.on_text_template_team, self.text_project_language_team
        )
        self.Bind(
            wx.EVT_TEXT_ENTER,
            self.on_text_template_team,
            self.text_project_language_team,
        )
        self.Bind(
            wx.EVT_COMBOBOX, self.on_combo_template_charset, self.combo_template_charset
        )
        # end wxGlade
        self.template = None

    def on_text_template_name(self, event):  # wxGlade: TemplatePanel.<event_handler>
        print("Event handler 'on_text_template_name' not implemented!")
        event.Skip()

    def on_text_template_team(self, event):  # wxGlade: TemplatePanel.<event_handler>
        print("Event handler 'on_text_template_team' not implemented!")
        event.Skip()

    def on_combo_template_charset(
        self, event
    ):  # wxGlade: TemplatePanel.<event_handler>
        print("Event handler 'on_combo_template_charset' not implemented!")
        event.Skip()

    def update_pane(self):
        pass


class ProjectPanel(wx.Panel):
    def __init__(self, *args, translation_panel=None, **kwds):
        # begin wxGlade: ProjectPanel.__init__
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)
        self.translation_panel = translation_panel

        sizer_22 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Project"), wx.VERTICAL
        )

        sizer_24 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Project Directory:"), wx.HORIZONTAL
        )
        sizer_22.Add(sizer_24, 0, wx.EXPAND, 0)

        self.text_project_directory = wx.TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_READONLY
        )
        sizer_24.Add(self.text_project_directory, 1, wx.EXPAND, 0)

        self.button_open_project_directory = wx.Button(self, wx.ID_ANY, "Open")
        sizer_24.Add(self.button_open_project_directory, 0, 0, 0)

        sizer_23 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Project Name:"), wx.VERTICAL
        )
        sizer_22.Add(sizer_23, 0, wx.EXPAND, 0)

        self.text_project_name = wx.TextCtrl(self, wx.ID_ANY, "")
        sizer_23.Add(self.text_project_name, 0, wx.EXPAND, 0)

        sizer_25 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Charset:"), wx.VERTICAL
        )
        sizer_22.Add(sizer_25, 0, wx.EXPAND, 0)

        self.combo_project_charset = wx.ComboBox(
            self, wx.ID_ANY, choices=["UTF-8", ""], style=wx.CB_DROPDOWN
        )
        self.combo_project_charset.SetSelection(0)
        sizer_25.Add(self.combo_project_charset, 0, wx.EXPAND, 0)

        sizer_27 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Default Template Location:"), wx.VERTICAL
        )
        sizer_22.Add(sizer_27, 0, wx.EXPAND, 0)

        self.text_project_pot_file = wx.TextCtrl(self, wx.ID_ANY, "")
        sizer_27.Add(self.text_project_pot_file, 0, wx.EXPAND, 0)

        sizer_19 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Default Structure:"), wx.VERTICAL
        )
        sizer_22.Add(sizer_19, 1, wx.EXPAND, 0)

        self.text_template_structure = wx.TextCtrl(self, wx.ID_ANY, "")
        sizer_19.Add(self.text_template_structure, 0, wx.EXPAND, 0)

        label_3 = wx.StaticText(self, wx.ID_ANY, "* <lang>: language")
        sizer_19.Add(label_3, 0, 0, 0)

        label_4 = wx.StaticText(self, wx.ID_ANY, "* <project>: project name")
        sizer_19.Add(label_4, 0, 0, 0)

        label_5 = wx.StaticText(self, wx.ID_ANY, "* <locale>: locale")
        sizer_19.Add(label_5, 0, 0, 0)

        label_6 = wx.StaticText(self, wx.ID_ANY, "* <team>: team")
        sizer_19.Add(label_6, 0, 0, 0)

        self.SetSizer(sizer_22)

        self.Layout()

        self.Bind(
            wx.EVT_BUTTON,
            self.on_project_open_directory,
            self.button_open_project_directory,
        )
        self.Bind(wx.EVT_TEXT, self.on_text_template_name, self.text_project_name)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_template_name, self.text_project_name)

        self.Bind(
            wx.EVT_COMBOBOX, self.on_combo_project_charset, self.combo_project_charset
        )

        self.Bind(wx.EVT_TEXT, self.on_text_template_file, self.text_project_pot_file)
        self.Bind(
            wx.EVT_TEXT_ENTER,
            self.on_text_template_file,
            self.text_project_pot_file,
        )

        self.Bind(
            wx.EVT_TEXT, self.on_text_template_structure, self.text_template_structure
        )
        self.Bind(
            wx.EVT_TEXT_ENTER,
            self.on_text_template_structure,
            self.text_template_structure,
        )
        # end wxGlade
        self.text_project_name.SetValue(self.translation_panel.project.name)
        self.combo_project_charset.SetSelection(self.translation_panel.project.charset)
        self.text_project_pot_file.SetValue(
            self.translation_panel.project.template_file
        )
        self.text_template_structure.SetValue(
            self.translation_panel.project.catalog_file
        )

    def on_project_open_directory(self, event):  # wxGlade: ProjectPanel.<event_handler>
        self.translation_panel.open_project_directory()

    def on_text_template_name(self, event):  # wxGlade: ProjectPanel.<event_handler>
        self.translation_panel.project.name = self.text_project_name.GetValue()

    def on_combo_project_charset(self, event):  # wxGlade: ProjectPanel.<event_handler>
        self.translation_panel.project.charset = self.combo_project_charset.GetValue()

    def on_text_template_file(self, event):  # wxGlade: ProjectPanel.<event_handler>
        self.translation_panel.project.template_file = (
            self.text_project_pot_file.GetValue()
        )

    def on_text_template_structure(
        self, event
    ):  # wxGlade: ProjectPanel.<event_handler>
        self.translation_panel.project.catalog_file = (
            self.text_template_structure.GetValue()
        )

    def update_pane(self):
        directory = self.translation_panel.project.directory
        if directory is None:
            directory = ""
        self.text_project_directory.SetValue(directory)

        tem_file = self.translation_panel.project.template_file
        self.text_project_pot_file.SetValue(tem_file)

        cat_file = self.translation_panel.project.catalog_file
        self.text_template_structure.SetValue(cat_file)

        name = self.translation_panel.project.name
        self.text_project_name.SetValue(self.translation_panel.project.name)

        self.combo_project_charset.SetSelection(self.translation_panel.project.charset)


class InfoPanel(wx.Panel):
    def __init__(self, *args, translation_panel=None, **kwds):
        # begin wxGlade: InfoPanel.__init__
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)
        self.translation_panel = translation_panel

        sizer_main = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Info"), wx.VERTICAL
        )

        self.text_information_description = wx.TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.text_information_description.SetFont(
            wx.Font(
                14,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Segoe UI",
            )
        )

        sizer_main.Add(self.text_information_description, 1, wx.EXPAND, 0)

        self.sizer_operations = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Operations"), wx.VERTICAL
        )
        sizer_main.Add(self.sizer_operations, 1, wx.EXPAND, 0)

        self.SetSizer(sizer_main)

        self.Layout()
        # end wxGlade
        self.info = None
        self.catalog = None

    def update_pane(self):
        def as_event(funct):
            def specific(event=None):
                funct(self.translation_panel.tree, self.catalog, self.translation_panel)

            return specific

        if self.info is not None:
            data = INTERFACE.get(self.info)
            desc = data["description"]
            self.text_information_description.SetValue(desc)

            self.sizer_operations.Clear(True)
            for cmd in data["commands"]:
                button = wx.Button(self, wx.ID_ANY, cmd["name"])
                self.Bind(wx.EVT_BUTTON, as_event(cmd["command"]), button)
                self.sizer_operations.Add(button, 0, 0, 0)
            self.Layout()
        self.Update()
        self.Refresh()


class PoboyWindow(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((1200, 800))
        self.language = None
        self.locale = None

        self.panel = TranslationPanel(self, wx.ID_ANY)

        self.main_menubar = wx.MenuBar()
        self.panel.build_menu(self.main_menubar)
        self.add_language_menu()
        self.SetMenuBar(self.main_menubar)

        _icon = wx.NullIcon
        _icon.CopyFromBitmap(icons8_translation_50.GetBitmap())
        self.SetIcon(_icon)
        self.SetTitle(_("POboy"))
        self.Layout()
        # end wxGlade

    def add_language_menu(self):
        tl = wx.FileTranslationsLoader()
        trans = tl.GetAvailableTranslations("poboy")

        wxglade_tmp_menu = wx.Menu()
        i = 0
        for lang in supported_languages:
            language_code, language_name, language_index = lang
            m = wxglade_tmp_menu.Append(wx.ID_ANY, language_name, "", wx.ITEM_RADIO)
            if i == self.language:
                m.Check(True)

            def language_update(q):
                return lambda e: self.load_language(q)

            self.Bind(wx.EVT_MENU, language_update(i), id=m.GetId())
            if language_code not in trans and i != 0:
                m.Enable(False)
            i += 1
        self.main_menubar.Append(wxglade_tmp_menu, _("Languages"))

    def load_language(self, lang):
        try:
            language_code, language_name, language_index = supported_languages[lang]
        except (IndexError, ValueError):
            return
        self.language = lang

        if self.locale:
            assert sys.getrefcount(self.locale) <= 2
            del self.locale
        self.locale = wx.Locale(language_index)
        # wxWidgets is broken. IsOk()==false and pops up error dialog, but it translates fine!
        if self.locale.IsOk() or "linux" in sys.platform:
            self.locale.AddCatalog("poboy")
        else:
            self.locale = None


class PoboyApp(wx.App):
    def OnInit(self):
        self.load_catalogs()

        self.frame = PoboyWindow(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

    def load_catalogs(self):
        try:  # pyinstaller internal location
            _resource_path = os.path.join(sys._MEIPASS, "locale")
            wx.Locale.AddCatalogLookupPathPrefix(_resource_path)
        except Exception:
            pass

        try:  # Mac py2app resource
            _resource_path = os.path.join(os.environ["RESOURCEPATH"], "locale")
            wx.Locale.AddCatalogLookupPathPrefix(_resource_path)
        except Exception:
            pass

        wx.Locale.AddCatalogLookupPathPrefix("locale")

        # Default Locale, prepended. Check this first.
        basepath = os.path.abspath(os.path.dirname(sys.argv[0]))
        localedir = os.path.join(basepath, "locale")
        wx.Locale.AddCatalogLookupPathPrefix(localedir)
