.PHONY: backend-install frontend-install backend-dev frontend-dev backend-test frontend-test frontend-build

backend-install:
	pip install -e .[dev]

frontend-install:
	cd frontend && npm install

backend-dev:
	uvicorn backend.main:app --reload

frontend-dev:
	cd frontend && npm run dev

backend-test:
	pytest

frontend-test:
	cd frontend && npm test

frontend-build:
	cd frontend && npm run build
