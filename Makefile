PYTHON ?= python3

.PHONY: start stop add-skill logs test lint typecheck dashboard

start:
	uvicorn api.main:app --host 0.0.0.0 --port 8000

stop:
	@echo "Use your process manager to stop Jarvis services."

add-skill:
	@echo "Create a new module under skills/<domain>/ and export a BaseSkill subclass."

logs:
	@echo "Tail logs under data/logs once runtime logging is enabled."

test:
	$(PYTHON) -m pytest --cov=core --cov=llm --cov=skills --cov=api

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy .

dashboard:
	cd dashboard && pnpm dev

