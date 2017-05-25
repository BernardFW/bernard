#!/bin/sh

export PYTHONPATH=$PYTHONPATH:$TRAVIS_BUILD_DIR/src
pytest
