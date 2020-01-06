
FROM alpine:3.10 as builder

LABEL maintainer="sola97 <my@sora.vip> "

ENV RINETD_BBR_POWERED_DOWNLOAD_URL https://github.com/linhua55/lkl_study/releases/download/v1.2/rinetd_bbr_powered
ENV RINETD_BBR_DOWNLOAD_URL https://github.com/linhua55/lkl_study/releases/download/v1.2/rinetd_bbr
ENV RINETD_PCC_DOWNLOAD_URL https://github.com/linhua55/lkl_study/releases/download/v1.2/rinetd_pcc


WORKDIR /

RUN  apk update && \
    apk add --no-cache git  build-base linux-headers wget && \
    git clone https://github.com/wangyu-/udp2raw-tunnel.git  && \
    cd udp2raw-tunnel && \
    make dynamic && \
    mv udp2raw_dynamic /bin/udp2raw && \
    cd / && \
    git clone https://github.com/wangyu-/UDPspeeder.git && \
    cd UDPspeeder && \
    make && \
    install speederv2 /bin && \
    wget ${RINETD_BBR_POWERED_DOWNLOAD_URL} -O /bin/rinetd-bbr-powered && \
    wget ${RINETD_BBR_DOWNLOAD_URL} -O /bin/rinetd-bbr && \ 
    wget ${RINETD_PCC_DOWNLOAD_URL} -O /bin/rinetd-pcc && \ 
    chmod +x /bin/rinetd-*


FROM mritd/shadowsocks:3.3.3-20191229

SHELL ["/bin/bash", "-c"]

RUN apk update && \
    apk add --no-cache libstdc++ iptables && \
    rm -rf /var/cache/apk/* && \
    mkdir -p /etc/v2ray/ && \
    touch /etc/v2ray/v2ray.crt && \
    touch /etc/v2ray/v2ray.key
COPY --from=builder /bin/udp2raw /usr/bin
COPY --from=builder /bin/speederv2 /usr/bin
COPY --from=builder /bin/rinetd-bbr /usr/bin
COPY --from=builder /bin/rinetd-bbr-powered /usr/bin
COPY --from=builder /bin/rinetd-pcc /usr/bin

COPY runit /etc/service
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
