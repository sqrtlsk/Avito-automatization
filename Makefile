VENV = .Avito_venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

SCRIPT_1 = Avito_views_daily.py
SCRIPT_2 = Avito_all_ad_info.py

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

google:
	/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
      --remote-debugging-port=9222 \
      --user-data-dir="$$HOME/chrome-remote-profile" \
	  > /dev/null 2>&1 & disown

run_1:
	$(PYTHON) $(SCRIPT_1)

run_2:
	$(PYTHON) $(SCRIPT_2)

all_views:
	make setup
	make google
	make run_1

all_data:
	make setup
	(make google &) && make run_2
