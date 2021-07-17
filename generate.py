import os
import re
import json
import string
import random
from urllib import request, parse
import base64
import math

# 密码和加密方式
PASSWD = ""  # 为空时自动生成
SS_ENCRYPT = "rc4-md5"  # 加密方式，并不是所有都和udpspeeder等兼容，会导致udp不通，需自行测试
GROUP_NAME = ""  # SSR客户端分组名称

# v2ray-plugin
V2RAY_CERT_FILE = ""
V2RAY_KEY_FILE = ""

# 其他参数
SS_PARAM = "--fast-open"
KCP_SERVER_PARAM = ""
KCP_CLIENT_PARAM = ""
UDPSPEEDER_FEC = ""
UDPSPEEDER_PARAM = ""
UDP2RAW_PARAM = "--cipher-mode xor --auth-mode simple --raw-mode {mode}  --fix-gro -a"
UDP2RAW_MODE = ""
UDP2RAW_PORT_PROTOCOL = ""  # 用于docker端口 tcp为""，udp为"/udp"
BBR_MODULE = ""
BBR_DESCRIPTION = "不启用"

# 服务端默认参数
server_ss_port = 6443  # 原生ss端口
server_name = "ssserver"
server_kcptun_port = 6500
server_udpspeeder_port = 6501
server_udp2raw_port = 4096
server_network_mode = "host"  # 用于支持Full cone NAT
# 客户端默认参数
client_name = "ssclient"
client_ss_port = server_kcptun_port  # windows，安卓等SS客户端可以连这个端口使用
relay_host = "127.0.0.1"  # 运行docker客户端的IP或域名, 生成ss链接用于局域网/国内中转
client_socks5_port = 1080
client_network_mode = "bridge"
# 全局变量

server_ip = None
server_host = None
is_domain = False
ip_data = dict()

# Linux下控制台输出颜色
if os.name == 'nt':
    CBLUE = CRED = CEND = CYELLOW = CGREEN = ""
else:
    CBLUE = '\033[94m'
    CRED = '\033[95m'
    CYELLOW = '\033[93m'
    CGREEN = '\033[92m'
    CEND = '\033[0m'


def get_network_mode():
    return {
        0: {"mode": "host", "desc": "支持 Full cone NAT"},
        1: {"mode": "bridge", "desc": "桥接"}
    }


def get_udp2raw_mode():
    return {
        0: {"mode": "faketcp", "protocol": "", "desc": "绕过Qos等"},
        1: {"mode": "udp", "protocol": "/udp", "desc": "心跳保活、断线重连等"}
    }


def get_udp_fec_param():
    return {
        0: {"FEC": "输入丢包率进行计算", "desc": ""},
        1: {"FEC": "-f1:1,2:2,5:3,10:4,17:5,25:6", "desc": "丢包率7%的时候，降到0.48%"},
        2: {"FEC": "-f1:3,2:4,8:6,20:10", "desc": "丢包率15%的时候，降到0.49%"},
        3: {"FEC": "-f1:3,3:4,4:5,6:6,8:7,10:8,12:9,14:10,17:11,19:12,20:13",
            "desc": "丢包率20%的时候，降到0.27%"},
        4: {"FEC": "-f1:3,2:4,3:5,4:6,5:7,7:8,8:9,10:10,12:11,13:12,15:13,17:14,19:15,20:16",
            "desc": "丢包率25%的时候，降到0.31%"},
        5: {"FEC": "-f1:4,2:5,3:6,4:7,5:8,6:9,7:10,8:11,10:12,11:13,13:14,14:15,15:16,17:17,18:18,20:19",
            "desc": "丢包率30%的时候，降到0.49%"},
    }


def get_tcp_param():
    return {
        0: {"KCP_SERVER_PARAM": "--mode fast2 --mtu 1300",
            "KCP_CLIENT_PARAM": "--mode fast2 --mtu 1300",
            "desc": "低丢包率下使用"},
        1: {"KCP_SERVER_PARAM": "--mode fast --datashard 15 --parityshard 8 --mtu 1300",
            "KCP_CLIENT_PARAM": "--mode fast --datashard 15 --parityshard 8 --mtu 1300",
            "desc": "丢包率15%的时候，降到0.42%"},
        2: {"KCP_SERVER_PARAM": "--mode fast --datashard 15 --parityshard 15 --mtu 1300",
            "KCP_CLIENT_PARAM": "--mode fast --datashard 15 --parityshard 15 --mtu 1300",
            "desc": "丢包率30%的时候,降到0.63%"}
    }


def get_bbr_module(select):
    return {
        0: ["", "不启用"],
        1: ["rinetd-bbr", "bbr原版"],
        2: ["rinetd-bbr-powered", "bbr魔改版"],
        3: ["rinetd-pcc", "pcc"]
    }[select]


def get_random_password(num):
    str = string.ascii_letters + string.digits
    key = random.sample(str, num)
    keys = "".join(key)
    return keys


def getURI(server_ip, ss_port, description="", group=GROUP_NAME, plugin="", plugin_opts=""):
    country = ip_data.get("country")
    city = ip_data.get("city", "") if ip_data.get("city") != ip_data.get("country") else ""
    remarks = " ".join([country, city, description])
    ss_tag = "#" + parse.quote(remarks)
    if plugin and plugin_opts:
        password = base64.urlsafe_b64encode(str.encode(f"{SS_ENCRYPT}:{PASSWD}", 'utf8')).decode("utf-8")
        plugin_data = parse.quote(f";{plugin_opts}")
        ss_data = f"{password}@{server_host}:{ss_port}/?plugin={plugin}{plugin_data}{ss_tag}"
        print(" " * 4 + CYELLOW + f"ss://{ss_data}")
        return

    remarks_b64_encode = base64.urlsafe_b64encode(str.encode(remarks, 'utf8')).decode("utf-8")

    ss_data = f"{SS_ENCRYPT}:{PASSWD}@{server_ip}:{ss_port}"
    ss_uri = base64.b64encode(ss_data.encode('utf8')).decode("utf-8") + ss_tag
    print(" " * 4 + CYELLOW + f"ss://{ss_uri}" + CEND)

    password_encode = base64.urlsafe_b64encode(str.encode(PASSWD, 'utf8')).decode("utf-8")
    group_encode = base64.urlsafe_b64encode(str.encode(group, 'utf8')).decode("utf-8")
    ssr_data = f"{server_ip}:{ss_port}:origin:{SS_ENCRYPT}:plain:{password_encode}/?obfsparam=&remarks={remarks_b64_encode}&group={group_encode}"
    ssr_uri = base64.urlsafe_b64encode(ssr_data.encode('utf8')).decode("utf-8").strip("=")
    print(" " * 4 + CYELLOW + f"ssr://{ssr_uri}".strip("=") + CEND)


def set_server_network_mode():
    global server_network_mode
    while True:
        print(f"{CGREEN}请选择服务端的网络模式{CEND}")
        for index, v in get_network_mode().items():
            if index == 0:
                print(f"{CGREEN}[{index}]." + v["mode"] + f"    {v['desc']} {CEND}{CYELLOW}[默认]{CEND}")
            else:
                print(f"{CGREEN}[{index}]." + v["mode"] + f"    {v['desc']}")

        input_select = input("请输入选项：")
        if input_select == "":
            server_network_mode = get_network_mode()[0]['mode']
            print(f"当前网络模式为--network={CYELLOW}{server_network_mode}{CEND}")
            break
        elif re.match("^\d+$", input_select) and get_network_mode().get(int(input_select), None):
            index = int(input_select)
            server_network_mode = get_network_mode()[index]['mode']
            print(f"当前网络模式为--network={CYELLOW}{server_network_mode}{CEND}")
            break
        else:
            print(CRED + "输入错误，请重新输入" + CEND)


def set_kcptun_param():
    global KCP_SERVER_PARAM, KCP_CLIENT_PARAM
    if KCP_SERVER_PARAM and KCP_SERVER_PARAM:
        return
    while True:
        print(f"{CGREEN}请选择kcptun的参数{CEND}")
        for index, v in get_tcp_param().items():
            if index == 0:
                print(f"{CGREEN}[{index}]." + v["KCP_SERVER_PARAM"] + f"    {v['desc']} {CEND}{CYELLOW}[默认]{CEND}")
            else:
                print(f"{CGREEN}[{index}]." + v["KCP_SERVER_PARAM"] + f"    {v['desc']}")

        input_select = input("请输入选项：")
        if input_select == "":
            KCP_SERVER_PARAM = get_tcp_param()[0]['KCP_SERVER_PARAM']
            KCP_CLIENT_PARAM = get_tcp_param()[0]['KCP_CLIENT_PARAM']
            print(f"当前kcptun参数：{CYELLOW}{KCP_SERVER_PARAM}{CEND}")
            break
        elif re.match("^\d+$", input_select) and get_tcp_param().get(int(input_select), None):
            index = int(input_select)
            KCP_SERVER_PARAM = get_tcp_param()[index]['KCP_SERVER_PARAM']
            KCP_CLIENT_PARAM = get_tcp_param()[index]['KCP_CLIENT_PARAM']
            print(f"当前kcptun参数：{CYELLOW}{KCP_SERVER_PARAM}{CEND}")
            break
        else:
            print(CRED + "输入错误，请重新输入" + CEND)


def set_udpspeeder_fec_param():
    global UDPSPEEDER_FEC
    if UDPSPEEDER_FEC:
        return
    while True:
        print(f"{CGREEN}请选择udpspeeder的FEC参数{CEND}")
        for index, v in get_udp_fec_param().items():
            if index == 0:
                print(f"{CGREEN}[{index}]." + v["FEC"] + f"    {v['desc']} {CEND}{CYELLOW}[默认]{CEND}")
            else:
                print(f"{CGREEN}[{index}]." + ",".join(v["FEC"].split(",")[:7]) + f"    {v['desc']}")
        input_select = input("请输入选项：")
        if input_select == "" or input_select == "0":
            while True:
                origin_loss = input(f"{CGREEN}请输入丢包率：{CEND}")
                if re.match("^\d+$", origin_loss):
                    origin_loss = int(origin_loss)
                    break
                else:
                    print(f"{CRED}输入有误，请重新输入{CEND}")
            UDPSPEEDER_FEC = calc_fec_param(0.5, origin_loss)
            print(f"当前FEC参数：{CYELLOW}{UDPSPEEDER_FEC}{CEND}")
            break
        elif re.match("^\d+$", input_select) and get_udp_fec_param().get(int(input_select), None):
            index = int(input_select)
            UDPSPEEDER_FEC = get_udp_fec_param()[index]['FEC']
            print(f"当前FEC参数：{CYELLOW}{UDPSPEEDER_FEC}{CEND}")
            break
        else:
            print(CRED + "输入错误，请重新输入" + CEND)


def set_udp2raw_mode_param():
    global UDP2RAW_MODE, UDP2RAW_PORT_PROTOCOL
    while True:
        print(f"{CGREEN}请选择UDP2raw的 --raw-mode{CEND}")
        for index, v in get_udp2raw_mode().items():
            if index == 0:
                print(f"{CGREEN}[{index}]." + v["mode"] + f"    {v['desc']} {CEND}{CYELLOW}[默认]{CEND}")
            else:
                print(f"{CGREEN}[{index}]." + ",".join(v["mode"].split(",")[:7]) + f"    {v['desc']}")
        input_select = input("请输入选项：")
        if input_select == "" or input_select == "0":
            UDP2RAW_MODE = get_udp2raw_mode().get(0)['mode']
            UDP2RAW_PORT_PROTOCOL = get_udp2raw_mode().get(0)['protocol']
            print(f"当前UDP2raw参数：{CYELLOW}{UDP2RAW_PARAM.format(mode=UDP2RAW_MODE)}{CEND}")
            break
        elif re.match("^\d+$", input_select) and get_udp2raw_mode().get(int(input_select), None):
            UDP2RAW_MODE = get_udp2raw_mode().get(int(input_select))['mode']
            UDP2RAW_PORT_PROTOCOL = get_udp2raw_mode().get(int(input_select))['protocol']
            print(f"当前UDP2raw参数：{CYELLOW}{UDP2RAW_PARAM.format(mode=UDP2RAW_MODE)}{CEND}")
            break
        else:
            print(CRED + "输入错误，请重新输入" + CEND)


def ss_bbr(server_num=0, client_offset=0, suffix=""):
    server_cmd = f'docker rm -f {server_name}_{server_num};\\\n\
       docker run -dt \\\n\
       --cap-add=NET_ADMIN \\\n\
       --network={server_network_mode} \\\n\
       --restart=always \\\n\
       --name {server_name}_{server_num} \\\n\
       -p {server_ss_port + server_num}:{server_ss_port + server_num} \\\n\
       -p {server_ss_port + server_num}:{server_ss_port + server_num}/udp \\\n\
        sola97/shadowsocks \\\n\
       -s "ss-server" \\\n\
       -S "-s 0.0.0.0 -p {server_ss_port + server_num} -m {SS_ENCRYPT} -k {PASSWD} -u {SS_PARAM}\" \\\n\
       -b "{BBR_MODULE}" '

    client_cmd = f'docker rm -f {client_name}{suffix};\\\n\
       docker run -dt \\\n\
       --network={client_network_mode} \\\n\
       --restart=always \\\n\
       --name {client_name}{suffix} \\\n\
       -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset} \\\n\
       -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset}/udp \\\n\
       sola97/shadowsocks \\\n\
       -s "ss-local" \\\n\
       -S "-s {server_host} -p {server_ss_port + server_num} -b 0.0.0.0 -l {client_socks5_port + client_offset} -u -m {SS_ENCRYPT} -k {PASSWD}  {SS_PARAM}"'

    print(f"{CRED}↓SS + {BBR_DESCRIPTION}↓{CEND}")
    print(f"服务端：\n    {CBLUE}{server_cmd}{CEND}")
    print(f"客户端：\n    {CBLUE}{client_cmd}{CEND}")
    print(f"{CRED}↑SS + {BBR_DESCRIPTION}↑{CEND}")
    print(f"服务端SS端口：{server_ss_port + server_num}")
    print(f"客户端SOCKS5端口：{client_socks5_port + client_offset}")
    print("密码为：" + PASSWD)
    print(f"导出链接：")
    getURI(server_host, server_ss_port + server_num, f"{BBR_DESCRIPTION} 直连")
    write_compose_file(server_cmd, subfolder="ss-bbr")
    write_compose_file(client_cmd, subfolder="ss-bbr")


def ss_v2ray_ws_tls_bbr(server_num=0, client_offset=0, suffix=""):
    server_ss_port = globals().get("server_ss_port")
    server_suffix = server_num
    global V2RAY_CERT_FILE, V2RAY_KEY_FILE
    if not is_domain:
        print(f"{CRED}启用 v2ray(ws+tls) 需要服务器地址为域名{CEND}")
        return

    if not V2RAY_CERT_FILE:
        while True:
            V2RAY_CERT_FILE = input(f"{CGREEN}请输入要mount的证书fullchain.cer文件的路径：{CEND}")
            confirm = input(
                f"{CGREEN}输入的路径为：{CEND}{CYELLOW}" + V2RAY_CERT_FILE + f" {CEND}{CGREEN}确认{CEND}{CYELLOW}Y{CEND}{CGREEN}/n{CEND}")
            if confirm == "" or confirm.lower().startswith("y"):
                break

    if not V2RAY_KEY_FILE:
        while True:
            V2RAY_KEY_FILE = input(f"{CGREEN}请输入要mount的证书{server_host}.key文件的路径：{CEND}")
            confirm = input(
                f"{CGREEN}输入的路径为：{CEND}{CYELLOW}" + V2RAY_KEY_FILE + f" {CEND}{CGREEN}确认{CEND}{CYELLOW}Y{CEND}{CGREEN}/n{CEND}")
            if confirm == "" or confirm.lower().startswith("y"):
                break
    while True:
        confirm = input(f"{CGREEN}是否设定服务器端口为443?{CEND}{CYELLOW}Y{CEND}{CGREEN}/n{CEND}")
        if confirm == "" or confirm.lower().startswith("y"):
            server_suffix = "https"
            server_ss_port = 443
            server_num = 0
            break
        elif confirm.lower().startswith("n"):
            break
    cert_file_path = "/etc/v2ray-plugin/fullchain.cer"
    key_file_path = f"/etc/v2ray-plugin/private.key"
    server_cmd = f'docker rm -f {server_name}_{server_suffix};\\\n\
       docker run -dt \\\n\
       --cap-add=NET_ADMIN \\\n\
       --restart=always \\\n\
       --network={server_network_mode} \\\n\
       --name {server_name}_{server_suffix} \\\n\
       -p {server_ss_port + server_num}:{server_ss_port + server_num} \\\n\
       -p {server_ss_port + server_num}:{server_ss_port + server_num}/udp \\\n\
       -v {V2RAY_CERT_FILE}:{cert_file_path} \\\n \
       -v {V2RAY_KEY_FILE}:{key_file_path} \\\n \
        sola97/shadowsocks \\\n\
       -s "ss-server" \\\n\
       -S "-s 0.0.0.0 -p {server_ss_port + server_num} -m {SS_ENCRYPT} -k {PASSWD} -u {SS_PARAM} --plugin v2ray-plugin --plugin-opts=server;tls;host={server_host};cert={cert_file_path};key={key_file_path}\" \\\n\
       -b "{BBR_MODULE}"'

    client_cmd = f'docker rm -f {client_name}{suffix};\\\n\
       docker run -dt \\\n\
       --restart=always \\\n\
       --network={client_network_mode} \\\n\
       --name {client_name}{suffix} \\\n\
       -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset} \\\n\
       -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset}/udp \\\n\
       sola97/shadowsocks \\\n\
       -m "-l0.0.0.0:{client_socks5_port + client_offset}  -r{server_ip}:{server_ss_port + server_num} -u" \\\n\
       -s "ss-local" \\\n\
       -S "-s {server_host} -p {server_ss_port + server_num} -b 0.0.0.0 -l {client_socks5_port + client_offset} -u -m {SS_ENCRYPT} -k {PASSWD}  {SS_PARAM}  --plugin v2ray-plugin --plugin-opts=tls;host={server_host}"'

    print(f"{CRED}↓SS + v2ray-plugin(ws+tls) + bbr↓{CEND}")
    print(f"服务端：\n    {CBLUE}{server_cmd}{CEND}")
    print(f"客户端：\n    {CBLUE}{client_cmd}{CEND}")
    print(f"{CRED}↑SS + v2ray-plugin(ws+tls) + bbr↑{CEND}")
    print(f"服务端SS端口：{server_ss_port + server_num}")
    print(f"客户端SOCKS5端口：{client_socks5_port + client_offset}")
    print("密码为：" + PASSWD)
    print(f"导出链接：")
    getURI(server_host, server_ss_port + server_num, f"{BBR_DESCRIPTION} + v2ray(ws+tls)", "", "v2ray-plugin",
           f"tls;host={server_host}")
    write_compose_file(server_cmd, subfolder="ss-v2ray")
    write_compose_file(client_cmd, subfolder="ss-v2ray")


def ss_kcptun_udpspeeder(server_num=0, client_offset=0, suffix=""):
    set_kcptun_param()
    set_udpspeeder_fec_param()
    server_cmd = f'docker rm -f {server_name}_{server_num};\\\n\
    docker run -dt \\\n\
    --cap-add=NET_ADMIN \\\n\
    --network={server_network_mode} \\\n\
    --restart=always \\\n\
    --name {server_name}_{server_num} \\\n\
    -p {server_ss_port + server_num}:{server_ss_port + server_num} \\\n\
    -p {server_ss_port + server_num}:{server_ss_port + server_num}/udp \\\n\
    -p {server_kcptun_port + server_num * 2}:{server_kcptun_port + server_num * 2}/udp \\\n\
    -p {server_udpspeeder_port + server_num * 2}:{server_udpspeeder_port + server_num * 2}/udp \\\n\
     sola97/shadowsocks \\\n\
    -s "ss-server" \\\n\
    -S "-s 0.0.0.0 -p {server_ss_port + server_num} -m {SS_ENCRYPT} -k {PASSWD} -u {SS_PARAM}\" \\\n\
    -k "kcpserver" \\\n\
    -K "-l 0.0.0.0:{server_kcptun_port + server_num * 2}  -t 127.0.0.1:{server_ss_port + server_num} {KCP_SERVER_PARAM} " \\\n\
    -u "-s -l0.0.0.0:{server_udpspeeder_port + server_num * 2} -r 127.0.0.1:{server_ss_port + server_num}  {UDPSPEEDER_FEC} {UDPSPEEDER_PARAM} -k {PASSWD}" \\\n\
    -b "{BBR_MODULE}" '

    client_cmd = f'docker rm -f {client_name}{suffix};\\\n\
    docker run -dt \\\n\
    --network={client_network_mode} \\\n\
    --restart=always \\\n\
    --name {client_name}{suffix} \\\n\
    -p {client_ss_port + client_offset}:{client_ss_port + client_offset} \\\n\
    -p {client_ss_port + client_offset}:{client_ss_port + client_offset}/udp \\\n\
    -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset} \\\n\
    -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset}/udp \\\n\
    sola97/shadowsocks \\\n\
    -s "ss-local" \\\n\
    -S "-s 127.0.0.1 -p {client_ss_port + client_offset} -b 0.0.0.0 -l {client_socks5_port + client_offset} -u -m {SS_ENCRYPT} -k {PASSWD}  {SS_PARAM}" \\\n\
    -k "kcpclient"  \\\n\
    -K "-l :{client_ss_port + client_offset} -r {server_ip}:{server_kcptun_port + server_num * 2} {KCP_CLIENT_PARAM}" \\\n\
    -u "-c -l0.0.0.0:{client_ss_port + client_offset}  -r{server_ip}:{server_udpspeeder_port + server_num * 2} {UDPSPEEDER_FEC} {UDPSPEEDER_PARAM} -k {PASSWD}"'
    print(f"{CRED}↓SS + Kcptun + UDPspeeder↓{CEND}")
    print(f"服务端：\n    {CBLUE}{server_cmd}{CEND}")
    print(f"客户端：\n    {CBLUE}{client_cmd}{CEND}")
    print(f"{CRED}↑SS + Kcptun + UDPspeeder↑{CEND}")
    print(f"服务端原生SS端口：{server_ss_port + server_num}")
    print(f"客户端本地映射SS端口：{client_ss_port + client_offset}\n"
          f"SOCKS5端口：{client_socks5_port + client_offset}")
    print("密码为：" + PASSWD)
    print(f"{BBR_DESCRIPTION + '加速' if BBR_MODULE else ''}直连服务端SS：")
    getURI(server_host, server_ss_port + server_num, f"{BBR_DESCRIPTION} 直连")
    print(f"通过{CRED}{relay_host}{CEND}的 Kcptun + UDPspeeder 的监听端口连接SS：")
    getURI(relay_host, client_ss_port + client_offset, '')
    write_compose_file(server_cmd, subfolder="ss-kcp-udp")
    write_compose_file(client_cmd, subfolder="ss-kcp-udp")


def ss_kcptun_udpspeeder_dual_udp2raw(server_num=0, client_offset=0, suffix=""):
    set_kcptun_param()
    set_udpspeeder_fec_param()
    set_udp2raw_mode_param()
    server_cmd = f'docker rm -f {server_name}_{server_num};\\\n\
    docker run -dt \\\n\
    --cap-add=NET_ADMIN \\\n\
    --network={server_network_mode} \\\n\
    --restart=always \\\n\
    --name {server_name}_{server_num} \\\n\
    -p {server_ss_port + server_num}:{server_ss_port + server_num} \\\n\
    -p {server_ss_port + server_num}:{server_ss_port + server_num}/udp \\\n\
    -p {server_udp2raw_port + server_num * 2}:{server_udp2raw_port + server_num * 2}{UDP2RAW_PORT_PROTOCOL} \\\n\
    -p {server_udp2raw_port + 1 + server_num * 2}:{server_udp2raw_port + 1 + server_num * 2}{UDP2RAW_PORT_PROTOCOL} \\\n\
     sola97/shadowsocks \\\n\
    -s "ss-server" \\\n\
    -S "-s 0.0.0.0 -p {server_ss_port + server_num} -m {SS_ENCRYPT} -k {PASSWD} -u --fast-open" \\\n\
    -k "kcpserver" \\\n\
    -K "-l 0.0.0.0:6500  -t 127.0.0.1:{server_ss_port + server_num} {KCP_SERVER_PARAM} " \\\n\
    -u "-s -l0.0.0.0:6501 -r 127.0.0.1:{server_ss_port + server_num}  {UDPSPEEDER_FEC} {UDPSPEEDER_PARAM} -k {PASSWD}" \\\n\
    -t "-s -l0.0.0.0:{server_udp2raw_port + server_num * 2} -r 127.0.0.1:6500    -k {PASSWD} {UDP2RAW_PARAM.format(mode=UDP2RAW_MODE)}" \\\n\
    -T "-s -l0.0.0.0:{server_udp2raw_port + 1 + server_num * 2} -r 127.0.0.1:6501    -k {PASSWD} {UDP2RAW_PARAM.format(mode=UDP2RAW_MODE)}"\\\n\
    -b "{BBR_MODULE}" '

    client_cmd = f'docker rm -f {client_name}{suffix};\\\n\
    docker run -dt \\\n\
    --cap-add=NET_ADMIN \\\n\
    --network={client_network_mode} \\\n\
    --restart=always \\\n\
    --name {client_name}{suffix} \\\n\
    -p {client_ss_port + client_offset}:{client_ss_port + client_offset} \\\n\
    -p {client_ss_port + client_offset}:{client_ss_port + client_offset}/udp \\\n\
    -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset} \\\n\
    -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset}/udp \\\n\
    sola97/shadowsocks \\\n\
    -t "-c -l0.0.0.0:3333  -r{server_ip}:{server_udp2raw_port + server_num * 2}  -k {PASSWD} {UDP2RAW_PARAM.format(mode=UDP2RAW_MODE)}\" \\\n\
    -T "-c -l0.0.0.0:3334  -r{server_ip}:{server_udp2raw_port + 1 + server_num * 2}  -k {PASSWD} {UDP2RAW_PARAM.format(mode=UDP2RAW_MODE)}\" \\\n\
    -k "kcpclient"  \\\n\
    -K "-l :{client_ss_port + client_offset} -r 127.0.0.1:3333 {KCP_CLIENT_PARAM}" \\\n\
    -u "-c -l0.0.0.0:{client_ss_port + client_offset}  -r127.0.0.1:3334 {UDPSPEEDER_FEC} {UDPSPEEDER_PARAM} -k {PASSWD}" \\\n\
    -s "ss-local" \\\n\
    -S "-s 127.0.0.1 -p {client_ss_port + client_offset} -b 0.0.0.0 -l {client_socks5_port + client_offset} -u -m {SS_ENCRYPT} -k {PASSWD}  {SS_PARAM}"'
    print(f"{CRED}↓SS + Kcptun + UDPspeeder + 双UDP2raw↓{CEND}")
    print(f"服务端：\n    {CBLUE}{server_cmd}{CEND}")
    print(f"客户端：\n    {CBLUE}{client_cmd}{CEND}")
    print(f"{CRED}↑SS + Kcptun + UDPspeeder + 双UDP2raw↑{CEND}")
    print(f"服务端原生SS端口：{server_ss_port + server_num}")
    print(f"客户端本地映射SS端口：{client_ss_port + client_offset}\n"
          f"SOCKS5端口：{client_socks5_port + client_offset}")
    print("密码为：" + PASSWD)
    print(f"{BBR_DESCRIPTION + '加速' if BBR_MODULE else ''}直连服务端SS：")
    getURI(server_host, server_ss_port + server_num, f"{BBR_DESCRIPTION} 直连")
    print(f"通过{CRED}{relay_host}{CEND}的 Kcptun + UDPspeeder 的监听端口连接SS：")
    getURI(relay_host, client_ss_port + client_offset, '双udp2raw')
    write_compose_file(server_cmd, subfolder="ss-kcp-udp-dual2raw")
    write_compose_file(client_cmd, subfolder="ss-kcp-udp-dual2raw")


def ss_kcptun_udpspeeder_udp2raw(server_num=0, client_offset=0, suffix=""):
    set_kcptun_param()
    set_udpspeeder_fec_param()
    set_udp2raw_mode_param()
    server_cmd = f'docker rm -f {server_name}_{server_num};\\\n\
    docker run -dt \\\n\
    --cap-add=NET_ADMIN \\\n\
    --network={server_network_mode} \\\n\
    --restart=always \\\n\
    --name {server_name}_{server_num} \\\n\
    -p {server_ss_port + server_num}:{server_ss_port + server_num} \\\n\
    -p {server_ss_port + server_num}:{server_ss_port + server_num}/udp \\\n\
    -p {server_kcptun_port + server_num * 2}:{server_kcptun_port + server_num * 2}/udp \\\n\
    -p {server_udp2raw_port + 1 + server_num * 2}:{server_udp2raw_port + 1 + server_num * 2}{UDP2RAW_PORT_PROTOCOL} \\\n\
     sola97/shadowsocks \\\n\
    -s "ss-server" \\\n\
    -S "-s 0.0.0.0 -p {server_ss_port + server_num} -m {SS_ENCRYPT} -k {PASSWD} -u {SS_PARAM}\" \\\n\
    -k "kcpserver" \\\n\
    -K "-l 0.0.0.0:{server_kcptun_port + server_num * 2}  -t 127.0.0.1:{server_ss_port + server_num} {KCP_SERVER_PARAM} " \\\n\
    -u "-s -l0.0.0.0:{server_kcptun_port + 1 + server_num * 2} -r 127.0.0.1:{server_ss_port + server_num}  {UDPSPEEDER_FEC} {UDPSPEEDER_PARAM} -k {PASSWD}"  \\\n\
    -t "-s -l0.0.0.0:{server_udp2raw_port + 1 + server_num * 2} -r 127.0.0.1:{server_kcptun_port + 1 + server_num * 2}    -k {PASSWD} {UDP2RAW_PARAM.format(mode=UDP2RAW_MODE)}"  \\\n\
    -b "{BBR_MODULE}" '

    client_cmd = f'docker rm -f {client_name}{suffix};\\\n\
    docker run -dt \\\n\
    --cap-add=NET_ADMIN \\\n\
    --network={client_network_mode} \\\n\
    --restart=always \\\n\
    --name {client_name}{suffix} \\\n\
    -p {client_ss_port + client_offset}:{client_ss_port + client_offset} \\\n\
    -p {client_ss_port + client_offset}:{client_ss_port + client_offset}/udp \\\n\
    -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset} \\\n\
    -p {client_socks5_port + client_offset}:{client_socks5_port + client_offset}/udp \\\n\
    sola97/shadowsocks \\\n\
    -t "-c -l0.0.0.0:3334  -r{server_ip}:{server_udp2raw_port + 1 + server_num * 2}  -k {PASSWD} {UDP2RAW_PARAM.format(mode=UDP2RAW_MODE)}" \\\n\
    -k "kcpclient"  \\\n\
    -K "-l :{client_ss_port + client_offset} -r {server_ip}:{server_kcptun_port + server_num * 2} {KCP_CLIENT_PARAM}" \\\n\
    -u "-c -l0.0.0.0:{client_ss_port + client_offset}  -r127.0.0.1:3334 {UDPSPEEDER_FEC} {UDPSPEEDER_PARAM} -k {PASSWD}" \\\n\
    -s "ss-local" \\\n\
    -S "-s 127.0.0.1 -p {client_ss_port + client_offset} -b 0.0.0.0 -l {client_socks5_port + client_offset} -u -m {SS_ENCRYPT} -k {PASSWD}  {SS_PARAM}"'
    print(f"{CRED}↓SS + Kcptun + UDPspeeder+ 单UDP2raw↓{CEND}")
    print(f"服务端：\n    {CBLUE}{server_cmd}{CEND}")
    print(f"客户端：\n    {CBLUE}{client_cmd}{CEND}")
    print(f"{CRED}↑SS + Kcptun + UDPspeeder+ 单UDP2raw↑{CEND}")
    print(f"服务端原生SS端口：{server_ss_port + server_num}")
    print(f"客户端本地映射SS端口：{client_ss_port + client_offset}\n"
          f"SOCKS5端口：{client_socks5_port + client_offset}")
    print("密码为：" + PASSWD)
    print(f"{BBR_DESCRIPTION + '加速' if BBR_MODULE else ''}直连服务端SS：")
    getURI(server_host, server_ss_port + server_num, f"{BBR_DESCRIPTION} 直连")
    print(f"通过{CRED}{relay_host}{CEND}的 Kcptun + UDPspeeder 的监听端口连接SS：")
    getURI(relay_host, client_ss_port + client_offset, '单udp2raw')
    write_compose_file(server_cmd, subfolder="ss-kcp-udp-udp2raw")
    write_compose_file(client_cmd, subfolder="ss-kcp-udp-udp2raw")


# 在丢包率为P的情况下，n个包中至少到达m个的概率
def f0(n, m, p):
    sum = 0
    for k in range(m, n + 1):
        sum += C(k, n) * math.pow(1 - p, k) * math.pow(p, n - k)
    return sum


def C(n, m):
    return math.factorial(m) / (math.factorial(n) * math.factorial(m - n))


def calc(x, y, p):
    return 1 - f0(x + y, x, p)


def predict_loss(fec, packet_loss):
    x, y = fec.split(":")
    pred = calc(int(x), int(y), packet_loss / 100.0) * 100
    print(f"{x}:{y} 可以将 {packet_loss}% 的丢包率降为 " + "%.2f%%" % pred)


def calc_fec_param(target_loss, origin_loss, num=20):
    str = "-f"
    origin_loss /= 100.0
    target_loss /= 100.0
    num += 1
    map = dict()
    for x in range(1, num):
        for y in range(1, num):
            if calc(x, y, origin_loss) < target_loss:
                map[y] = x
                break
    return str + ",".join(f"{map[k]}:{k}" for k in sorted(map.keys()))


# 转换为docker-compose

def search(command, arg):
    regex = "^[ ]*[-]+" + arg + '[\s="]+([^\n\\\\"]+)[ ]*'
    if re.findall(regex, command, flags=re.MULTILINE).__len__() > 0:
        value = '"' + re.search(re.compile(regex, re.MULTILINE), command, ).group(1).strip() + '"'
        return value
    return ""


def search_ports(command):
    if search(command, "network") == '"host"':
        return ""
    else:
        ports = "\n    ports:"
        for p in re.findall("^[ ]*-p (\S+)", command, flags=re.MULTILINE):
            ports += "\n        - " + p
        return ports


def search_env(command):
    env = ""
    map = {
        "SS_MODULE": "s",
        "SS_CONFIG": "S",
        "KCP_MODULE": "k",
        "KCP_CONFIG": "K",
        "UDPSPEEDER_CONFIG": "u",
        "UDP2RAW_CONFIG_ONE": "t",
        "UDP2RAW_CONFIG_TWO": "T",
        "BBR_MODULE": "b",
        "BBR_CONFIG": "B",
        "TINY_MAPPER_CONFIG_ONE": "m",
        "TINY_MAPPER_CONFIG_TWO": 'M',
    }
    for cmd_name, cmd_key in map.items():
        cmd = search(command, cmd_key)
        if cmd:
            env += f"\n        {cmd_name}: {cmd}"
    return env


def get_docker_compose(command):
    docker_compose_template = f'''version: '3.7'
services:
  shadowsocks:
    cap_add:
      - NET_ADMIN
    image: sola97/shadowsocks
    container_name: {search(command, "name")}
    restart: always
    network_mode: {search(command, "network")}{search_ports(command)}
    environment:{search_env(command)}
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    '''
    return docker_compose_template


def write_compose_file(command, subfolder=""):
    path = "docker-compose/"+subfolder+"/"
    if not os.path.exists(path):
        os.makedirs(path)
    file_name = path + search(command, "name").strip('"') + ".yml"
    file_content = get_docker_compose(command)
    with open(file_name, mode='w', encoding='utf-8') as f:
        f.write(file_content)
    print(f"{CGREEN}已写入docker-compose文件：" + file_name)


if __name__ == '__main__':
    if not PASSWD:
        PASSWD = get_random_password(8)
    while True:
        query = input(f"{CGREEN}请输入服务器IP或者域名(留空为获取本机IP)：{CEND}")
        try:
            print("正在获取服务器IP的所在地...")
            with request.urlopen(f"http://ip-api.com/json/{query}?lang=zh-CN") as f:
                ip_data = json.loads(f.read().decode('utf-8'))
                if ip_data['status'] == 'success':
                    client_name = "ss_" + ip_data['countryCode'] + (
                        f"_{ip_data['region']}" if ip_data['region'] else "")
                    client_name = client_name.lower()
                    server_ip = ip_data['query']
                    if query != server_ip and query != "":
                        server_host = query
                        is_domain = True
                    else:
                        server_host = server_ip
                    print(f"{CYELLOW}服务器信息：" + " ".join(
                        [ip_data.get("country", ""), ip_data.get("city", ""), server_ip]) + CEND)
                    break
                else:
                    print("获取失败，请检查输入是否有误")
        except Exception as e:
            print("获取失败，请重试", e)

    server_num = 0
    client_offset = 0

    sname_input = input(f"{CGREEN}请输入服务端容器名(默认为{CEND}{CYELLOW}{server_name}{CEND}{CGREEN}，回车保持默认)\n：{CEND}")
    if sname_input:
        server_name = sname_input

    sn_input = input(f"{CGREEN}请输入sserver容器的序号（用于运行多个容器的情况，默认为0，回车保持默认）\n：{CEND}")
    if re.match("^\d+$", sn_input):
        server_num = int(sn_input)
        client_offset = int(sn_input)
    print(f"服务端docker容器名为：{CYELLOW}{server_name}_{server_num}{CEND}")

    cname_input = input(f"{CGREEN}请输入客户端容器名(默认为{CEND}{CYELLOW}{client_name}{CEND}{CGREEN}，回车保持默认)\n：{CEND}")
    if cname_input:
        client_name = cname_input

    print(f"客户端docker容器名为：{CYELLOW}{client_name}{CEND}")
    cl_offset = input(
        f"{CGREEN}客户端将使用{CEND}{CYELLOW}{client_socks5_port + client_offset}{CEND}{CGREEN}端口，如需修改请输入新的偏移量，当前为{client_socks5_port}+{CEND}{CYELLOW}{server_num}\n：{CEND}")

    if re.match("^\d+$", cl_offset):
        client_offset = int(cl_offset)
    print(f"客户端SOCKS5端口为：{CYELLOW}{client_socks5_port + client_offset}{CEND}")

    set_server_network_mode()

    while True:
        print(f"{CGREEN}请选择启动的bbr模块,回车保持默认,当前为{CEND}{CYELLOW}{BBR_DESCRIPTION}{CEND}")
        for i in range(4):
            print(f"{CGREEN}[{i}]." + " ".join(get_bbr_module(i)) + CEND)

        input_select = input("请输入选项：")
        if input_select in ("0", "1", "2", "3"):
            BBR_MODULE, BBR_DESCRIPTION = get_bbr_module(int(input_select))
            print("当前bbr模块：" + CYELLOW + " ".join([BBR_MODULE, BBR_DESCRIPTION]) + CEND)
            break
        elif input_select == "":
            print("当前bbr模块：" + CYELLOW + " ".join([BBR_MODULE, BBR_DESCRIPTION]) + CEND)
            break
        else:
            print(CRED + "输入错误，请重新输入" + CEND)

    while True:
        print(f"{CGREEN}请选择方案：")
        print("[0].退出")
        bbr = "+ " + BBR_DESCRIPTION if BBR_MODULE else ""
        print(f"[1].SS {bbr}")
        print(f"[2].SS {bbr}+ v2ray-plugin(ws+tls)")
        print(f"[3].SS {bbr}+ Kcptun + UDPspeeder + 单UDP2raw {CEND}{CYELLOW}[默认 游戏推荐]{CEND}{CGREEN}")
        print(f"[4].SS {bbr}+ Kcptun + UDPspeeder")
        print(f"[5].SS {bbr}+ Kcptun + UDPspeeder + 双UDP2raw")
        input_select = input("请输入选项：")
        if input_select == "":
            print("输入有误，请重新输入")
        if input_select == "1":
            ss_bbr(server_num, client_offset)
        if input_select == "2":
            ss_v2ray_ws_tls_bbr(server_num, client_offset, "_v2ray")
        if input_select == "3":
            ss_kcptun_udpspeeder_udp2raw(server_num, client_offset)
        if input_select == "4":
            ss_kcptun_udpspeeder(server_num, client_offset)
        if input_select == "5":
            ss_kcptun_udpspeeder_dual_udp2raw(server_num, client_offset)
        if input_select == "0":
            print("退出")
            break
