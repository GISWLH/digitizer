.PHONY: test benchmark flux ai check showcase
test:
	python -m pytest -q
benchmark:
	python scripts/benchmark.py --ablation --require-90
flux:
	python scripts/validate_flux.py
ai:
	python scripts/validate_ai.py --require-90
check: test benchmark flux ai
	python scripts/validate_paper.py
showcase:
	python scripts/build_showcase.py
	python scripts/build_ai_showcase.py
