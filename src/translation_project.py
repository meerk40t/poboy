import os
from collections import OrderedDict
from datetime import datetime

from babelmsg import mofile
from src.utils import (
    HEADER,
    TEMPLATE,
    generate_template_from_python_package,
    load,
    save,
)


class TranslationProject:
    """
    Translation Project is the project class it stores the local sources directory the locale directory should be
    a subdirectory of the project directory. And it stores a list of all the catalogs within this project including
    the template.
    """

    def __init__(self):
        self.catalogs = OrderedDict()
        self.name = ""
        self.charset = 0
        self.directory = None
        self.template_file = "/locale/messages.pot"
        self.catalog_file = "/locale/{locale}/LC_MESSAGES/{domain}.po"

    def clear(self):
        self.catalogs.clear()
        self.name = ""
        self.charset = 0
        self.directory = None
        self.template_file = "/locale/messages.pot"
        self.catalog_file = "/locale/{locale}/LC_MESSAGES/{domain}.po"

    def init(self, locale: str, domain: str = "messages", language: str = None):
        template = self.catalogs.get(TEMPLATE)
        translate = template.clone()
        translate._locale = locale
        translate.revision_date = datetime.now()
        translate.fuzzy = False
        translate.filename = self.catalog_file.format(
            locale=str(locale), domain=str(domain), language=str(language)
        )
        self.catalogs[locale] = translate
        self.save(translate)

    def compile_all(self):
        for c in self.catalogs:
            if c == TEMPLATE:
                continue  # We do not compile template objects.
            catalog = self.catalogs[c]
            filename = catalog.filename
            if filename.endswith(".po"):
                filename = filename[:-3]
            filename += ".mo"
            with open(filename, "wb") as save:
                mofile.write_mo(save, catalog)

    def save_all(self):
        for c in self.catalogs:
            catalog = self.catalogs[c]
            save(catalog)

    def save(self, catalog):
        save(catalog)

    def save_locale(self, locale: str):
        catalog = self.catalogs[locale]
        self.save(catalog)

    def load(self, filename, locale=None):
        catalog = load(filename)
        self.catalogs[locale] = catalog

    def load_all_translations(self):
        if self.directory is None:
            raise FileNotFoundError
        locale_directory = os.path.join(self.directory, "locale")
        for path, dirs, files in os.walk(locale_directory):
            for file in files:
                if file.endswith(".po"):
                    basedir = os.path.split(os.path.relpath(path, locale_directory))[0]
                    self.load(os.path.join(path, file), locale=basedir)
                if file.endswith(".pot"):
                    self.load(os.path.join(path, file), locale=TEMPLATE)

    def babel_update(
        self,
        no_fuzzy_matching=False,
        update_header_comment=False,
        keep_user_comments=True,
    ):
        template = self.catalogs[TEMPLATE]
        if template is None:
            return

        for catalog in self.catalogs.values():
            if catalog.locale is None:
                continue  # Cannot update the template
            catalog.update(
                template,
                no_fuzzy_matching=no_fuzzy_matching,
                update_header_comment=update_header_comment,
                keep_user_comments=keep_user_comments,
            )

    def babel_extract(self):
        new_template = generate_template_from_python_package(self.directory)
        template = self.catalogs.get(TEMPLATE)
        if template is not None:
            new_template.difference(template)
            new_template.properties_of(template)
        self.catalogs[TEMPLATE] = new_template

    def calculate_updates(self):
        template = self.catalogs.get(TEMPLATE)
        if template is None:
            return
        for message in template:
            msgid = str(message.id)
            name = msgid.strip()
            if name == HEADER:
                continue
            for catalog in self.catalogs.values():
                if msgid not in catalog._messages:
                    catalog.new[msgid] = message.clone()

    def perform_updates(self):
        for catalog in self.catalogs.values():
            catalog._messages.update(catalog.new)
            catalog.new.clear()

    def delete_equals(self):
        for catalog in self.catalogs.values():
            for message in catalog:
                if message.id == message.string:
                    message.string = None

    def get_orphans(self, catalog):
        template = self.catalogs[TEMPLATE]
        if template is None:
            return
        for m in catalog._messages:
            message = catalog._messages[m]
            msgid = str(message.id)
            name = msgid.strip()
            if name == HEADER:
                continue
            if msgid not in template._messages:
                yield message

    def mark_all_orphans_obsolete(self):
        template = self.catalogs[TEMPLATE]
        if template is None:
            return
        for message in template:
            msgid = str(message.id)
            name = msgid.strip()
            if name == HEADER:
                continue
            for catalog in self.catalogs.values():
                if msgid not in catalog._messages:
                    new_message = message.clone()
                    catalog.obsolete[msgid] = new_message
                    new_message.modified = True
