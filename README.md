## Dockerfile
- **shadowsocks-libev 版本: 3.2.4**
- **kcptun 版本: 20190109**
- **udpspeederv2 版本: 20190121.0**
- **udp2raw 版本: 20181113.0**

**基于[mtrid/shadowsocks](https://github.com/mritd/dockerfile/tree/master/shadowsocks)修改**

[同时加速tcp和udp流量](https://github.com/wangyu-/UDPspeeder/wiki/UDPspeeder---kcptun-finalspeed---$$-%E5%90%8C%E6%97%B6%E5%8A%A0%E9%80%9Ftcp%E5%92%8Cudp%E6%B5%81%E9%87%8F)

![](https://github.com/wangyu-/UDPspeeder/raw/master/images/cn/speeder_kcptun.PNG)

### 打开姿势

``` sh
docker run -dt --name ss -p 6443:6443 shadowsocks -S "-s 0.0.0.0 -p 6443 -m chacha20 -k test123"
```

### 支持选项

- `-s` : 指定 shadowsocks 命令，默认为 `ss-server`
- `-S` : shadowsocks-libev 参数字符串
- `-k` : 指定 kcptun 命令，默认为 `kcpserver` 
- `-K` : kcptun 参数字符串
- `-t` : udp2raw 参数字符串
- `-T` : udp2raw 参数字符串
- `-g` : 使用 `/dev/urandom` 来生成随机数

### 选项描述

- `-s` : 参数后指定一个 shadowsocks 命令，如 ss-local，不写默认为 ss-server；该参数用于 shadowsocks 在客户端和服务端工作模式间切换，可选项如下: `ss-local`、`ss-manager`、`ss-nat`、`ss-redir`、`ss-server`、`ss-tunnel`
- `-S` : 参数后指定一个 shadowsocks-libev 的参数字符串，所有参数将被拼接到 `ss-server` 后
- `-k` : 参数后指定一个 kcptun 命令，如 kcpclient，不写默认为 kcpserver；该参数用于 kcptun 在客户端和服务端工作模式间切换，可选项如下: `kcpserver`、`kcpclient`
- `-K` : 参数后指定一个 kcptun 的参数字符串，所有参数将被拼接到 `kcptun` 后;不写默认为禁用;
- `-t` : 参数后指定一个 udp2raw 的参数字符串，所有参数将被拼接到 `udpspeederv2` 后;不写默认为禁用;
- `-T` : 启动第二个 udp2raw 进程的参数字符串;不写默认为禁用;
- `-g` : 修复在 GCE 上可能出现的 `This system doesn't provide enough entropy to quickly generate high-quality random numbers.` 错误





### 命令示例

**Server 端**

``` sh
docker run -dt \
--restart=always \
--name ssserver \
-p 6443:6443 \
-p 6443:6443/udp \
-p 6500:6500/udp \
-p 6501:6501/udp \
 shadowsocks \
-s "ss-server" \
-S "-s 0.0.0.0 -p 6443 -m chacha20 -k test123 -u --fast-open" \
-k "kcpserver" \
-K "-l 0.0.0.0:6500  -t 127.0.0.1:6443 -mode fast2" \
-u "-s -l0.0.0.0:6501 -r 127.0.0.1:6443  -f20:10 -k test123 "
```

**以上命令相当于执行了**

``` sh
ss-server -s 0.0.0.0 -p 6443 -m chacha20 -k test123 -u --fast-open
kcpserver -l 0.0.0.0:6500  -t 127.0.0.1:6443 -mode fast2
speederv2 -s -l0.0.0.0:6501 -r 127.0.0.1:6443  -f20:10 -k test123 
```

**Client 端**

``` sh
docker run -dt \
-p 6500:6500 \
-p 6500:6500/udp \
-p 1080:1080 \
-p 1080:1080/udp \
--restart=always \
--name ssclient \
shadowsocks \
-s "ss-local" \
-S "-s 127.0.0.1 -p 6500 -b 0.0.0.0 -l 1080 -u -m chacha20 -k test123  --fast-open" \
-k "kcpclient"  \
-K "-l :6500 -r $SS_SERVER_IP:6500 -mode fast2" \
-u "-c -l[::]:6500  -r$SS_SERVER_IP:6501 -f20:10 -k test123" 
```

**以上命令相当于执行了** 

``` sh
ss-local -s 127.0.0.1 -p 6500 -b 0.0.0.0 -l 1080 -u -m chacha20 -k test123  --fast-open
kcpclient -l :6500 -r $SS_SERVER_IP:6500 -mode fast2
speederv2 -c -l[::]:6500  -r$SS_SERVER_IP:6501 -f20:10 -k test123
```


**注意：启用udp2raw时候要指定`docker --cap-add=NET_ADMIN` **


### 环境变量支持


|环境变量|作用|取值|
|-------|---|---|
|SS_MODULE|shadowsocks 启动命令| `ss-local`、`ss-manager`、`ss-nat`、`ss-redir`、`ss-server`、`ss-tunnel`|
|SS_CONFIG|shadowsocks-libev 参数字符串|所有字符串内内容应当为 shadowsocks-libev 支持的选项参数|
|KCP_MODULE|kcptun 启动命令| `kcpserver`、`kcpclient`|
|KCP_CONFIG|kcptun 参数字符串|所有字符串内内容应当为 kcptun 支持的选项参数|
|UDPSPEEDER_CONFIG|udpspeederv2 参数字符串|所有字符串内内容应当为 udpspeederv2 支持的选项参数,为空时不启动
|UDP2RAW_CONFIG_ONE|第一个 udp2raw 进程参数字符串|所有字符串内内容应当为 udp2raw 支持的选项参数,为空时不启动
|UDP2RAW_CONFIG_TWO|第二个 udp2raw 进程参数字符串|所有字符串内内容应当为 udp2raw 支持的选项参数,为空时不启动
|RNGD_FLAG|是否使用 `/dev/urandom` 生成随机数|可选参数为 true 和 false，默认为 fasle 不使用|



**使用时可指定环境变量，如下**

``` sh
docker run -dt --name ss -p 6443:6443 -p 6500:6500/udp -e SS_CONFIG="-s 0.0.0.0 -p 6443 -m chacha20-ietf-poly1305 -k test123" -e KCP_MODULE="kcpserver" -e KCP_CONFIG="-t 127.0.0.1:6443 -l :6500 -mode fast2" shadowsocks
```
