#!/bin/bash

cp -r ../../examples .
cp -r ../../tests .
cp ../../runtests.py .

docker build -t 'reflectrpc-test:python3.5' .

rm -rf examples
rm -rf tests
rm runtests.py
