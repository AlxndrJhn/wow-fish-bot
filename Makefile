.PHONY: format static test
format:
	black src
	black tests

static:
	mypy src
	pydocstyle src
	flake8
	black --check src
	black --check tests

test:
	pytest -s -vvv -m "not slow"
	pytest -s -vvv tests/pubsub/test_pubsub.py::test_main

emulator:
	docker run --name pubsub -it --rm -p 8538:8538 -d \
		bigtruedata/gcloud-pubsub-emulator \
		start --data-dir=/data --host-port=0.0.0.0:8538 \
			  --log-http --verbosity=debug --user-output-enabled
