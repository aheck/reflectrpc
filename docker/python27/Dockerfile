#
# Build this dockerfile with ./build.sh
#
# It runs the ReflectRPC unit tests against the latest ReflectRPC version
# available on PyPI
#
# After this image ran the shell variable $? should be 0 otherwise the tests
# failed
#
FROM ubuntu:16.04
MAINTAINER Andreas Heck "aheck@gmx.de"

RUN apt-get update && apt-get install -y \
  python \
  python-pip \
  gcc \
  libssl-dev \
  libssl1.0.0 \
  libffi-dev \
  libffi6
RUN pip install reflectrpc pexpect
RUN mkdir /tmp/reflectrpc-test
RUN cp `which rpcsh` /tmp/reflectrpc-test
RUN cp `which rpcdoc` /tmp/reflectrpc-test
RUN cp `which rpcgencode` /tmp/reflectrpc-test

ADD ./examples /tmp/reflectrpc-test/examples
ADD ./tests /tmp/reflectrpc-test/tests
ADD ./runtests.py /tmp/reflectrpc-test

WORKDIR /tmp/reflectrpc-test
CMD python runtests.py
