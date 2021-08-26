# use python package as base
FROM python:3.9-slim
ARG GITHUB_TOKEN
ARG PYPI_URL=https://${GITHUB_TOKEN}@pypi.data.vanoord.com/

# upgrade packages
RUN apt update && apt install -y git procps
RUN pip install --upgrade pip

# install python package
WORKDIR /breakwater
ADD . /breakwater
RUN pip install -e . --extra-index-url https://$GITHUB_TOKEN@pypi.data.vanoord.com/

EXPOSE 8888

CMD ["sh", "-c", "tail -f /dev/null"]