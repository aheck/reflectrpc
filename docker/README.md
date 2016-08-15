# Release Testing #

This directory contains docker images for testing releases of ReflectRPC. They
install the newest release form PyPI along a Python 2.7 or 3.5 environment. When
you run these images they run the ReflectRPC test suite against the installed PyPI
release of ReflectRPC.

The purpose of those images is to test each release to make sure the latest
ReflectRPC version on PyPI works as expected.

## Usage ##

```bash
./build.sh
docker run <IMGID>
echo $?
```

The output will be 0 if all tests ran successfully. If not check the output for
what went wrong.
