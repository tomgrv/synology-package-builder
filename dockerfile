# Docker file to start unbuntu with python3.6 in privileged mode
FROM ubuntu

# Install python3
RUN apt-get update && apt-get install -y python3 python3-pip git cifs-utils

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY build /build

# Ensure build script is executable
RUN chmod +x /build

# Code file to execute when the docker container starts up (`build.sh`)
ENTRYPOINT ["/build"]
