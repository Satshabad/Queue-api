test:
	nosetests ${SINGLETEST} --nocapture -i '^(it|ensure|must|should|specs?|examples?|deve)' -i '(specs?(.py)?|examples?(.py)?)' '--with-spec' '--spec-color'

.PHONY: test test-watch
