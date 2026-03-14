FROM debian:bullseye-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    ca-certificates \
    && wget -O - https://files.freeswitch.org/repo/deb/debian-release/fsstretch-archive-keyring.asc | apt-key add - \
    && echo "deb https://files.freeswitch.org/repo/deb/debian-release/ bullseye main" > /etc/apt/sources.list.d/freeswitch.list \
    && apt-get update && apt-get install -y \
    freeswitch-meta-all \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY freeswitch/dialplan/*.xml /etc/freeswitch/dialplan/
COPY freeswitch/sip_profiles/*.xml /etc/freeswitch/sip_profiles/
COPY freeswitch/autoload_configs/*.xml /etc/freeswitch/autoload_configs/

EXPOSE 5060/udp 5060/tcp 8021 16384-32768/udp

CMD ["/usr/bin/freeswitch", "-nonat", "-nc"]
