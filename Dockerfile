FROM alpine:3.9

LABEL maintainer="sola97"

ARG TZ='Asia/Shanghai'

ENV TZ ${TZ}
ENV SS_LIBEV_VERSION v3.2.5
ENV KCP_VERSION 20190611
ENV UDPSPEEDER_VERSION 20190121.0
ENV SS_DOWNLOAD_URL https://github.com/shadowsocks/shadowsocks-libev.git 
ENV OBFS_DOWNLOAD_URL https://github.com/shadowsocks/simple-obfs.git
ENV V2RAY_PLUGIN_DOWNLOAD_URL https://github.com/shadowsocks/v2ray-plugin/releases/download/v1.0/v2ray-plugin-linux-amd64-8cea1a3.tar.gz
ENV KCP_DOWNLOAD_URL https://github.com/xtaci/kcptun/releases/download/v${KCP_VERSION}/kcptun-linux-amd64-${KCP_VERSION}.tar.gz
ENV UDPSPEEDER_DOWNLOAD_URL https://github.com/wangyu-/UDPspeeder/releases/download/${UDPSPEEDER_VERSION}/speederv2_binaries.tar.gz
ENV UDP2RAW_DOWNLOAD_URL https://github.com/wangyu-/udp2raw-tunnel.git 
ENV LINUX_HEADERS_DOWNLOAD_URL=http://dl-cdn.alpinelinux.org/alpine/v3.7/main/x86_64/linux-headers-4.4.6-r2.apk

RUN apk upgrade \
    && apk add --no-cache bash tzdata rng-tools libstdc++ iptables\
    && apk add --no-cache --virtual .build-deps \
        autoconf \
        automake \
        build-base \
        curl \
        c-ares-dev \
        libev-dev \
        libtool \
        linux-headers \
        libsodium-dev \
        mbedtls-dev \
        pcre-dev \
        tar \
        git \
    && curl -sSL ${LINUX_HEADERS_DOWNLOAD_URL} > /linux-headers-4.4.6-r2.apk \
    && apk add --virtual .build-deps-kernel /linux-headers-4.4.6-r2.apk \
    && git clone ${SS_DOWNLOAD_URL} \
    && (cd shadowsocks-libev \
    && git checkout tags/${SS_LIBEV_VERSION} -b ${SS_LIBEV_VERSION} \
    && git submodule update --init --recursive \
    && ./autogen.sh \
    && ./configure --prefix=/usr --disable-documentation \
    && make install) \
    && git clone ${OBFS_DOWNLOAD_URL} \
    && (cd simple-obfs \
    && git submodule update --init --recursive \
    && ./autogen.sh \
    && ./configure --disable-documentation \
    && make install) \
    && curl -o v2ray_plugin.tar.gz -sSL ${V2RAY_PLUGIN_DOWNLOAD_URL} \
    && tar -zxf v2ray_plugin.tar.gz \
    && mv v2ray-plugin_linux_amd64 /usr/bin/v2ray-plugin \
    && curl -sSLO ${KCP_DOWNLOAD_URL} \
    && tar -zxf kcptun-linux-amd64-${KCP_VERSION}.tar.gz \
    && mv server_linux_amd64 /usr/bin/kcpserver \
    && mv client_linux_amd64 /usr/bin/kcpclient \
    && curl -sSLO ${UDPSPEEDER_DOWNLOAD_URL} \
    && tar -zxf speederv2_binaries.tar.gz \
    && mv speederv2_amd64 /usr/bin/speederv2 \
    && git clone ${UDP2RAW_DOWNLOAD_URL} \
    && (cd udp2raw-tunnel \
    && make dynamic \
    && mv udp2raw_dynamic /usr/bin/udp2raw) \
    && ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && apk del .build-deps .build-deps-kernel \
    && apk add --no-cache \
      $(scanelf --needed --nobanner /usr/bin/ss-* /usr/local/bin/obfs-* \
      | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
      | sort -u) \
    && rm -rf kcptun-linux-amd64-${KCP_VERSION}.tar.gz \
        shadowsocks-libev \
        simple-obfs \
        v2ray_plugin.tar.gz \
        speederv2* \
        udp2raw-tunnel \
        /var/cache/apk/* 

ADD entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
