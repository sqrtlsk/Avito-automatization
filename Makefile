VENV = .Avito_venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

SCRIPT = Avito_views_daily.py

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

google:
	/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
      --remote-debugging-port=9222 \
      --user-data-dir="$$HOME/chrome-remote-profile" \
	  > /dev/null 2>&1 & disown

run:
	$(PYTHON) $(SCRIPT)

all:
	make setup
	(make google &) && make run