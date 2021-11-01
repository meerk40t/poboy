import os
import sys
import glob

import re
import wx

_ = wx.GetTranslation

from wx.lib.embeddedimage import PyEmbeddedImage

PUNCTUATION = (".", "?", "!", ":", ";")


icons8_translation_50 = PyEmbeddedImage(
    b'iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAABmJLR0QA/wD/AP+gvaeTAAAD'
    b'oklEQVRogd2ay0sVURzHP+bNWrgpuPdKLYKeG20jImQRBZdoERTSwmiT1CK0FkGt7WlRQi2K'
    b'3Bb9ARIu06VEi8RKe1EE3gjKIGtRRt4W8xtnmjsz5zEzV/MLB+ae8zvf7/nOnDmvubDM0ABc'
    b'Az4ClRqlMtAv2jpoAnpUQVdraCCYrmiamJL43rjAsgTt0CBNCx14TyYOfhNT8jsS7t2pNVS6'
    b'ReC5xLwE1iUlzApxusYmVIRZIkq3AEyi2Z0AVqTbrsVHkieSVd0CXtd6RQ26VpZ1jc3EEaY1'
    b'X9gYMTazlI2AwYSY5qi1EvgufEVFrImu1hJFl3A70IrT2Ci4M/a0Bl/qw74u4TOJa42JGZKY'
    b'GynqakOX8LbE3Y8o3yflP4H1KepqQ5dwK/BLYk8EyjYCX6SsL2VdbZgQnpLYeeA8kAM2AG8k'
    b'fxSo1+Ap+nRtUuh+xvTOnBUjFeAJ8EGunwJrNTnywERCMxUC+xmbR7wf+Oar+wc4DNQp6hWA'
    b'ks+MaoiOQuh+xtRIHnjgq/fbdz0JnCF8QdoIvMB5z0oh5aaoareukRxwEvgs8T+A0zjd6Rxe'
    b'F3sdw9GHY6Zg2uoQGBupB7rw9ggVYATYFIjLAQeAo4H8PDCA92I22rQ6BMZG2n0xb4FOQ8FH'
    b'UnfAsJ4KVl3rHnCM+OVJFFpwzOQD+TlgjaScBa/1O2KCAk7jW2Jien3aygVhCGpi5DreuxSF'
    b'cbz5aNxCI1Mj7oucwzETNU+0ieYQ8F6u2wy1MjPiztY6K99B0ewELsn1XUO9zIyUcCa7CeKH'
    b'2EZgFvgKrAK2if6sol4QVe12j0w7DEj8KOKNSCWqR6cgukVv0Jf3WPK6DXSrjPT7Mm3ThIYB'
    b'F2NSZ5cvzx3BxpIYaRAzZZKZ0VkANkvsO/5dYOaBOSlrtjWSFCaEtyT2QkjZQym7mYFuqoSr'
    b'gRmJbceb1d10XMpmJDYtXW3oEh5Bv5t2meiqNkG6cE2o+EaAPTjb4tmImCacg4tRYG9S3R40'
    b'jvIDhKonshlnOTJH/Oi2W7jmpY61rjsMan2X0CEUuEP8kCKuDm/J0p9E1+Y4X2Ukh/fFWGcv'
    b'c1FiPxG/bVDeQFMzKsJDUu4uSVTYgrcqPphAFzAzoyIclvI7KlEf3Nl/OIHuAvzH+ZNEHxik'
    b'Pp5rYkF32X1DDIPJ5+FFfyJRMP3GvSSNGP1lQpB0P2ODnaIZ+UHJZkJMYz9jmy7HNcx0iZLW'
    b'fsYkTYsJ3b9J/R/4C673TQnRnTmBAAAAAElFTkSuQmCC')


def plugin(kernel, lifecycle):
    if getattr(sys, "frozen", False):
        # This plugin is source only.
        return
    if lifecycle == "register":
        context = kernel.root
        _ = kernel.translation

        @context.console_command(
            "locale", output_type="locale", hidden=True
        )
        def locale(channel, _, **kwargs):
            return "locale", "en"

        @context.console_command(
            "generate", input_type="locale", output_type="locale", hidden=True
        )
        def generate_locale(channel, _, data=None, **kwargs):

            return "locale", data

        @context.console_argument("locale", help="locale use for these opeations")
        @context.console_command(
            "change", input_type="locale", output_type="locale", hidden=True
        )
        def change_locale(channel, _, data=None, locale=None, **kwargs):
            if locale is None:
                raise SyntaxError
            channel("locale changed from %s to %s" % (data, locale))
            return "locale", locale

        @context.console_command(
            "update", input_type="locale", hidden=True
        )
        def update_locale(channel, _, data=None, **kwargs):
            """
            This script updates the message.po structure with the original translation information.

            @param channel:
            @param _:
            @param data:
            @param kwargs:
            @return:
            """
            if data == "en":
                channel("Cannot update English since it is the default language and has no file")
            keys = dict()
            translations = open("./locale/%s/LC_MESSAGES/meerk40t.po" % data, "r", encoding="utf-8")

            file_lines = translations.readlines()
            key = None
            index = 0
            translation_header = []
            while index < len(file_lines):
                # Header is defined as the first batch of uninterrupted lines in the file.
                try:
                    if file_lines[index]:
                        translation_header.append(file_lines[index])
                    else:
                        break
                    index += 1
                except IndexError:
                    break

            while index < len(file_lines):
                try:
                    # Find msgid and all multi-lined message ids
                    if re.match("msgid \"(.*)\"", file_lines[index]):
                        m = re.match("msgid \"(.*)\"", file_lines[index])
                        key = m.group(1)
                        index += 1
                        if index >= len(file_lines):
                            break
                        while re.match("^\"(.*)\"$", file_lines[index]):
                            m = re.match("^\"(.*)\"$", file_lines[index])
                            key += m.group(1)
                            index += 1

                    # find all message strings and all multi-line message strings
                    if re.match("msgstr \"(.*)\"", file_lines[index]):
                        m = re.match("msgstr \"(.*)\"", file_lines[index])
                        value = [file_lines[index]]
                        if len(key) > 0:
                            keys[key] = value
                        index += 1
                        while re.match("^\"(.*)\"$", file_lines[index]):
                            value.append(file_lines[index])
                            if len(key) > 0:
                                keys[key] = value
                            index += 1
                    index += 1
                except IndexError:
                    break

            template = open("./locale/messages.po", "r", encoding="utf-8")
            lines = []

            file_lines = list(template.readlines())
            index = 0
            template_header = []
            while index < len(file_lines):
                # Header is defined as the first batch of uninterrupted lines in the file.
                # We read the template header but do not use them.
                try:
                    if file_lines[index]:
                        template_header.append(file_lines[index])
                    else:
                        break
                    index += 1
                except IndexError:
                    break

            # Lines begins with the translation's header information.
            lines.extend(translation_header)
            while index < len(file_lines):
                try:
                    # Attempt to locate message id
                    if re.match("msgid \"(.*)\"", file_lines[index]):
                        lines.append(file_lines[index])
                        m = re.match("msgid \"(.*)\"", file_lines[index])
                        key = m.group(1)
                        index += 1
                        while re.match("^\"(.*)\"$", file_lines[index]):
                            lines.append(file_lines[index])
                            key += m.group(1)
                            index += 1
                except IndexError:
                    pass
                try:
                    # Attempt to locate message string
                    if re.match("msgstr \"(.*)\"", file_lines[index]):
                        if key in keys:
                            lines.extend(keys[key])
                            index += 1
                            while re.match("^\"(.*)\"$", file_lines[index]):
                                index += 1
                        else:
                            lines.append(file_lines[index])
                            index += 1
                            while re.match("^\"(.*)\"$", file_lines[index]):
                                lines.append(file_lines[index])
                                index += 1
                except IndexError:
                    pass
                try:
                    # We append any line if it wasn't fully read by msgid and msgstr readers.
                    lines.append(file_lines[index])
                    index += 1
                except IndexError:
                    break

            filename = "meerk40t.update"
            channel("writing %s" % filename)
            import codecs
            template = codecs.open(filename, "w", "utf8")
            template.writelines(lines)
        try:
            kernel.register("window/Translate", PoboyFrame)
        except NameError:
            pass


class TranslationPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.translations = None
        self.template = None
        self.language = None

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        self.tree = wx.TreeCtrl(self, wx.ID_ANY, style=wx.TR_HAS_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT | wx.TR_HIDE_ROOT | wx.TR_NO_LINES | wx.TR_SINGLE | wx.TR_TWIST_BUTTONS)
        sizer_1.Add(self.tree, 1, wx.EXPAND, 0)

        self.root = self.tree.AddRoot(_("Translation"))

        self.workflow = self.tree.AppendItem(self.root, _("Workflow"))
        self.errors = self.tree.AppendItem(self.root, _("Errors"))
        self.issues = self.tree.AppendItem(self.root, _("Issues"))

        self.tree.SetItemTextColour(self.errors, wx.RED)
        self.error_printf = self.tree.AppendItem(self.errors, _("printf-tokens"))

        self.tree.SetItemTextColour(self.issues, wx.Colour(127, 127, 0))
        self.warning_equal = self.tree.AppendItem(self.issues, _("msgid==msgstr"))
        self.warning_start_capital = self.tree.AppendItem(self.issues, _("capitalization"))
        self.warning_end_punct = self.tree.AppendItem(self.issues, _("ending punctuation"))
        self.warning_end_space = self.tree.AppendItem(self.issues, _("ending whitespace"))
        self.warning_double_space = self.tree.AppendItem(self.issues, _("double space"))

        self.all = self.tree.AppendItem(self.workflow, _("All Translations"))
        self.workflow_untranslated = self.tree.AppendItem(self.workflow, _("Untranslated"))
        self.workflow_translated = self.tree.AppendItem(self.workflow, _("Translated"))

        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_selection)
        self.tree.ExpandAll()

        self.panel_entry = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_entry, 3, wx.EXPAND, 0)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        self.text_comment = wx.TextCtrl(self.panel_entry, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.text_comment.SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_2.Add(self.text_comment, 3, wx.EXPAND, 0)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.Add(sizer_3, 1, wx.EXPAND, 0)

        self.checkbox_1 = wx.CheckBox(self.panel_entry, wx.ID_ANY, _("Fuzzy"))
        self.checkbox_1.SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_3.Add(self.checkbox_1, 0, 0, 0)

        self.text_original_text = wx.TextCtrl(self.panel_entry, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.text_original_text.SetFont(
            wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_2.Add(self.text_original_text, 6, wx.EXPAND, 0)

        self.text_translated_text = wx.TextCtrl(self.panel_entry, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
        self.text_translated_text.SetFont(
            wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_2.Add(self.text_translated_text, 6, wx.EXPAND, 0)

        self.panel_entry.SetSizer(sizer_2)

        self.SetSizer(sizer_1)

        self.Layout()

        self.Bind(wx.EVT_TEXT, self.on_text_translated, self.text_translated_text)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.text_translated_text)
        self.text_translated_text.SetFocus()
        self.text_original_text.SetCanFocus(False)
        self.text_comment.SetCanFocus(False)
        # end wxGlade
        self.entries = []
        self.entry = None

    def load_translation(self, translation_file):
        self.translations = open(translation_file, "r", encoding="utf-8")
        translations = self.translations
        self.clear()

        file_lines = translations.readlines()
        index = 0
        while index < len(file_lines):
            comment = ""
            msgid = ""
            msgstr = ""
            try:
                # Find comments and all multiline comments
                if re.match("^#(.*)$", file_lines[index]):
                    m = re.match("^#(.*)$", file_lines[index])
                    comment = m.group(1)
                    index += 1
                    if index >= len(file_lines):
                        break
                    while re.match("^#(.*)$", file_lines[index]):
                        m = re.match("^#(.*)$", file_lines[index])
                        comment += m.group(1)
                        index += 1

                # find msgid and all multiline message ids
                if re.match("msgid \"(.*)\"", file_lines[index]):
                    m = re.match("msgid \"(.*)\"", file_lines[index])
                    msgid = m.group(1)
                    index += 1
                    if index >= len(file_lines):
                        break
                    while re.match("^\"(.*)\"$", file_lines[index]):
                        m = re.match("^\"(.*)\"$", file_lines[index])
                        msgid += m.group(1)
                        index += 1

                # find all message strings and all multi-line message strings
                if re.match("msgstr \"(.*)\"", file_lines[index]):
                    m = re.match("msgstr \"(.*)\"", file_lines[index])
                    msgstr = m.group(1)
                    index += 1
                    while re.match("^\"(.*)\"$", file_lines[index]):
                        m = re.match("^\"(.*)\"$", file_lines[index])
                        msgstr += m.group(1)
                        index += 1
            except IndexError:
                break
            if len(comment) or len(msgid) or len(msgstr):
                msgid = msgid.replace("\\n", "\n")
                msgstr = msgstr.replace("\\n", "\n")
                self.entries.append([comment, msgid, msgstr, list()])
            index += 1
        self.update()
        self.tree.ExpandAll()

    def clear(self):
        self.entries.clear()
        self.update()

    def save_translation(self, translation_file):
        with open(translation_file, "w", encoding="utf-8") as save:
            for entry in self.entries:
                comment = entry[0]
                msgid = entry[1]
                msgstr = entry[2]
                items = entry[3]
                save.write(comment)
                save.write(msgid)
                save.write(msgstr)

    def clear_tree(self):
        self.tree.DeleteChildren(self.all)
        self.tree.DeleteChildren(self.error_printf)
        self.tree.DeleteChildren(self.warning_equal)
        self.tree.DeleteChildren(self.warning_end_space)
        self.tree.DeleteChildren(self.warning_end_punct)
        self.tree.DeleteChildren(self.warning_double_space)
        self.tree.DeleteChildren(self.warning_start_capital)
        self.tree.DeleteChildren(self.workflow_translated)
        self.tree.DeleteChildren(self.workflow_untranslated)

    def update(self):
        self.clear_tree()
        for entry in self.entries:
            msgid = entry[1]
            name = msgid.strip()
            if name == "":
                name = _("HEADER")
            self.tree.AppendItem(self.all, name, data=entry)
            self.process_validate_entry(entry)

    def add_entry(self, comment="", msgid="", msgstr=""):
        self.entries.append([comment, msgid, msgstr, []])

    def update_translation_values(self):
        if self.entry is not None:
            self.text_comment.SetValue(self.entry[0])
            self.text_original_text.SetValue(self.entry[1])
            self.text_translated_text.SetValue(self.entry[2])

    def on_tree_selection(self, event):
        try:
            data = [
                self.tree.GetItemData(item) for item in self.tree.GetSelections()
            ]
            if len(data) > 0:
                self.entry = data[0]
                self.update_translation_values()
        except RuntimeError:
            pass

    def source(self):
        self.text_translated_text.SetValue(self.text_original_text.GetValue())

    def next(self):
        t = None
        for item in list(self.tree.GetSelections()):
            t = item
            break
        n = self.tree.GetNextSibling(t)
        self.process_validate_entry(self.entry)
        if n.IsOk():
            self.tree.SelectItem(n)

    def previous(self):
        t = None
        for item in list(self.tree.GetSelections()):
            t = item
            break
        n = self.tree.GetPrevSibling(t)
        self.process_validate_entry(self.entry)
        if n.IsOk():
            self.tree.SelectItem(n)

    def process_validate_entry(self, entry):
        comment = entry[0]
        msgid = entry[1]
        msgstr = entry[2]
        items = entry[3]

        old_parents = []
        for item in items:
            old_parents.append(self.tree.GetItemParent(item))
        new_parents = self.find_classifications(entry)

        name = msgid.strip()
        if name == "":
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
            items.append(self.tree.AppendItem(item, name, data=entry))

    def find_classifications(self, entry):
        classes = []
        comment = entry[0]
        msgid = entry[1]
        msgstr = entry[2]
        if msgid == "":
            return classes
        if not msgstr:
            classes.append(self.workflow_untranslated)
            return classes
        else:
            classes.append(self.workflow_translated)

        if msgid == msgstr:
            classes.append(self.warning_equal)
        if msgid[-1] != msgstr[-1]:
            if msgid[-1] in PUNCTUATION or msgstr[-1] in PUNCTUATION:
                classes.append(self.warning_end_punct)
            if msgid[-1] == " " or msgstr[-1] == " ":
                classes.append(self.warning_end_space)
        if ("%f" in msgid) != ("%f" in msgstr):
            classes.append(self.error_printf)
        elif ("%s" in msgid) != ("%s" in msgstr):
            classes.append(self.error_printf)
        elif ("%d" in msgid) != ("%d" in msgstr):
            classes.append(self.error_printf)
        if msgid[0].isupper() != msgstr[0].isupper():
            classes.append(self.warning_start_capital)
        if "  " in msgstr and "  " not in msgid:
            classes.append(self.warning_double_space)
        return classes

    def on_text_translated(self, event):  # wxGlade: TranslationPanel.<event_handler>
        if self.entry:
            self.entry[2] = self.text_translated_text.GetValue()

    def on_text_enter(self, event):
        t = None
        for item in list(self.tree.GetSelections()):
            t = self.tree.GetNextSibling(item)
        if self.entry is not None:
            self.process_validate_entry(self.entry)
        if t is not None and t.IsOk():
            self.tree.SelectItem(t)
        self.text_translated_text.SetFocus()


class PoboyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((1200, 800))

        self.panel = TranslationPanel(self, wx.ID_ANY)

        # Menu Bar
        self.frame_menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()

        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("New\tCtrl+N"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_new, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Open Translation\tCtrl+O"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_open, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Open Template\tCtrl+Shift+O"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_template, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Open Sources\tAlt+O"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_sources, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Save Translation\tCtrl+S"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_save, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Save Template\tCtrl+S"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_save, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Save as"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_saveas, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Export"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_export, item)
        self.frame_menubar.Append(wxglade_tmp_menu, _("File"))
        wxglade_tmp_menu = wx.Menu()
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Previous Entry\tCtrl+Up"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_previous, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Next Entry\tCtrl+Down"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_next, item)
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Copy Source\tAlt+Down"), "")
        self.Bind(wx.EVT_MENU, self.on_menu_source, item)
        self.frame_menubar.Append(wxglade_tmp_menu, _("Navigate"))
        self.SetMenuBar(self.frame_menubar)
        # Menu Bar end

        _icon = wx.NullIcon
        _icon.CopyFromBitmap(icons8_translation_50.GetBitmap())
        self.SetIcon(_icon)
        self.SetTitle(_("POboy"))

    def on_menu_new(self, event):
        self.panel.clear()

    def on_menu_open(self, event):  # wxGlade: MyFrame.<event_handler>
        filename = "./locale/messages.po"
        default_file = os.path.basename(filename)
        default_dir = os.path.dirname(filename)

        with wx.FileDialog(
                self,
                _("Open"),
                defaultDir=default_dir,
                defaultFile=default_file,
                wildcard="*.po",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            fileDialog.SetFilename(default_file)
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind
            pathname = fileDialog.GetPath()
            self.panel.load_translation(pathname)

    def on_menu_open_template(self, event):  # wxGlade: MyFrame.<event_handler>
        self.on_menu_open(event)

    def generate_from_python_sources(self, directory):
        """
        This will later be replaced with internal parsing of the python files.
        :param directory:
        :return:
        """
        for python_file in glob.glob("%s/**/*.py" % directory, recursive=True):
            file = open(python_file, "r", encoding="utf-8").read()
            search = re.compile("_\([\"\']([^\"\']*)[\"\']\)")
            for m in search.findall(file):
                self.panel.add_entry(msgid=str(m))
        self.panel.update()

    def on_menu_open_sources(self, event):
        dlg = wx.DirDialog(self,
                           message="Choose python sources directory",
                           style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            directory = os.path.abspath(dlg.GetPath())
            self.generate_from_python_sources(directory)
        dlg.Destroy()

    def on_menu_save(self, event):  # wxGlade: MyFrame.<event_handler>
        with wx.FileDialog(
                self,
                _("Save Project"),
                wildcard="*.po",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind
            pathname = fileDialog.GetPath()
            if not pathname.lower().endswith(".po"):
                pathname += ".po"
            self.panel.save_translation(pathname)

    def on_menu_saveas(self, event):  # wxGlade: MyFrame.<event_handler>
        print("Event handler 'on_menu_saveas' not implemented!")
        event.Skip()

    def on_menu_export(self, event):  # wxGlade: MyFrame.<event_handler>
        print("Event handler 'on_menu_export' not implemented!")
        event.Skip()

    def on_menu_previous(self, event):  # wxGlade: MyFrame.<event_handler>
        self.panel.previous()

    def on_menu_next(self, event):  # wxGlade: MyFrame.<event_handler>
        self.panel.next()

    def on_menu_source(self, event):  # wxGlade: MyFrame.<event_handler>
        self.panel.source()


# end of class MyFrame

class PoboyApp(wx.App):
    def OnInit(self):
        self.frame = PoboyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

# end of class MyApp

if __name__ == "__main__":
    app = PoboyApp(0)
    app.MainLoop()
