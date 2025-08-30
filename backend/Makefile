PY=python
PORT=8000

install:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate && FLASK_APP=app.py FLASK_ENV=development flask run -p $(PORT)

test:
	. .venv/bin/activate && pytest -q

fmt:
	. .venv/bin/activate && python -m pip install ruff && ruff check --fix .

clean:
	rm -rf .venv
	rm -f prime_coherence.db
	rm -rf artifacts/*
