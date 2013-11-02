#!/bin/bash -ex

if [ "$TRAVIS_PYTHON_VERSION" != "2.7" ]
then
    python -m doctest rst2beamer.py
fi

for expected in test/*_expected.tex
do
    base=$(basename "$expected" '_expected.tex')
    ./rst2beamer.py --no-codeblocks-use-pygments "test/$base.rst" .tmp.tex
    diff --unified "$expected" .tmp.tex
    rm -f .tmp.tex
done

echo -e '\x1b[01;32mOkay\x1b[0m'
