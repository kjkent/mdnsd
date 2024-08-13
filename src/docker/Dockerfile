# syntax=docker/dockerfile:1.7-labs

ARG TMPDIR=/tmp/dmr-build/

# ----------------------[ Stage 1 ]---------------------------------
FROM alpine AS build
ARG TMPDIR

# Build from GitHub repo
# ----------------------
# ARG REPO="https://github.com/kjkent/docker-mdns-repeater.git"
# ADD "${REPO}" "${TMPDIR}"
# ----------------------

# Build from local project
# ------------------------
COPY mdns-repeater.c "${TMPDIR}"
COPY --from=project-root --parents=true **/* "${TMPDIR}"
# ------------------------

RUN apk add build-base git
RUN make --directory "${TMPDIR}"

# ----------------------[ Stage 2 ]---------------------------------
FROM alpine
ARG TMPDIR

COPY --from=build --chmod=0751 "${TMPDIR}"/build/mdns-repeater /bin/

RUN apk add --no-cache libcap-setcap python3
RUN setcap cap_net_raw=+ep /bin/mdns-repeater

ENTRYPOINT ["/bin/mdns-repeater", "-f"]
CMD ["-h"]
