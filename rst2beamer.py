#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2007-2009 Ryan Krauss, Paul-Michael Agapow
# Copyright (C) 2013-2015 Steven Myint
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""A docutils script converting restructured text into Beamer-flavoured LaTeX.

Beamer is a LaTeX document class for presentations. Via this script, ReST can
be used to prepare slides. It can be called::

        rst2beamer.py infile.txt > outfile.tex

where ``infile.txt`` contains the rst and ``outfile.tex`` contains the
Beamer-flavoured LaTeX.

See <http:www.agapow.net/software/rst2beamer> for more details.

"""

# TODO: modifications for handout sections?
# TODO: sections and subsections?
# TODO: convert document metadata to front page fields?
# TODO: toc-conversion?
# TODO: fix descriptions

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from docutils.core import publish_cmdline, default_description
from docutils.writers.latex2e import Writer as Latex2eWriter
from docutils.writers.latex2e import LaTeXTranslator, DocumentClass
from docutils import nodes
from docutils.nodes import fully_normalize_name as normalize_name
from docutils.parsers.rst import directives, Directive
from docutils import utils
from docutils.writers.latex2e import PreambleCmds


__docformat__ = 'restructuredtext en'
__author__ = ('Ryan Krauss <ryanwkrauss@gmail.com> & '
              'Paul-Michael Agapow <agapow@bbsrc.ac.uk>')
__version__ = '0.8.6'


SHOWNOTES_FALSE = 'false'
SHOWNOTES_TRUE = 'true'
SHOWNOTES_ONLY = 'only'
SHOWNOTES_LEFT = 'left'
SHOWNOTES_RIGHT = 'right'
SHOWNOTES_TOP = 'top'
SHOWNOTES_BOTTOM = 'bottom'

SHOWNOTES_OPTIONS = [
    SHOWNOTES_FALSE,
    SHOWNOTES_TRUE,
    SHOWNOTES_ONLY,
    SHOWNOTES_LEFT,
    SHOWNOTES_RIGHT,
    SHOWNOTES_TOP,
    SHOWNOTES_BOTTOM,
]

HIGHLIGHT_OPTIONS = {
    'python': 'python',
    'guess': 'guess',
    'c++': 'cpp',
}

BEAMER_SPEC = (
    'Beamer options',
    'These are derived almost entirely from the LaTeX2e options',
    tuple(
        [
            (
                'Specify theme.',
                ['--theme'],
                {'default': 'Ilmenau', }
            ),
            (
                'Overlay bulleted items. Put [<+-| alert@+>] at the end of '
                '\\begin{itemize} so that Beamer creates an overlay for each '
                'bulleted item and the presentation reveals one bullet at a '
                'time',
                ['--overlaybullets'],
                {'default': False, }
            ),
            (
                'Default for whether or not to pass the fragile option to '
                'the beamber frames (slides).',
                ['--fragile-default'],
                {'default': True, }
            ),

            (
                'Center figures. All includegraphics statements will be put '
                'inside center environments.',
                ['--centerfigs'],
                {'default': True, }
            ),
            (
                'Shortauthor for use in header/footer of slide',
                ['--shortauthor'],
                {'default': '', }
            ),
            (
                'Shorttitle for use in header/footer of slide',
                ['--shorttitle'],
                {'default': '', }
            ),

            (
                # TODO: this doesn't seem to do anything ...
                'Specify document options. Multiple options can be given, '
                'separated by commas. Default is "10pt,a4paper".',
                ['--documentoptions'],
                {'default': '', }
            ),
            (
                'Print embedded notes along with the slides. Possible '
                "arguments include 'false' (don't show), 'only' (show "
                "only notes), 'left', 'right', 'top', 'bottom' (show in "
                'relation to the annotated slide).',
                ['--shownotes'],
                {
                    'action': 'store',
                    'type': 'choice',
                    'dest': 'shownotes',
                    'choices': SHOWNOTES_OPTIONS,
                    'default': SHOWNOTES_FALSE,
                }
            ),
            # should the pygments highlighter be used for codeblocks?
            (
                'Use the Pygments syntax highlighter to color blocks of '
                'code. Otherwise, they will be typeset as simple literal '
                'text. Obviously Pygments must be installed or an error '
                'will be raised. ',
                ['--no-codeblocks-use-pygments'],
                {
                    'action': 'store_false',
                    'dest': 'cb_use_pygments',
                    'default': True,
                }
            ),
            # replace tabs inside codeblocks?
            (
                'Replace the leading tabs in codeblocks with spaces.',
                ['--codeblocks-replace-tabs'],
                {
                    'action': 'store',
                    'type': int,
                    'dest': 'cb_replace_tabs',
                    'default': 0,
                }
            ),
            # what language the codeblock is if not specified
            (
                'The default language to highlight code blocks as. ',
                ['--codeblocks-default-language'],
                {
                    'action': 'store',
                    'type': 'choice',
                    'dest': 'cb_default_lang',
                    'choices': list(HIGHLIGHT_OPTIONS.values()),
                    'default': 'guess',
                }
            ),
        ] + list(Latex2eWriter.settings_spec[2][2:])
    ),
)

BEAMER_DEFAULTS = {
    'use_latex_toc': True,
    'output_encoding': 'utf-8',
    'documentclass': 'beamer',
    'documentoptions': 't',
    # text is at the top of each slide rather than centered. Changing to
    # 'c' centers the text on each slide (vertically)
}

BEAMER_DEFAULT_OVERRIDES = {'use_latex_docinfo': 1}


BOOL_DICT = {'false': False,
             'true': True,
             '0': False,
             '1': True}

PreambleCmds.documenttitle = r"""
%% Document title
\title[%s]{%s}
\author[%s]{%s}
\date{%s}
\maketitle
"""

DOCINFO_W_INSTITUTE = r"""
%% Document title
\title[%s]{%s}
\author[%s]{%s}
\date{%s}
\institute{%s}
\maketitle
"""


LEADING_SPACE_RE = re.compile('^ +')


def adjust_indent_spaces(strn, orig_width=8, new_width=3):
    """Adjust the leading space on a string so as to change the indent width.

    :Parameters:
        strn
            The source string to change.
        orig_width
            The expected width for an indent in the source string.
        new_width
            The new width to make an ident.

    :Returns:
        The original string re-indented.

    That takes strings that may be indented by a set number of spaces (or its
    multiple) and adjusts the indent for a new number of spaces. So if the
    expected indent width is 8 and the desired ident width is 3, a string has
    been indented by 16 spaces, will be changed to have a indent of 6.

    For example::

        >>> adjust_indent_spaces ('        foo')
        '   foo'
        >>> adjust_indent_spaces ('      foo', orig_width=2, new_width=1)
        '   foo'

    This is useful where meaningful indent must be preserved (i.e. passed
    through) ReST, especially tabs when used in the literal environments. ReST
    transforms tabs-as-indents to 8 spaces, which leads to excessively spaced
    out text. This function can be used to adjust the indent step to a
    reasonable size.

    .. note::

        Excess spaces (those above and beyond a multiple of the original
        indent width) will be preserved. Only indenting spaces will be
        handled. Mixing tabs and spaces is - as always - a bad idea.

    """
    # Preconditions & preparation:
    assert 1 <= orig_width
    assert 0 <= new_width
    if orig_width == new_width:
        return strn
    # Main:
    match = LEADING_SPACE_RE.match(strn)
    if match:
        indent_len = match.end() - match.start()
        indent_cnt = indent_len // orig_width
        indent_depth = indent_cnt * orig_width
        strn = ' ' * indent_cnt * new_width + strn[indent_depth:]
    return strn


def node_has_class(node, classes):
    """Does the node have one of these classes?

    :Parameters:
        node
            A docutils node
        class
            A class name or list of class names.

    :Returns:
        A boolean indicating membership.

    A convenience function, largely for testing for the special class names
    in containers.

    """
    # Preconditions & preparation:
    # wrap single name in list
    if not issubclass(type(classes), list):
        classes = [classes]
    # Main:
    for cname in classes:
        if cname in node['classes']:
            return True
    return False


def node_lang_class(node):
    """Extract a language specification from a node class names.

    :Parameters:
        node
            A docutils node

    :Returns:
        A string giving a language abbreviation (e.g. 'py') or None if no
        langauge is found.

    Some sourcecode containers can pass a (programming) language specification
    by passing it via a classname like 'lang-py'. This function searches a
    nodes classnames for those starting with 'lang-' and returns the trailing
    portion. Note that if more than one classname matches, only the first is
    seen.

    """
    # Main:
    for cname in node['classes']:
        if cname.startswith('lang-'):
            return cname[5:]
    return None


def wrap_children_in_columns(par_node, children, width=None):
    """Replace this node's children with columns containing the passed
    children.

    :Parameters:
        par_node
            The node whose children are to be replaced.
        children
            The new child nodes, to be wrapped in columns and added to the
            parent.
        width
            The width to be assigned to the columns.

    In constructing columns for beamer using either 'simplecolumns' approach,
    we have to wrap the original elements in column nodes, giving them an
    appropriate width. Note that this mutates parent node.

    """
    # Preconditions & preparation:
    # TODO: check for children and raise error if not?
    width = width or 0.90
    # Main:
    # calc width of child columns
    child_cnt = len(children)
    col_width = width / child_cnt
    # set each element of content in a column and add to column set
    new_children = []
    for child in children:
        col = column()
        col.width = col_width
        col.append(child)
        new_children.append(col)
    par_node.children = new_children


def has_sub_sections(node):
    """Test whether or not a section node has children with the tagname
    section.

    The function is going to be used to assess
    whether or not a certain section is the lowest level. Sections
    that have not sub-sections (i.e. no children with the tagname
    section) are assumed to be Beamer slides

    """
    for child in node.children:
        if child.tagname == 'section':
            return True
    return False


def string_to_bool(text, default=True):
    """Turn a commandline argument string into a boolean value.

    >>> string_to_bool('true')
    True

    >>> string_to_bool('false')
    False

    >>> string_to_bool('0')
    False

    >>> string_to_bool('1')
    True

    >>> string_to_bool('abc')
    True

    """
    if isinstance(text, bool):
        return text
    return BOOL_DICT.get(text.lower(), default)


def highlight_code(text, lang):
    """Syntax-highlight source code using Pygments.

    :Parameters:
        text
            The code to be formatted.
        lang
            The language of the source code.

    :Returns:
        A LaTeX formatted representation of the source code.

    """
    # Preconditions & preparation:
    from pygments import highlight
    from pygments.formatters import LatexFormatter
    lexer = get_lexer(text, lang)
    if not lexer:
        return text
    lexer.add_filter('whitespace', tabsize=3, tabs=' ')
    return highlight(text, lexer, LatexFormatter(tabsize=3))


def get_lexer(text, lang):
    """Return the Pygments lexer for parsing this sourcecode.

    :Parameters:
        text
            The sourcecode to be lexed for highlighting. This is analysed if
            the language is 'guess'.
        lang
            An abbreviation for the programming langauge of the code. Can be
            any 'name' accepted by Pygments, including 'none' (plain text) or
            'guess' (analyse the passed code for clues).

    :Returns:
        A Pygments lexer.

    """
    # TODO: what if source has errors?
    # Preconditions & preparation:
    from pygments.lexers import (get_lexer_by_name, TextLexer, guess_lexer)
    # Main:
    if lang == 'guess':
        try:
            return guess_lexer(text)
        except ValueError:
            return None
    elif lang == 'none':
        return TextLexer
    else:
        return get_lexer_by_name(lang)


# Special nodes for marking up beamer layout.
class columnset(nodes.container):

    """A group of columns to display on one slide.

    Named as per docutils standards.

    """
    # NOTE: a simple container, has no attributes.


class column(nodes.container):

    """A single column, grouping content.

    Named as per docutils standards.

    """

    width = 0


class beamer_note(nodes.container):

    """Annotations for a beamer presentation.

    Named as per docutils standards and to distinguish it from core
    docutils node type.

    """


class onlybeamer(nodes.container):

    """A block of text to appear in the presentation and not in the handouts or
    article form.

    Named as per docutils standards.

    """

    handouttext = ''


class block(nodes.container):

    """A block of text to appear in a block environment.

    Named as per docutils standards.

    """

    title = ''


# DIRECTIVES

class CodeBlockDirective(Directive):

    """Directive for a code block with special highlighting or line numbering
    settings.

    Unabashedly borrowed from the Sphinx source.

    """
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = {
        'linenos': directives.flag,
    }

    def run(self):
        # extract langauge from block or commandline
        # we allow the langauge specification to be optional
        try:
            language = self.arguments[0]
        except IndexError:
            language = 'guess'
        code = '\n'.join(self.content)
        literal = nodes.literal_block(code, code)
        literal['classes'].append('code-block')
        literal['language'] = language
        literal['linenos'] = 'linenos' in self.options
        return [literal]

for _name in ['code-block', 'sourcecode']:
    directives.register_directive(_name, CodeBlockDirective)


class SimpleColsDirective(Directive):

    """A directive that wraps all contained nodes in beamer columns.

    Accept 'width' as an optional argument for total width of contained
    columns.

    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {'width': float}

    def run(self):
        # Preconditions:
        self.assert_has_content()
        # get width
        width = self.options.get('width', 0.9)
        if (width <= 0.0) or (1.0 < width):
            raise self.error(
                "columnset width '%f' must be between 0.0 and 1.0" %
                width)
        # Main:
        # parse content of columnset
        dummy = nodes.Element()
        self.state.nested_parse(self.content, self.content_offset,
                                dummy)
        # make columnset
        text = '\n'.join(self.content)
        cset = columnset(text)
        # wrap children in columns & set widths
        wrap_children_in_columns(cset, dummy.children, width)
        # Postconditions & return:
        return [cset]

directives.register_directive('beamer-simplecolumns', SimpleColsDirective)


class ColumnSetDirective(Directive):

    """A directive that encloses explicit columns in a 'columns' environment.

    Within this, columns are explcitly set with the column directive. There is
    a single optional argument 'width' to determine the total width of
    columns on the page, expressed as a fraction of textwidth. If no width is
    given, it defaults to 0.90.

    Contained columns may have an assigned width. If not, the remaining width
    is divided amongst them. Contained columns can 'overassign' width,
    provided all column widths are defined.

    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {'width': float}

    def run(self):
        # Preconditions:
        self.assert_has_content()
        # get and check width of column set
        width = self.options.get('width', 0.9)
        if (width <= 0.0) or (1.0 < width):
            raise self.error(
                "columnset width '%f' must be between 0.0 and 1.0" % width)
        # Main:
        # make columnset
        text = '\n'.join(self.content)
        cset = columnset(text)
        # parse content of columnset
        self.state.nested_parse(self.content, self.content_offset, cset)
        # survey widths
        used_width = 0.0
        unsized_cols = []
        for child in cset:
            child_width = getattr(child, 'width', None)
            if child_width:
                used_width += child_width
            else:
                unsized_cols.append(child)

        if 1.0 < used_width:
            raise self.error(
                "cumulative column width '%f' exceeds 1.0" % used_width)
        # set unsized widths
        if unsized_cols:
            excess_width = width - used_width
            if excess_width <= 0.0:
                raise self.error(
                    "no room for unsized columns '%f'" % excess_width)
            col_width = excess_width / len(unsized_cols)
            for child in unsized_cols:
                child.width = col_width
        elif width < used_width:
            # TODO: should post a warning?
            pass
        # Postconditions & return:
        return [cset]

directives.register_directive('beamer-columnset', ColumnSetDirective)


class ColumnDirective(Directive):

    """A directive to explicitly create an individual column.

    This can only be used within the columnset directive. It can takes a
    single optional argument 'width' to determine the column width on
    page. If no width is given, it is recorded as None and should be
    later assigned by the enclosing columnset.

    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {'width': float}

    def run(self):
        # Preconditions:
        self.assert_has_content()
        # get width
        width = self.options.get('width')
        if width is not None:
            if (width <= 0.0) or (1.0 < width):
                raise self.error(
                    "columnset width '%f' must be between 0.0 and 1.0" %
                    width)
        # Main:
        # make columnset
        text = '\n'.join(self.content)
        col = column(text)
        col.width = width
        # parse content of column
        self.state.nested_parse(self.content, self.content_offset, col)
        # adjust widths
        # Postconditions & return:
        return [col]

directives.register_directive('beamer-column', ColumnDirective)


class NoteDirective(Directive):

    """A directive to include notes within a beamer presentation."""
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True
    option_spec = {}

    def run(self):
        # Preconditions:
        self.assert_has_content()
        # Main:
        # Preconditions:
        # make columnset
        text = '\n'.join(self.content)
        note_node = beamer_note(text)
        # parse content of note
        self.state.nested_parse(self.content, self.content_offset, note_node)
        # Postconditions & return:
        return [note_node]

directives.register_directive('beamer-note', NoteDirective)


class BeamerSection(Directive):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True

    def run(self):
        title = self.arguments[0]

        text_node = nodes.Text(title)
        text_nodes = [text_node]
        title_node = nodes.title(title, '', *text_nodes)
        name = normalize_name(title_node.astext())

        section_node = nodes.section(rawsource=self.block_text)
        section_node['names'].append(name)
        section_node += title_node
        messages = []
        title_messages = []
        section_node += messages
        section_node += title_messages
        section_node.tagname = 'beamer-section'
        return [section_node]

directives.register_directive('beamer-section', BeamerSection)


class OnlyBeamerDirective(Directive):

    r"""A directive that encloses its content in \only<beamer>{content} so that
    the content shows up in the presentation and not in the handouts or article
    version."""
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True
    option_spec = {'handouttext': str}

    def run(self):
        # Preconditions:
        self.assert_has_content()
        # get and check width of column set
        text = '\n'.join(self.content)
        only_beamer_set = onlybeamer(text)
        handouttext = self.options.get('handouttext', '')
        only_beamer_set.handouttext = handouttext
        # parse content of columnset
        self.state.nested_parse(self.content, self.content_offset,
                                only_beamer_set)
        # survey widths
        return [only_beamer_set]

directives.register_directive('onlybeamer', OnlyBeamerDirective)


class BlockDirective(Directive):

    r"""A directive that encloses its content in.

    \begin{block}{title}
       content
    \end{block}

    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True
    option_spec = {}

    def run(self):
        # Preconditions:
        self.assert_has_content()
        title = self.arguments[0]
        # get and check width of column set
        text = '\n'.join(self.content)
        body_set = block(text)
        # parse content of columnset
        self.state.nested_parse(self.content, self.content_offset,
                                body_set)
        # survey widths
        body_set.title = title
        return [body_set]

directives.register_directive('block', BlockDirective)


class BeamerTranslator(LaTeXTranslator):

    """A converter for docutils elements to beamer-flavoured latex."""

    def __init__(self, document):
        LaTeXTranslator.__init__(self, document)

        # Used for Beamer title and possibly header/footer. Set from docinfo
        # record the settings for codeblocks.
        self.organization = None
        self.cb_use_pygments = document.settings.cb_use_pygments
        self.cb_replace_tabs = document.settings.cb_replace_tabs
        self.cb_default_lang = document.settings.cb_default_lang

        self.head_prefix = [x for x in self.head_prefix
                            if '{typearea}' not in x]

        self.head_prefix.extend([
            '\\definecolor{rrblitbackground}{rgb}{0.55, 0.3, 0.1}\n',
            '\\newenvironment{rtbliteral}{\n',
            '\\begin{ttfamily}\n',
            '\\color{rrblitbackground}\n',
            '}{\n',
            '\\end{ttfamily}\n',
            '}\n',
        ])

        if self.cb_use_pygments:
            self.head_prefix.extend([
                '\\usepackage{fancyvrb}\n',
                '\\usepackage{color}\n',
            ])

        # set appropriate header options for theming
        theme = document.settings.theme
        if theme:
            self.head_prefix.append('\\usetheme{%s}\n' % theme)

        set_header_options(self.head_prefix, document.settings.shownotes)

        if self.cb_use_pygments:
            from pygments.formatters import LatexFormatter
            self.head_prefix.extend([
                LatexFormatter().get_style_defs(),
            ])

        self.overlay_bullets = string_to_bool(
            document.settings.overlaybullets, False)
        self.fragile_default = string_to_bool(
            document.settings.fragile_default,
            True)
        self.shortauthor = document.settings.shortauthor
        self.shorttitle = document.settings.shorttitle
        # using a False default because
        # True is the actual default. If you are trying to pass in a value
        # and I can't determine what you really meant, I am assuming you
        # want something other than the actual default.
        self.centerfigs = string_to_bool(
            document.settings.centerfigs,
            False)  # same reasoning as above
        self.in_columnset = False
        self.in_column = False
        self.in_note = False
        self.frame_level = 0

        # this fixes the hardcoded section titles in docutils 0.4
        self.d_class = DocumentClass('article')

        self.admonition_alert_type = None

    def depart_document(self, node):
        # Complete header with information gained from walkabout
        # a) conditional requirements (before style sheet)
        self.requirements = self.requirements.sortedvalues()
        # b) coditional fallback definitions (after style sheet)
        self.fallbacks = self.fallbacks.sortedvalues()
        # c) PDF properties
        self.pdfsetup.append(PreambleCmds.linking % self.hyperref_options)

        if self.pdfauthor:
            authors = self.author_separator.join(self.pdfauthor)
            self.pdfinfo.append('  pdfauthor={%s}' % authors)
        if self.pdfinfo:
            self.pdfsetup += [r'\hypersetup{'] + self.pdfinfo + ['}']
        # Complete body
        # a) document title (part 'body_prefix')
        # NOTE: Docutils puts author/date into docinfo, so normally
        #       we do not want LaTeX author/date handling (via \maketitle).
        #       To deactivate it, we add \title, \author, \date,
        #       even if the arguments are empty strings.
        if self.title or self.author_stack or self.date:
            authors = ['\\\\\n'.join(author_entry)
                       for author_entry in self.author_stack]
            title = [''.join(self.title)] + self.title_labels
            if self.shorttitle:
                shorttitle = self.shorttitle
            else:
                shorttitle = ''.join(self.title)
            if self.shortauthor:
                shortauthor = self.shortauthor
            else:
                shortauthor = ''.join(self.pdfauthor)

            if self.subtitle:
                title += [r'\\ % subtitle',
                          r'\large{%s}' % ''.join(self.subtitle)
                          ] + self.subtitle_labels
            docinfo_list = [shorttitle,
                            '%\n  '.join(title),
                            shortauthor,
                            ' \\and\n'.join(authors),
                            ', '.join(self.date)]
            if self.organization is None:
                docinfo_str = PreambleCmds.documenttitle % tuple(docinfo_list)
            else:
                docinfo_list.append(self.organization)
                docinfo_str = DOCINFO_W_INSTITUTE % tuple(docinfo_list)
            self.body_pre_docinfo.append(docinfo_str)
        # b) bibliography
        # TODO insertion point of bibliography should be configurable.
        if self._use_latex_citations and len(self._bibitems) > 0:
            if not self.bibtex:
                widest_label = ''
                for bib_item in self._bibitems:
                    if len(widest_label) < len(bib_item[0]):
                        widest_label = bib_item[0]
                self.out.append('\n\\begin{thebibliography}{%s}\n' %
                                widest_label)
                for bib_item in self._bibitems:
                    # cite_key: underscores must not be escaped
                    cite_key = bib_item[0].replace(r'\_', '_')
                    self.out.append('\\bibitem[%s]{%s}{%s}\n' %
                                    (bib_item[0], cite_key, bib_item[1]))
                self.out.append('\\end{thebibliography}\n')
            else:
                self.out.append('\n\\bibliographystyle{%s}\n' %
                                self.bibtex[0])
                self.out.append('\\bibliography{%s}\n' % self.bibtex[1])
        # c) make sure to generate a toc file if needed for local contents:
        if 'minitoc' in self.requirements and not self.has_latex_toc:
            self.out.append('\n\\faketableofcontents % for local ToCs\n')

    def visit_docinfo_item(self, node, name):
        if name == 'author':
            self.pdfauthor.append(self.attval(node.astext()))
        if self.use_latex_docinfo:
            if name in ('author', 'contact', 'address'):
                # We attach these to the last author. If any of them precedes
                # the first author, put them in a separate "author" group
                # (in lack of better semantics).
                if name == 'author' or not self.author_stack:
                    self.author_stack.append([])
                if name == 'address':   # newlines are meaningful
                    self.insert_newline = 1
                    text = self.encode(node.astext())
                    self.insert_newline = False
                else:
                    text = self.attval(node.astext())
                self.author_stack[-1].append(text)
                raise nodes.SkipNode
            elif name == 'date':
                self.date.append(self.attval(node.astext()))
                raise nodes.SkipNode
            elif name == 'organization':
                self.organization = node.astext()
                raise nodes.SkipNode

        self.out.append('\\textbf{%s}: &\n\t' % self.language_label(name))
        if name == 'address':
            self.insert_newline = 1
            self.out.append('{\\raggedright\n')
            self.context.append(' } \\\\\n')
        else:
            self.context.append(' \\\\\n')

    def visit_image(self, node):
        attrs = node.attributes
        if 'align' not in attrs and self.centerfigs:
            attrs['align'] = 'center'
        if (
            ('height' not in attrs) and
            ('width' not in attrs) and
            ('scale' not in attrs)
        ):
            attrs['height'] = '0.75\\textheight'
        LaTeXTranslator.visit_image(self, node)

    def depart_Text(self, node):
        pass

    def visit_section(self, node):
        if node.astext() == 'blankslide':
            # this never gets reached, but I don't know if that is bad
            self.out.append('\\begin{frame}[plain]{}\n\\end{frame}')
        else:
            if has_sub_sections(node):
                temp = self.section_level + 1
                if temp > self.frame_level:
                    self.frame_level = temp
            else:
                self.out.append(begin_frametag(node, self.fragile_default))
            LaTeXTranslator.visit_section(self, node)

    def depart_section(self, node):
        # Remove counter for potential subsections.
        LaTeXTranslator.depart_section(self, node)
        if self.section_level == self.frame_level:
            self.out.append(end_frametag())

    def visit_title(self, node):
        if node.astext() == 'dummy':
            raise nodes.SkipNode
        if isinstance(node.parent, nodes.admonition):
            assert self.admonition_alert_type
            self.out.append('\\begin{%s}{%s}\n' % (self.admonition_alert_type,
                                                   self.encode(node.astext())))
            raise nodes.SkipNode
        if node.astext() == 'blankslide':
            # A blankslide has no title, but is otherwise processed as normal,
            # meaning that the title is blank, but the slide can have some
            # content. It must at least contain a comment.
            raise nodes.SkipNode
        elif self.section_level == self.frame_level + 1:
            self.out.append('\\frametitle{%s}\n\n' %
                            self.encode(node.astext()))
            raise nodes.SkipNode
        else:
            LaTeXTranslator.visit_title(self, node)

    def depart_title(self, node):
        if self.section_level != self.frame_level + 1:
            LaTeXTranslator.depart_title(self, node)

    def visit_literal_block(self, node):
        # FIXME: the purpose of this method is unclear, but it causes parsed
        # literals in docutils 0.6 to lose indenting. Thus we've solve the
        # problem be just getting rid of it. [PMA 20091020]
        # TODO: replace leading tabs like in codeblocks?
        if node_has_class(node, 'code-block') and self.cb_use_pygments:
            self.visit_codeblock(node)
        else:
            self.out.append('\\setbeamerfont{quote}{parent={}}\n')
            LaTeXTranslator.visit_literal_block(self, node)

    def depart_literal_block(self, node):
        # FIXME: see `visit_literal_block`
        if node_has_class(node, 'code-block') and self.cb_use_pygments:
            self.visit_codeblock(node)
        else:
            LaTeXTranslator.depart_literal_block(self, node)
            self.out.append('\\setbeamerfont{quote}{parent=quotation}\n')

    def visit_codeblock(self, node):
        # Was langauge argument defined on node?
        lang = node.get('language')
        # Otherwise, was it defined in node classes?
        if lang is None:
            lang = node_lang_class(node)
        # Otherwise, use commandline argument or default
        if lang is None:
            lang = self.cb_default_lang
        # Replace tabs if required.
        srccode = node.rawsource
        if self.cb_replace_tabs:
            srccode = '\n'.join(
                adjust_indent_spaces(x, new_width=self.cb_replace_tabs)
                for x in srccode.split('\n'))
        self.out.append('\n' + highlight_code(srccode, lang) + '\n')
        raise nodes.SkipNode

    def depart_codeblock(self, node):
        pass

    def visit_bullet_list(self, node):
        begin_str = '\\begin{itemize}'
        if self.node_overlay_check(node):
            begin_str += '[<+-| alert@+>]'
        begin_str += '\n'
        self.out.append(begin_str)

    def node_overlay_check(self, node):
        """Assuming that the bullet or enumerated list is the child of a slide,
        check to see if the slide has either nooverlay or overlay in its
        classes.

        If not, default to the commandline specification for
        overlaybullets.

        """
        if 'nooverlay' in node.parent.attributes['classes']:
            return False
        elif 'overlay' in node.parent.attributes['classes']:
            return True
        else:
            return self.overlay_bullets

    def depart_bullet_list(self, node):
        self.out.append('\\end{itemize}\n')

    def visit_enumerated_list(self, node):
        # LaTeXTranslator has a very complicated
        # visit_enumerated_list that throws out much of what latex
        # does to handle them for us. I am going back to relying
        # on latex.
        begin_str = '\\begin{enumerate}'
        if self.node_overlay_check(node):
            begin_str += '[<+-| alert@+>]'
        begin_str += '\n'
        self.out.append(begin_str)
        if 'start' in node:
            self.out.append('\\addtocounter{enumi}{%d}\n'
                            % (node['start'] - 1))

    def depart_enumerated_list(self, node):
        self.out.append('\\end{enumerate}\n')

    def visit_columnset(self, _):
        assert not self.in_columnset, \
            'already in column set, which cannot be nested'
        self.in_columnset = True
        self.out.append('\\begin{columns}[T]\n')

    def depart_columnset(self, _):
        assert self.in_columnset, 'not in column set'
        self.in_columnset = False
        self.out.append('\\end{columns}\n')

    def visit_column(self, node):
        assert not self.in_column, 'already in column, which cannot be nested'
        self.in_column = True
        self.out.append('\\column{%.2f\\textwidth}\n' % node.width)

    def depart_column(self, _):
        self.in_column = False
        self.out.append('\n')

    def visit_beamer_note(self, _):
        assert not self.in_note, 'already in note, which cannot be nested'
        self.in_note = True
        self.out.append('\\note{\n')

    def depart_beamer_note(self, _):
        self.in_note = False
        self.out.append('}\n')

    def visit_onlybeamer(self, node):
        if node.handouttext:
            self.out.append('\\only<handout>{%s}\n' % node.handouttext)
        self.out.append('\\only<beamer>{\n')

    def depart_onlybeamer(self, _):
        self.out.append('}\n')

    def visit_block(self, node):
        if hasattr(node, 'title'):
            title = node.title
        else:
            title = ''
        self.out.append('\\begin{block}{%s}\n' % title)

    def depart_block(self, _):
        self.out.append('\\end{block}\n')

    def visit_admonition(self, node):
        self.fallbacks['admonition'] = PreambleCmds.admonition
        if 'error' in node['classes']:
            self.fallbacks['error'] = PreambleCmds.error
        myclass = get_admonition_class(node)

        self.admonition_alert_type = get_alertblock_type(myclass)

    def depart_admonition(self, node=None):
        assert self.admonition_alert_type
        self.out.append('\\end{%s}\n' % self.admonition_alert_type)
        self.admonition_alert_type = None

    def visit_container(self, node):
        """Handle containers with 'special' names, ignore the rest."""
        # NOTE: theres something weird here where ReST seems to translate
        # underscores in container identifiers into hyphens. So for the
        # moment we'll allow both.
        if node_has_class(node, 'beamer-simplecolumns'):
            self.visit_columnset(node)
            wrap_children_in_columns(node, node.children)
        elif node_has_class(node, 'beamer-note'):
            self.visit_beamer_note(node)
        else:
            # currently the LaTeXTranslator does nothing, but just in case
            LaTeXTranslator.visit_container(self, node)

    def depart_container(self, node):
        if node_has_class(node, 'beamer-simplecolumns'):
            self.depart_columnset(node)
        elif node_has_class(node, 'beamer-note'):
            self.depart_beamer_note(node)
        else:
            # currently the LaTeXTranslator does nothing, but just in case
            LaTeXTranslator.depart_container(self, node)

    def unimplemented_visit(self, node):
        assert False


def node_fragile_check(node, fragile_default):
    """Check whether or not a slide should be marked as fragile.

    If the slide has class attributes of fragile or notfragile, then
    the document default is overridden.

    """
    if 'notfragile' in node.attributes['classes']:
        return False
    elif 'fragile' in node.attributes['classes']:
        return True
    else:
        return fragile_default


def begin_frametag(node, fragile_default):
    bf_str = '\n\\begin{frame}'
    if node_fragile_check(node, fragile_default):
        bf_str += '[fragile]'
    bf_str += '\n'
    return bf_str


def end_frametag():
    return '\n\\end{frame}\n'


def get_admonition_class(node):
    """Return the stripped generic 'admonition' from the list of classes."""
    filt_classes = [cls for cls in node['classes'] if cls != 'admonition']
    assert len(filt_classes) == 1
    # I think docutils lowers anyways, but just to be sure.
    myclass = filt_classes[0].lower()
    return myclass


def get_alertblock_type(myclass):
    alertlist = ['attention', 'caution', 'danger', 'error', 'warning']
    if myclass in alertlist:
        env = 'alertblock'
    else:
        env = 'block'
    return env


def set_header_options(head_prefix, shownotes):
    """Set appropriate header options for note display."""
    if shownotes == SHOWNOTES_TRUE:
        shownotes = SHOWNOTES_RIGHT
    use_pgfpages = True
    if shownotes == SHOWNOTES_FALSE:
        option_str = 'hide notes'
        use_pgfpages = False
    elif shownotes == SHOWNOTES_ONLY:
        option_str = 'show only notes'
    else:
        if shownotes == SHOWNOTES_LEFT:
            notes_posn = 'left'
        elif shownotes in SHOWNOTES_RIGHT:
            notes_posn = 'right'
        elif shownotes == SHOWNOTES_TOP:
            notes_posn = 'top'
        elif shownotes == SHOWNOTES_BOTTOM:
            notes_posn = 'bottom'
        else:
            # TODO: better error handling
            assert False, "unrecognised option for shownotes '{}'".format(
                shownotes)
        option_str = 'show notes on second screen=%s' % notes_posn
    if use_pgfpages:
        head_prefix.append('\\usepackage{pgfpages}\n')
    head_prefix.append('\\setbeameroption{%s}\n' % option_str)


class BeamerWriter(Latex2eWriter):

    """A docutils writer that produces Beamer-flavoured LaTeX."""
    settings_spec = BEAMER_SPEC
    settings_default_overrides = BEAMER_DEFAULT_OVERRIDES

    def __init__(self):
        self.settings_defaults.update(BEAMER_DEFAULTS)
        Latex2eWriter.__init__(self)
        self.translator_class = BeamerTranslator


def main():
    description = (
        'Generates Beamer-flavoured LaTeX for PDF-based presentations. ' +
        default_description)

    publish_cmdline(
        writer=BeamerWriter(),
        description=description,
        settings_overrides={'halt_level': utils.Reporter.ERROR_LEVEL})


if __name__ == '__main__':
    main()
