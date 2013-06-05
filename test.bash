#!/bin/bash -ex

for base in figure_centering_test \
            hyperlink_color \
            overlay_test \
            sectioning_test \
            simple_slide_test
do
    ./rst2beamer.py test/$base.rst .tmp.tex
    diff test/${base}_expected.tex .tmp.tex
    rm -f .tmp.tex
done
