.PHONY: test benchmark flux check showcase
test:
	python -m pytest -q
benchmark:
	python scripts/benchmark.py --ablation --require-90
flux:
	python scripts/validate_flux.py
check: test benchmark flux
	python scripts/validate_paper.py
showcase:
	python scripts/build_showcase.py
