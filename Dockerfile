FROM alpine:3.10 as builder

WORKDIR /

RUN  apk update && \
    apk add --no-cache git  build-base linux-headers && \
    git clone https://github.com/wangyu-/udp2raw-tunnel.git  && \
    cd udp2raw-tunnel && \
    make dynamic && \
    mv udp2raw_dynamic /bin/udp2raw && \
    cd / && \
    git clone https://github.com/wangyu-/UDPspeeder.git && \
    cd UDPspeeder && \
    make && \
    install speederv2 /bin



FROM mritd/shadowsocks:3.3.3-20191101

SHELL ["/bin/bash", "-c"]

RUN apk update && \
    apk add --no-cache libstdc++ iptables && \
    rm -rf /var/cache/apk/* && \
    adduser -h /tmp -s /sbin/nologin -S -D -H udp2raw && \
    adduser -h /tmp -s /sbin/nologin -S -D -H udpspeeder
COPY --from=builder /bin/udp2raw /usr/bin
COPY --from=builder /bin/speederv2 /usr/bin
COPY runit /etc/service
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]