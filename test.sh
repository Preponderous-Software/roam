# /bin/bash
# Usage: ./test.sh

# generate coverage file named "cov.xml"
python -m pytest --verbose -vv --cov=src --cov-report=term-missing --cov-report=xml:cov.xml