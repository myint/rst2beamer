check:
	pep8 rst2beamer.py
	pyflakes rst2beamer.py
	pylint \
		--reports=no \
		--max-module-lines=2500 \
		--disable=bad-continuation \
		--disable=fixme \
		--disable=invalid-name \
		--disable=missing-docstring \
		--disable=no-name-in-module \
		--disable=star-args \
		--disable=too-few-public-methods \
		--disable=too-many-branches \
		--disable=too-many-instance-attributes \
		--disable=too-many-public-methods \
		--rcfile=/dev/null rst2beamer.py
	check-manifest
