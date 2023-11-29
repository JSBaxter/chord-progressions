test:
	@echo "Running all tests..."
	@python -m pytest tests

test-ugscraper:
	@echo "Running scraper tests..."
	@python -m pytest tests/ugscraper

test-ugscraper-coverage:
	@echo "Running scraper tests with coverage..."
	@python -m pytest --cov=ugscraper tests/ugscraper
