#!/bin/bash -ex

./rst2beamer.py test/simple_slide_test.rst .tmp.tex
diff test/simple_slide_test_expected.tex .tmp.tex
rm -f .tmp.tex
