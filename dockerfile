# Docker file to start unbuntu with python3.6 in privileged mode
FROM ubuntu

# Install python3
RUN apt-get update && apt-get install -y python3 python3-pip git cifs-utils jq

# Copies build scripts to the root of the container
COPY build* /

# Copies stubs to the root of the container
COPY stubs /stubs

# Ensure build script is executable
RUN chmod +x /build*

# Code file to execute when the docker container starts up (`build`)
ENTRYPOINT ["/build"]
