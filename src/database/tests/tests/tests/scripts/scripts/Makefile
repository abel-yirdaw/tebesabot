# Makefile for Habesha Dating Bot

.PHONY: help install run test deploy clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run bot locally"
	@echo "  make test       - Run tests"
	@echo "  make deploy     - Deploy to Vercel"
	@echo "  make clean      - Clean temporary files"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

run:
	python main.py

test:
	pytest tests/ -v --cov=src

deploy:
	./scripts/deploy.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov