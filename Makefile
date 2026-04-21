PYTHON ?= python

.PHONY: start start-dev stop test lint typecheck dashboard install-models voice-test memory-clear memory-stats browser-check add-skill logs

start:
	@echo "[jarvis] Starting Ollama + API"
	@start /b ollama serve
	@timeout /t 2 /nobreak >nul
	uvicorn api.main:app --host 0.0.0.0 --port 8000

start-dev:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

stop:
	@echo "[jarvis] Stopping Jarvis services"
	@taskkill /f /im uvicorn.exe 2>nul || true

install-models:
	bash scripts/install_models.sh

voice-test:
	$(PYTHON) -c "from voice.stt import SpeechToTextService; import asyncio; print(asyncio.run(SpeechToTextService().health_check()))"

memory-clear:
	@echo "[jarvis] Clearing ChromaDB"
	@rmdir /s /q data\chroma 2>nul || true
	@mkdir data\chroma
	@echo "Memory cleared."

memory-stats:
	$(PYTHON) -c "from llm.memory.chroma_store import ChromaMemoryStore; from core.config import AppSettings; from llm.ollama_client import OllamaClient; settings = AppSettings.load(); client = OllamaClient(settings); store = ChromaMemoryStore(settings, client); import asyncio; print(f'Docs: {asyncio.run(store.count())}')"

browser-check:
	$(PYTHON) -c "from skills.browser.windows_browser import get_default_browser_name, get_default_browser_path; print(f'Browser: {get_default_browser_name()}'); print(f'Path: {get_default_browser_path()}')"

add-skill:
	@echo "Create a new module under skills/<domain>/ and export a BaseSkill subclass."
	@echo "Then register it in skills/loader.py"

logs:
	@if exist data\logs (type data\logs\*.log 2>nul || echo "No log files yet.") else (echo "Logs dir not found.")

test:
	$(PYTHON) -m pytest --cov=core --cov=llm --cov=skills --cov=api -v

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy .

dashboard:
	cd dashboard && pnpm dev
