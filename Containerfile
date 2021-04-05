FROM docker.io/python:3.9-alpine as builder
COPY . /app
WORKDIR /app
RUN pip install setuptools wheel \
    && python setup.py sdist bdist_wheel


FROM docker.io/python:3.9-alpine
LABEL maintainer="Odd Stråbø <oddstr13@openshell.no>, k3rnelpan1c-dev <k3rnelpan1c-dev@pm.me>" \
    description="Jellyfin Plugin Repository Manager" version="0.4.0" \
    source="https://github.com/oddstr13/jellyfin-plugin-repository-manager"
COPY --from=builder /app/dist/* /opt/jprm/
WORKDIR /opt/jprm/
RUN pip install ./*.whl \
    && adduser -u 111111 -s /bin/sh -HD jrpm jrpm
USER jprm
ENTRYPOINT [ "jrpm" ]
