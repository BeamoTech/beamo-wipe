.PHONY: test iso demo preview preview-web lint cloud-test legacy-cloud-test

test:
	python3 -m pytest

iso:
	./scripts/build-iso.sh

# Retained compatibility alias; not the approved Blacksmith CI gate.
cloud-test legacy-cloud-test:
	@printf 'Legacy Cloud Build submission; separate authorization required. See docs/development.md.\n'
	./scripts/ci-cloud.sh

demo preview:
	./preview

preview-web:
	./preview --web
