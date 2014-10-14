==========
rst2beamer
==========

.. image:: https://travis-ci.org/myint/rst2beamer.svg?branch=master
    :target: https://travis-ci.org/myint/rst2beamer
    :alt: Build status


Introduction
============

A docutils script converting reStructuredText into Beamer-flavoured LaTeX.

Beamer is a LaTeX document class for presentations. rst2beamer
provides a docutils writer that transforms reStructuredText
into Beamer-flavoured LaTeX and provides a command-line script for the
same. Via this script, reStructuredText can therefore be used to prepare slides
and presentations.

This is an unofficial fork (of https://pypi.python.org/pypi/rst2beamer) that
runs on both Python 2 and 3.


Installation
============

Using ``pip``::

    $ pip install --upgrade rst2beamer3k

Beamer dependency
-----------------

On MacPorts::

    $ sudo port install texlive-latex -x11 texlive-fonts-recommended -x11


Usage
=====

rst2beamer should interpret a reasonable subset of reStructuredText and
produce reasonable LaTeX. Not all features of Beamer have been implemented,
just a (large) subset that allows the quick production of good looking slides.
These include:

* Overlay lists (i.e. list items that appear point-by-point).
* Beamer themes.
* Automatic centering and resizing of figures.
* Embedded notes and the output of note slides.
* Arranging slide contents into columns.

Some examples can be found in the ``docs/examples`` directory of the
distribution. In practice, rst2beamer can be used with ``pdflatex`` to get PDF
versions of a presentation.

rst2beamer is called::

    $ rst2beamer [options] [<source> [<destination>]]

For example::

    $ rst2beamer infile.txt outfile.tex

``infile.txt`` contains the reStructuredText and ``outfile.tex`` contains the
produced Beamer LaTeX.

It supports the usual docutils and LaTeX writer (``rst2latex``) options, save
the ``documentclass`` option (which is fixed to ``beamer``) and ``hyperref``
options (which are already set in Beamer). It also supports::

    --theme=THEME           Specify Beamer theme.
    --overlaybullets=OVERLAYBULLETS
                            Overlay bulleted items. Put [<+-| alert@+>] at the
                            end of \begin{itemize} so that Beamer creats an
                            overlay for each bulleted item and the presentation
                            reveals one bullet at a time
    --centerfigs=CENTERFIGS
                            Center figures.  All includegraphics statements will
                            be put inside center environments.
    --documentoptions=DOCUMENTOPTIONS
                            Specify document options. Multiple options can be
                            given, separated by commas.  Default is
                            "10pt,a4paper".
    --shownotes=SHOWNOTES   Print embedded notes along with the slides. Possible
                            arguments include 'false' (don't show), 'only' (show
                            only notes), 'left', 'right', 'top', 'bottom' (show
                            in relation to the annotated slide).


Limitations
===========

Earlier versions of rst2beamer did not work with docutils 0.4, seemingly due
to changes in the LaTeX writer. While this has been fixed, most work has been
done with docutils snapshots from version 0.5 and up. In balance, users are
recommended to update docutils.

More recently, changes in the LaTeX writer in docutils 0.6 broke rst2beamer
again. We think all those bugs have been caught.

Not all features of Beamer are supported, and some - that deal with with page
layout or presentation - may never be. Introducing complex syntax to achieve
complex and specific page effects defeats the point of reStructuredText's
simple and easy-to-write format. If you need a complex presentation, use
PowerPoint or Keynote.

If the content for an individual slide is too large, it will simply overflow
the edges of the slide and disappear. Arguably, this is a sign you should put
less on each slide.


Credits
=======

rst2beamer is developed by `Ryan Krauss <ryanwkrauss@gmail.com>`__ and
`Paul-Michael Agapow <agapow@bbsrc.ac.uk>`__. Thanks to those who reported and
helped us track down bugs: Perttu Laurinen, Mike Pennington, James Haggerty
and Dale Hathaway.
