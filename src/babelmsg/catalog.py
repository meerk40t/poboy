# -*- coding: utf-8 -*-
"""
    babel.messages.catalog
    ~~~~~~~~~~~~~~~~~~~~~~

    Data structures for message catalogs.

    :copyright: (c) 2013-2021 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""

import re
from cgi import parse_header
from collections import OrderedDict
from copy import copy
from datetime import datetime
from datetime import time as time_
from datetime import timezone
from difflib import get_close_matches
from email import message_from_string

from .core import Locale, UnknownLocaleError
from .plurals import get_plural

__all__ = ["Message", "Catalog", "TranslationError"]

from .util import _cmp, distinct

PYTHON_FORMAT = re.compile(
    r"""
    \%
        (?:\(([\w]*)\))?
        (
            [-#0\ +]?(?:\*|[\d]+)?
            (?:\.(?:\*|[\d]+))?
            [hlL]?
        )
        ([diouxXeEfFgGcrs%])
""",
    re.VERBOSE,
)


class Message(object):
    """Representation of a single message in a catalog."""

    def __init__(
        self,
        id,
        string="",
        locations=(),
        flags=(),
        auto_comments=(),
        user_comments=(),
        previous_id=(),
        lineno=None,
        context=None,
        original_lines=None,
        modified=False,
        items=None,
    ):
        """Create the message object.

        :param id: the message ID, or a ``(singular, plural)`` tuple for
                   pluralizable messages
        :param string: the translated message string, or a
                       ``(singular, plural)`` tuple for pluralizable messages
        :param locations: a sequence of ``(filename, lineno)`` tuples
        :param flags: a set or sequence of flags
        :param auto_comments: a sequence of automatic comments for the message
        :param user_comments: a sequence of user comments for the message
        :param previous_id: the previous message ID, or a ``(singular, plural)``
                            tuple for pluralizable messages
        :param lineno: the line number on which the msgid line was found in the
                       PO file, if any
        :param context: the message context
        :param original_lines: the original lines that were parsed into this message
        :param modified: modified flag for this particular message
        :param items: the tree items list for storage purposes.
        """
        self._id = id
        if not string and self.pluralizable:
            string = ("", "")
        self._string = string
        self.locations = list(distinct(locations))
        self.flags = set(flags)
        if id and self.python_format:
            self.flags.add("python-format")
        else:
            self.flags.discard("python-format")
        self.auto_comments = list(distinct(auto_comments))
        self.user_comments = list(distinct(user_comments))
        if isinstance(previous_id, str):
            self.previous_id = [previous_id]
        else:
            self.previous_id = list(previous_id)
        self.lineno = lineno
        self.context = context

        self.original_lines = original_lines
        self.modified = modified

        self.items = items
        if self.items is None:
            self.items = list()

    def __repr__(self):
        return "<%s %r (flags: %r)>" % (type(self).__name__, self._id, list(self.flags))

    def __cmp__(self, other):
        """Compare Messages, taking into account plural ids"""

        def values_to_compare(obj):
            if isinstance(obj, Message) and obj.pluralizable:
                return obj.id[0], obj.context or ""
            return obj.id, obj.context or ""

        return _cmp(values_to_compare(self), values_to_compare(other))

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def clone(self):
        return Message(
            *map(
                copy,
                (
                    self._id,
                    self._string,
                    self.locations,
                    self.flags,
                    self.auto_comments,
                    self.user_comments,
                    self.previous_id,
                    self.lineno,
                    self.context,
                    self.original_lines,
                    self.modified,
                ),
            )
        )

    def check(self, catalog=None):
        """Run various validation checks on the message.  Some validations
        are only performed if the catalog is provided.  This method returns
        a sequence of `TranslationError` objects.

        :rtype: ``iterator``
        :param catalog: A catalog instance that is passed to the checkers
        :see: `Catalog.check` for a way to perform checks for all messages
              in a catalog.
        """
        from .checkers import checkers

        errors = []
        for checker in checkers:
            try:
                checker(catalog, self)
            except TranslationError as e:
                errors.append(e)
        return errors

    @property
    def fuzzy(self):
        """Whether the translation is fuzzy.

        >>> Message('foo').fuzzy
        False
        >>> msg = Message('foo', 'foo', flags=['fuzzy'])
        >>> msg.fuzzy
        True
        >>> msg
        <Message 'foo' (flags: ['fuzzy'])>

        :type:  `bool`"""
        return "fuzzy" in self.flags

    @fuzzy.setter
    def fuzzy(self, fuzzy: bool):
        self.modified = True
        if fuzzy:
            if "fuzzy" not in self.flags:
                self.flags.add("fuzzy")
        else:
            if "fuzzy" in self.flags:
                self.flags.discard("fuzzy")

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value
        self.modified = True

    @property
    def string(self):
        return self._string

    @string.setter
    def string(self, value):
        self._string = value
        self.modified = True

    @property
    def pluralizable(self):
        """Whether the message is plurizable.

        >>> Message('foo').pluralizable
        False
        >>> Message(('foo', 'bar')).pluralizable
        True

        :type:  `bool`"""
        return isinstance(self._id, (list, tuple))

    @property
    def python_format(self):
        """Whether the message contains Python-style parameters.

        >>> Message('foo %(name)s bar').python_format
        True
        >>> Message(('foo %(name)s', 'foo %(name)s')).python_format
        True

        :type:  `bool`"""
        ids = self._id
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        return any(PYTHON_FORMAT.search(id) for id in ids)


class TranslationError(Exception):
    """Exception thrown by translation checkers when invalid message
    translations are encountered."""


DEFAULT_HEADER = """\
# Translations template for PROJECT.
# Copyright (C) YEAR ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#"""


class Catalog(object):
    """Representation of a message catalog."""

    def __init__(
        self,
        locale=None,
        domain=None,
        header_comment=DEFAULT_HEADER,
        project=None,
        version=None,
        copyright_holder=None,
        msgid_bugs_address=None,
        creation_date=None,
        revision_date=None,
        last_translator=None,
        language_team=None,
        charset=None,
        fuzzy=True,
        filename=None,
    ):
        """Initialize the catalog object.

        :param locale: the locale identifier or `Locale` object, or `None`
                       if the catalog is not bound to a locale (which basically
                       means it's a template)
        :param domain: the message domain
        :param header_comment: the header comment as string, or `None` for the
                               default header
        :param project: the project's name
        :param version: the project's version
        :param copyright_holder: the copyright holder of the catalog
        :param msgid_bugs_address: the email address or URL to submit bug
                                   reports to
        :param creation_date: the date the catalog was created
        :param revision_date: the date the catalog was revised
        :param last_translator: the name and email of the last translator
        :param language_team: the name and email of the language team
        :param charset: the encoding to use in the output (defaults to utf-8)
        :param fuzzy: the fuzzy bit on the catalog header
        """
        self.domain = domain
        self.locale = locale
        self._header_comment = header_comment
        self._messages = OrderedDict()

        self.original_header = None
        self.project = project or "PROJECT"
        self.version = version or "VERSION"
        self.copyright_holder = copyright_holder or "ORGANIZATION"
        self.msgid_bugs_address = msgid_bugs_address or "EMAIL@ADDRESS"

        self.last_translator = last_translator or "FULL NAME <EMAIL@ADDRESS>"
        """Name and email address of the last translator."""
        self.language_team = language_team or "LANGUAGE <LL@li.org>"
        """Name and email address of the language team."""

        self.charset = charset or "utf-8"

        if creation_date is None:
            creation_date = datetime.now()
        self.creation_date = creation_date
        if revision_date is None:
            revision_date = datetime.now()
        self.revision_date = revision_date
        self.fuzzy = fuzzy

        self.modified = False
        self.filename = filename

        self.new = OrderedDict()  # Dictionary of new messages from template
        self.orphans = OrderedDict()  # Dictionary of orphaned events from messages
        self.obsolete = OrderedDict()  # Dictionary of obsolete messages

        self._num_plurals = None
        self._plural_expr = None

    def clone(self):
        c = Catalog(
            *map(
                copy,
                (
                    self.locale,
                    self.domain,
                    self._header_comment,
                    self.project,
                    self.version,
                    self.copyright_holder,
                    self.msgid_bugs_address,
                    self.creation_date,
                    self.revision_date,
                    self.last_translator,
                    self.language_team,
                    self.charset,
                    self.fuzzy,
                    self.filename,
                ),
            )
        )
        for m in self._messages:
            message = self._messages[m]
            c[message.id] = message.clone()
        return c

    def properties_of(self, template):
        self.locale = template.locale
        self.domain = template.domain
        self._header_comment = template._header_comment
        self.project = template.project
        self.version = template.version
        self.copyright_holder = template.copyright_holder
        self.msgid_bugs_address = template.msgid_bugs_address
        self.creation_date = template.creation_date
        self.revision_date = template.revision_date
        self.last_translator = template.last_translator
        self.language_team = template.language_team
        self.charset = template.charset
        self.fuzzy = template.fuzzy
        self.filename = template.filename

    def _set_locale(self, locale):
        if locale is None:
            self._locale_identifier = None
            self._locale = None
            return

        if isinstance(locale, Locale):
            self._locale_identifier = str(locale)
            self._locale = locale
            return

        if isinstance(locale, str):
            self._locale_identifier = str(locale)
            try:
                self._locale = Locale.parse(locale)
            except UnknownLocaleError:
                self._locale = None
            return

        raise TypeError(
            "`locale` must be a Locale, a locale identifier string, or None; got %r"
            % locale
        )

    def _get_locale(self):
        return self._locale

    def _get_locale_identifier(self):
        return self._locale_identifier

    locale = property(_get_locale, _set_locale)
    locale_identifier = property(_get_locale_identifier)

    def _get_header_comment(self):
        comment = self._header_comment
        year = datetime.now().strftime("%Y")
        if hasattr(self.revision_date, "strftime"):
            year = self.revision_date.strftime("%Y")
        comment = (
            comment.replace("PROJECT", self.project)
            .replace("VERSION", self.version)
            .replace("YEAR", year)
            .replace("ORGANIZATION", self.copyright_holder)
        )
        locale_name = str(self.locale)
        if locale_name:
            comment = comment.replace(
                "Translations template", "%s translations" % locale_name
            )
        return comment

    def _set_header_comment(self, string):
        self._header_comment = string

    header_comment = property(
        _get_header_comment,
        _set_header_comment,
        doc="""\
    The header comment for the catalog.

    >>> catalog = Catalog(project='Foobar', version='1.0',
    ...                   copyright_holder='Foo Company')
    >>> print(catalog.header_comment) #doctest: +ELLIPSIS
    # Translations template for Foobar.
    # Copyright (C) ... Foo Company
    # This file is distributed under the same license as the Foobar project.
    # FIRST AUTHOR <EMAIL@ADDRESS>, ....
    #

    The header can also be set from a string. Any known upper-case variables
    will be replaced when the header is retrieved again:

    >>> catalog = Catalog(project='Foobar', version='1.0',
    ...                   copyright_holder='Foo Company')
    >>> catalog.header_comment = '''\\
    ... # The POT for my really cool PROJECT project.
    ... # Copyright (C) 1990-2003 ORGANIZATION
    ... # This file is distributed under the same license as the PROJECT
    ... # project.
    ... #'''
    >>> print(catalog.header_comment)
    # The POT for my really cool Foobar project.
    # Copyright (C) 1990-2003 Foo Company
    # This file is distributed under the same license as the Foobar
    # project.
    #

    :type: `unicode`
    """,
    )

    def _get_mime_headers(self):
        headers = []
        headers.append(("Project-Id-Version", "%s %s" % (self.project, self.version)))
        headers.append(("Report-Msgid-Bugs-To", self.msgid_bugs_address))
        headers.append(
            (
                "POT-Creation-Date",
                datetime.now(timezone.utc).strftime("%y-%m-%d %H:%M%Z"),
            )
        )
        if isinstance(self.revision_date, (datetime, time_, int, float)):
            headers.append(
                (
                    "PO-Revision-Date",
                    datetime.now(timezone.utc).strftime("%y-%m-%d %H:%M%Z"),
                )
            )
        else:
            headers.append(("PO-Revision-Date", self.revision_date))
        headers.append(("Last-Translator", self.last_translator))
        if self.locale_identifier:
            headers.append(("Language", str(self.locale_identifier)))
        if self.locale_identifier and ("LANGUAGE" in self.language_team):
            headers.append(
                (
                    "Language-Team",
                    self.language_team.replace("LANGUAGE", str(self.locale_identifier)),
                )
            )
        else:
            headers.append(("Language-Team", self.language_team))
        if self.locale is not None:
            headers.append(("Plural-Forms", self.plural_forms))
        headers.append(("MIME-Version", "1.0"))
        headers.append(("Content-Type", "text/plain; charset=%s" % self.charset))
        headers.append(("Content-Transfer-Encoding", "8bit"))
        headers.append(("Generated-By", "Poboy %s\n" % "0.0.1"))
        return headers

    def _force_text(self, s, encoding="utf-8", errors="strict"):
        if isinstance(s, str):
            return s
        if isinstance(s, bytes):
            return s.decode(encoding, errors)
        return str(s)

    def _set_mime_headers(self, headers):
        for name, value in headers:
            name = self._force_text(name.lower(), encoding=self.charset)
            value = self._force_text(value, encoding=self.charset)
            if name == "project-id-version":
                parts = value.split(" ")
                self.project = " ".join(parts[:-1])
                self.version = parts[-1]
            elif name == "report-msgid-bugs-to":
                self.msgid_bugs_address = value
            elif name == "last-translator":
                self.last_translator = value
            elif name == "language":
                value = value.replace("-", "_")
                self._set_locale(value)
            elif name == "language-team":
                self.language_team = value
            elif name == "content-type":
                mimetype, params = parse_header(value)
                if "charset" in params:
                    self.charset = params["charset"].lower()
            elif name == "plural-forms":
                _, params = parse_header(" ;" + value)
                self._num_plurals = int(params.get("nplurals", 2))
                self._plural_expr = params.get("plural", "(n != 1)")
            # elif name == "pot-creation-date":
            #     self.creation_date = _parse_datetime_header(value)
            # elif name == "po-revision-date":
            #     # Keep the value if it's not the default one
            #     if "YEAR" not in value:
            #         self.revision_date = _parse_datetime_header(value)

    mime_headers = property(
        _get_mime_headers,
        _set_mime_headers,
        doc="""\
    The MIME headers of the catalog, used for the special ``msgid ""`` entry.

    The behavior of this property changes slightly depending on whether a locale
    is set or not, the latter indicating that the catalog is actually a template
    for actual translations.

    Here's an example of the output for such a catalog template:

    >>> from babel.dates import UTC
    >>> created = datetime(1990, 4, 1, 15, 30, tzinfo=UTC)
    >>> catalog = Catalog(project='Foobar', version='1.0',
    ...                   creation_date=created)
    >>> for name, value in catalog.mime_headers:
    ...     print('%s: %s' % (name, value))
    Project-Id-Version: Foobar 1.0
    Report-Msgid-Bugs-To: EMAIL@ADDRESS
    POT-Creation-Date: 1990-04-01 15:30+0000
    PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
    Last-Translator: FULL NAME <EMAIL@ADDRESS>
    Language-Team: LANGUAGE <LL@li.org>
    MIME-Version: 1.0
    Content-Type: text/plain; charset=utf-8
    Content-Transfer-Encoding: 8bit
    Generated-By: Babel ...

    And here's an example of the output when the locale is set:

    >>> revised = datetime(1990, 8, 3, 12, 0, tzinfo=UTC)
    >>> catalog = Catalog(locale='de_DE', project='Foobar', version='1.0',
    ...                   creation_date=created, revision_date=revised,
    ...                   last_translator='John Doe <jd@example.com>',
    ...                   language_team='de_DE <de@example.com>')
    >>> for name, value in catalog.mime_headers:
    ...     print('%s: %s' % (name, value))
    Project-Id-Version: Foobar 1.0
    Report-Msgid-Bugs-To: EMAIL@ADDRESS
    POT-Creation-Date: 1990-04-01 15:30+0000
    PO-Revision-Date: 1990-08-03 12:00+0000
    Last-Translator: John Doe <jd@example.com>
    Language: de_DE
    Language-Team: de_DE <de@example.com>
    Plural-Forms: nplurals=2; plural=(n != 1)
    MIME-Version: 1.0
    Content-Type: text/plain; charset=utf-8
    Content-Transfer-Encoding: 8bit
    Generated-By: Babel ...

    :type: `list`
    """,
    )

    @property
    def num_plurals(self):
        """The number of plurals used by the catalog or locale.

        >>> Catalog(locale='en').num_plurals
        2
        >>> Catalog(locale='ga').num_plurals
        5

        :type: `int`"""
        if self._num_plurals is None:
            num = 2
            if self.locale:
                num = get_plural(self.locale)[0]
            self._num_plurals = num
        return self._num_plurals

    @property
    def plural_expr(self):
        """The plural expression used by the catalog or locale.

        >>> Catalog(locale='en').plural_expr
        '(n != 1)'
        >>> Catalog(locale='ga').plural_expr
        '(n==1 ? 0 : n==2 ? 1 : n>=3 && n<=6 ? 2 : n>=7 && n<=10 ? 3 : 4)'
        >>> Catalog(locale='ding').plural_expr  # unknown locale
        '(n != 1)'

        :type: `str`"""
        if self._plural_expr is None:
            expr = "(n != 1)"
            if self.locale:
                expr = get_plural(self.locale)[1]
            self._plural_expr = expr
        return self._plural_expr

    @property
    def plural_forms(self):
        """Return the plural forms declaration for the locale.

        >>> Catalog(locale='en').plural_forms
        'nplurals=2; plural=(n != 1)'
        >>> Catalog(locale='pt_BR').plural_forms
        'nplurals=2; plural=(n > 1)'

        :type: `str`"""
        return "nplurals=%s; plural=%s" % (self.num_plurals, self.plural_expr)

    def __contains__(self, id):
        """Return whether the catalog has a message with the specified ID."""
        return self._key_for(id) in self._messages

    def __len__(self):
        """The number of messages in the catalog.

        This does not include the special ``msgid ""`` entry."""
        return len(self._messages)

    def __iter__(self):
        """Iterates through all the entries in the catalog, in the order they
        were added, yielding a `Message` object for every entry.

        :rtype: ``iterator``"""
        buf = []
        for name, value in self.mime_headers:
            buf.append("%s: %s" % (name, value))
        flags = set()
        if self.fuzzy:
            flags |= {"fuzzy"}
        yield Message(
            "", "\n".join(buf), flags=flags, original_lines=self.original_header
        )
        for key in self._messages:
            yield self._messages[key]

    def __repr__(self):
        locale = ""
        if self.locale:
            locale = " %s" % self.locale
        return "<%s %r%s>" % (type(self).__name__, self.domain, locale)

    def __delitem__(self, id):
        """Delete the message with the specified ID."""
        self.delete(id)

    def __getitem__(self, id):
        """Return the message with the specified ID.

        :param id: the message ID
        """
        return self.get(id)

    def __setitem__(self, id, message):
        """Add or update the message with the specified ID.

        >>> catalog = Catalog()
        >>> catalog[u'foo'] = Message(u'foo')
        >>> catalog[u'foo']
        <Message u'foo' (flags: [])>

        If a message with that ID is already in the catalog, it is updated
        to include the locations and flags of the new message.

        >>> catalog = Catalog()
        >>> catalog[u'foo'] = Message(u'foo', locations=[('main.py', 1)])
        >>> catalog[u'foo'].locations
        [('main.py', 1)]
        >>> catalog[u'foo'] = Message(u'foo', locations=[('utils.py', 5)])
        >>> catalog[u'foo'].locations
        [('main.py', 1), ('utils.py', 5)]

        :param id: the message ID
        :param message: the `Message` object
        """
        key = self._key_for(id, message.context)
        current = self._messages.get(key)
        if current:
            if message.pluralizable and not current.pluralizable:
                # The new message adds pluralization
                current.id = message.id
                current.string = message.string
            current.locations = list(distinct(current.locations + message.locations))
            current.auto_comments = list(
                distinct(current.auto_comments + message.auto_comments)
            )
            current.user_comments = list(
                distinct(current.user_comments + message.user_comments)
            )
            current.flags |= message.flags
            message = current
        elif id == "":
            # special treatment for the header message
            self.original_header = message.original_lines
            self.mime_headers = message_from_string(message.string).items()
            self.header_comment = "\n".join(
                [("# %s" % c).rstrip() for c in message.user_comments]
            )
            self.fuzzy = message.fuzzy
        else:
            if isinstance(id, (list, tuple)):
                assert isinstance(
                    message.string, (list, tuple)
                ), "Expected sequence but got %s" % type(message.string)
            self._messages[key] = message

    def add(
        self,
        id,
        string=None,
        locations=(),
        flags=(),
        auto_comments=(),
        user_comments=(),
        previous_id=(),
        lineno=None,
        context=None,
    ):
        """Add or update the message with the specified ID.

        >>> catalog = Catalog()
        >>> catalog.add(u'foo')
        <Message ...>
        >>> catalog[u'foo']
        <Message u'foo' (flags: [])>

        This method simply constructs a `Message` object with the given
        arguments and invokes `__setitem__` with that object.

        :param id: the message ID, or a ``(singular, plural)`` tuple for
                   pluralizable messages
        :param string: the translated message string, or a
                       ``(singular, plural)`` tuple for pluralizable messages
        :param locations: a sequence of ``(filename, lineno)`` tuples
        :param flags: a set or sequence of flags
        :param auto_comments: a sequence of automatic comments
        :param user_comments: a sequence of user comments
        :param previous_id: the previous message ID, or a ``(singular, plural)``
                            tuple for pluralizable messages
        :param lineno: the line number on which the msgid line was found in the
                       PO file, if any
        :param context: the message context
        """
        message = Message(
            id,
            string,
            list(locations),
            flags,
            auto_comments,
            user_comments,
            previous_id,
            lineno=lineno,
            context=context,
        )
        self[id] = message
        return message

    def check(self):
        """Run various validation checks on the translations in the catalog.

        For every message which fails validation, this method yield a
        ``(message, errors)`` tuple, where ``message`` is the `Message` object
        and ``errors`` is a sequence of `TranslationError` objects.

        :rtype: ``iterator``
        """
        for message in self._messages.values():
            errors = message.check(catalog=self)
            if errors:
                yield message, errors

    def get(self, id, context=None):
        """Return the message with the specified ID and context.

        :param id: the message ID
        :param context: the message context, or ``None`` for no context
        """
        return self._messages.get(self._key_for(id, context))

    def delete(self, id, context=None):
        """Delete the message with the specified ID and context.

        :param id: the message ID
        :param context: the message context, or ``None`` for no context
        """
        key = self._key_for(id, context)
        if key in self._messages:
            del self._messages[key]

    def difference(self, template):
        messages = self._messages
        remaining = messages.copy()

        for message in template:
            if message.id:
                key = self._key_for(message.id, message.context)
                if key in messages:
                    remaining.pop(message.id)
                else:
                    self.new[message.id] = message.clone()
        for msgid in remaining:
            message = remaining[msgid]
            self.orphans[msgid] = message

    def update(
        self,
        template,
        no_fuzzy_matching=False,
        update_header_comment=False,
        keep_user_comments=True,
    ):
        """Update the catalog based on the given template catalog.

        >>> template = Catalog()
        >>> template.add('green', locations=[('main.py', 99)])
        <Message ...>
        >>> template.add('blue', locations=[('main.py', 100)])
        <Message ...>
        >>> template.add(('salad', 'salads'), locations=[('util.py', 42)])
        <Message ...>
        >>> catalog = Catalog(locale='de_DE')
        >>> catalog.add('blue', u'blau', locations=[('main.py', 98)])
        <Message ...>
        >>> catalog.add('head', u'Kopf', locations=[('util.py', 33)])
        <Message ...>
        >>> catalog.add(('salad', 'salads'), (u'Salat', u'Salate'),
        ...             locations=[('util.py', 38)])
        <Message ...>

        >>> catalog.update(template)
        >>> len(catalog)
        3

        >>> msg1 = catalog['green']
        >>> msg1.string
        >>> msg1.locations
        [('main.py', 99)]

        >>> msg2 = catalog['blue']
        >>> msg2.string
        u'blau'
        >>> msg2.locations
        [('main.py', 100)]

        >>> msg3 = catalog['salad']
        >>> msg3.string
        (u'Salat', u'Salate')
        >>> msg3.locations
        [('util.py', 42)]

        Messages that are in the catalog but not in the template are removed
        from the main collection, but can still be accessed via the `obsolete`
        member:

        >>> 'head' in catalog
        False
        >>> list(catalog.obsolete.values())
        [<Message 'head' (flags: [])>]

        :param template: the reference catalog, usually read from a POT file
        :param no_fuzzy_matching: whether to use fuzzy matching of message IDs
        """
        messages = self._messages
        remaining = messages.copy()
        self._messages = OrderedDict()
        self.new = OrderedDict()
        self.orphans = OrderedDict()

        # Prepare for fuzzy matching
        fuzzy_candidates = []
        if not no_fuzzy_matching:
            fuzzy_candidates = dict(
                [
                    (self._key_for(msgid), messages[msgid].context)
                    for msgid in messages
                    if msgid and messages[msgid].string
                ]
            )
        fuzzy_matches = set()

        def _merge(message, oldkey, newkey, fuzzy=False):
            message = message.clone()
            if oldkey != newkey:
                fuzzy = True
                fuzzy_matches.add(oldkey)
                oldmsg = messages.get(oldkey)
                if isinstance(oldmsg.id, str):
                    message.previous_id = [oldmsg.id]
                else:
                    message.previous_id = list(oldmsg.id)
            else:
                oldmsg = remaining.pop(oldkey, None)
            message.string = oldmsg.string

            if keep_user_comments:
                message.user_comments = list(distinct(oldmsg.user_comments))

            if isinstance(message.id, (list, tuple)):
                if not isinstance(message.string, (list, tuple)):
                    fuzzy = True
                    message.string = tuple(
                        [message.string] + ([""] * (len(message.id) - 1))
                    )
                elif len(message.string) != self.num_plurals:
                    fuzzy = True
                    message.string = tuple(message.string[: len(oldmsg.string)])
            elif isinstance(message.string, (list, tuple)):
                fuzzy = True
                message.string = message.string[0]
            message.flags |= oldmsg.flags
            if fuzzy:
                message.fuzzy = True
            self[message.id] = message

        for message in template:
            if message.id:
                key = self._key_for(message.id, message.context)
                if key in messages:
                    _merge(message, key, key)
                else:
                    if not no_fuzzy_matching:
                        # do some fuzzy matching with difflib
                        if isinstance(key, tuple):
                            matchkey = key[0]  # just the msgid, no context
                        else:
                            matchkey = key
                        matches = get_close_matches(
                            matchkey.lower().strip(),
                            fuzzy_candidates.keys(),
                            1,
                            cutoff=0.85,
                        )
                        if matches:
                            newkey = matches[0]
                            newctxt = fuzzy_candidates[newkey]
                            if newctxt is not None:
                                newkey = newkey, newctxt
                            _merge(message, newkey, key, True)
                            continue

                    self[message.id] = message

        for msgid in remaining:
            if no_fuzzy_matching or msgid not in fuzzy_matches:
                message = remaining[msgid]
                self.obsolete[msgid] = message
                message.modified = True

        if update_header_comment:
            # Allow the updated catalog's header to be rewritten based on the
            # template's header
            self.header_comment = template.header_comment

        # Make updated catalog's POT-Creation-Date equal to the template
        # used to update the catalog
        self.creation_date = template.creation_date

    def _key_for(self, id, context=None):
        """The key for a message is just the singular ID even for pluralizable
        messages, but is a ``(msgid, msgctxt)`` tuple for context-specific
        messages.
        """
        key = id
        if isinstance(key, (list, tuple)):
            key = id[0]
        if context is not None:
            key = (key, context)
        return key
