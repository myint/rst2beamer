check:
	pep8 rst2beamer.py
	pyflakes rst2beamer.py
	pylint \
		--reports=no \
		--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}' \
		--max-module-lines=2500 \
		--disable=C0103,C0111,E0611,R0201,R0902,R0904,R0912,W0142,W0201,W0223,W0511,W0703 \
		--disable=bad-continuation \
		--rcfile=/dev/null rst2beamer.py
	check-manifest
