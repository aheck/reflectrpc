#!/bin/bash

cp -r ../../examples .
cp -r ../../tests .
cp ../../runtests.py .

docker build -t 'reflectrpc-test:python2.7' .

rm -rf examples
rm -rf tests
rm runtests.py
