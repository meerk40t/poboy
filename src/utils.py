import os
import re
from collections import OrderedDict
from copy import copy
from datetime import datetime
from difflib import get_close_matches

import wx

from babelmsg import Catalog, extract, mofile, pofile

PUNCTUATION = (".", "?", "!", ":", ";")
TEMPLATE = ""
HEADER = ""
PRINTF_RE = re.compile(
    r"(%(?:(?:[-+0#]{0,5})(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:h|l|ll|w|I|I32|I64)?[cCdiouxXeEfgGaAnpsSZ])|%%)"
)


def save(catalog, filename=None, write_mo=True):
    if filename is None:
        filename = catalog.filename
    if filename is None:
        raise FileNotFoundError
    with open(filename, "wb") as save:
        pofile.write_po(save, catalog, original_header=False)
    if filename.endswith(".pot") or not write_mo:
        return
    if filename.endswith(".po"):
        filename = filename[:-3]
    filename += ".mo"
    with open(filename, "wb") as save:
        mofile.write_mo(save, catalog)


def load(filename):
    with open(filename, "r", encoding="utf-8") as file:
        catalog = pofile.read_po(file, filename=filename)
        return catalog


def generate_template_from_python_package(sources_directory, strip_comment_tags=False):
    template = Catalog()
    for filename, lineno, message, comments, context in extract.extract_from_dir(
        sources_directory,
        strip_comment_tags=strip_comment_tags,
    ):
        template.add(
            message,
            None,
            [(filename, lineno)],
            auto_comments=comments,
            context=context,
        )
    return template


def obsolete_orphans(tree, catalog, panel):
    for m in list(catalog.orphans):
        message = catalog[m]
        parents = [tree.GetItemParent(item) for item in message.items]
        if catalog.workflow_orphans in parents:
            message.modified = True
            catalog.obsolete[m] = message
            del catalog[m]
            del catalog.orphans[m]

            for item in message.items:
                tree.Delete(item)
            tree.Delete(message.item)

            message.item = tree.AppendItem(
                catalog.workflow_obsolete, m, data=(catalog, message)
            )


def delete_orphans(tree, catalog, panel):
    for m in list(catalog.orphans):
        message = catalog[m]
        message.modified = True
        for item in message.items:
            tree.Delete(item)
        del catalog[m]
        del catalog.orphans[m]


def save_as_patch(tree, catalog, panel):
    newcatalog = catalog.clone()
    newcatalog._messages.clear()
    newcatalog._messages.update(catalog.new)
    save(newcatalog, "patch.po", write_mo=False)


def move_new_to_general(tree, catalog, panel):
    for m in list(catalog.new):
        message = catalog.new[m]
        message.modified = True
        del catalog.new[m]
        catalog[m] = message

        for item in message.items:
            tree.Delete(item)
        tree.Delete(message.item)

        message.item = tree.AppendItem(catalog.workflow_all, m, data=(catalog, message))
        panel.message_revalidate(catalog, message)


def fuzzy_match(tree, catalog, panel):
    candidates = list(catalog.orphans)
    candidates.extend(catalog.obsolete)

    for new_message in catalog.new.values():
        matches = get_close_matches(new_message.id, candidates, 1, cutoff=0.85)
        if matches:
            match = matches[0]
            cur_message = None
            try:
                cur_message = catalog.orphans[match]
            except KeyError:
                pass
            try:
                cur_message = catalog.obsolete[match]
            except KeyError:
                pass
            if not cur_message:
                continue
            new_message.string = copy(cur_message.string)
            new_message.fuzzy = True
            new_message.modified = True
            panel.message_revalidate(catalog, new_message)
