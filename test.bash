#!/bin/bash -ex

trap "echo -e '\x1b[01;31mFailed\x1b[0m'" ERR

if [ "$TRAVIS_PYTHON_VERSION" != "2.7" ]
then
    python -m doctest rst2beamer.py
fi

RST2BEAMER=( \
    ./rst2beamer.py \
    --traceback --theme=Warsaw --overlaybullets=1 \
    --no-codeblocks-use-pygments \
)

for expected in test/*_expected.tex
do
    base=$(basename "$expected" '_expected.tex')
    "${RST2BEAMER[@]}" "test/$base.rst" .tmp.tex
    diff --unified "$expected" .tmp.tex
    rm -f .tmp.tex
done

# Adhoc tests.
"${RST2BEAMER[@]}" --language=de 'test/warning_test.rst' .tmp.tex
diff --unified 'test/warning_test_expected.de.tex' .tmp.tex
rm -f .tmp.tex

echo -e '\x1b[01;32mOkay\x1b[0m'
