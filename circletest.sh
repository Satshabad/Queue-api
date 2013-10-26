#!/bin/bash

i=0
files=()
for file in $(find ./tests -name "*.py")
do
  if [ $(($i % $CIRCLE_NODE_TOTAL)) -eq $CIRCLE_NODE_INDEX ]
  then
    files+=" $file"
  fi
  ((i++))
done

QUEUE_API_MODE="TEST" \
nosetests ${SINGLETEST} --nocapture -i '^(it|ensure|must|should|specs?|examples?|deve)' -i '(specs?(.py)?|examples?(.py)?)' '--with-spec' '--spec-color' ${files[@]}


