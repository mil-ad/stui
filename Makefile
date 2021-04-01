.PHONY: dist
dist:
	python setup.py sdist bdist_wheel

.PHONY: upload
upload: dist
	twine upload --skip-existing dist/*
