pre-commit:
	pre-commit run --all-files

test:
	poetry run pytest tests/pytest_tests/ -v

new-release:
	twine upload dist/*