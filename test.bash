#!/bin/bash -ex

for expected in test/*_expected.tex
do
    base=$(basename "$expected" '_expected.tex')
    ./rst2beamer.py "test/$base.rst" .tmp.tex
    diff "$expected" .tmp.tex
    rm -f .tmp.tex
done
