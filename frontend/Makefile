PY=python
PORT=8501

install:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate && streamlit run dashboard.py --server.port $(PORT)
