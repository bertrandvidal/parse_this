#!/bin/bash

# test in python 2.7
function test_python_version(){
  ENV_PATH=$1
  PY_VERSION=$2
  if [ ! -d "${ENV_PATH}" ]; then
    virtualenv --prompt="(parse_this_${PY_VERSION})" --python=python"${PY_VERSION}" "${ENV_PATH}"
  fi
  source "${ENV_PATH}"/bin/activate
  python -m unittest discover -p "*_test.py"
}

test_python_version "env_27" "2.7"
test_python_version "env_39" "3.9"
