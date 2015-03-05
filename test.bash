#!/bin/bash -ex

trap "echo -e '\x1b[01;31mFailed\x1b[0m'" ERR

if [ "$TRAVIS_PYTHON_VERSION" != "2.7" ]
then
    python -m doctest rst2beamer.py
fi

for expected in test/*_expected.tex
do
    base=$(basename "$expected" '_expected.tex')
    ./rst2beamer.py \
        --traceback \
        --no-codeblocks-use-pygments "test/$base.rst" .tmp.tex
    diff --unified "$expected" .tmp.tex
    rm -f .tmp.tex
done

# Adhoc tests.
./rst2beamer.py \
    --language=de \
    --traceback \
    --no-codeblocks-use-pygments 'test/warning_test.rst' .tmp.tex
diff --unified 'test/warning_test_expected.de.tex' .tmp.tex
rm -f .tmp.tex

echo -e '\x1b[01;32mOkay\x1b[0m'
