import os
import re
import json
import string
import random
from urllib import request
#Linux下控制台输出颜色
if os.name == 'nt':
    CBLUE=CRED=CEND=""
else:
    CBLUE = '\033[94m'
    CRED = '\033[95m'
    CEND = '\033[0m'

#密码和加密方式
PASSWD="" #为空时自动生成
SS_ENCRYPT= "aes-256-cfb" #加密方式，并不是所有都兼容，有些会导致udp不通，需自行测试

#其他参数
SS_PARAM="--fast-open"
UDPSPEEDER_PARAM="-f1:3,2:4,8:6,20:10" #UDPspeeder的fec参数
KCP_SERVER_PARAM="--mode fast2"
KCP_CLIENT_PARAM="--mode fast2"
UDP2RAW_PARAM="--cipher-mode xor --auth-mode simple --raw-mode faketcp  --fix-gro -a"

#服务端默认参数
server_ip=None
server_ss_port=6443 #原生ss端口
server_name="ssserver"
server_kcptun_port=6500
server_udpspeeder_port=6501
server_udp2raw_port=4096

#客户端默认参数
client_name="ssclient"
client_ss_port=server_kcptun_port #windows，安卓等SS客户端可以连这个端口使用
client_socks5_port=1080

def get_tcp_param(select):
    return {
        0:{"KCP_SERVER_PARAM":"--mode fast2",
            "KCP_CLIENT_PARAM":"--mode fast2"},#丢包少的情况，默认
        1:{"KCP_SERVER_PARAM":"--mode fast --datashard 15 --parityshard 8",
           "KCP_CLIENT_PARAM":"--mode fast --datashard 15 --parityshard 8"}, #丢包率15%的时候，降到0.42%
        2: {"KCP_SERVER_PARAM": "--mode fast --datashard 15 --parityshard 15",
            "KCP_CLIENT_PARAM": "--mode fast --datashard 15 --parityshard 15"},#丢包率30%的时候,降到0.63%
    }[select]

def getRandomPassword(num):
    str=string.ascii_letters+string.digits
    key=random.sample(str,num)
    keys="".join(key)
    return keys

def ss_kcptun_udpspeeder(server_num=0, client_offset=0,suffix=""):
    server_cmd = f'docker rm -f {server_name}_{server_num};\\\n\
    docker run -dt \\\n\
    --restart=always \\\n\
    --name {server_name}_{server_num} \\\n\
    -p {server_ss_port+server_num}:6443 \\\n\
    -p {server_ss_port+server_num}:6443/udp \\\n\
    -p {server_kcptun_port+server_num*2}:6500/udp \\\n\
    -p {server_udpspeeder_port+server_num*2}:6501/udp \\\n\
     sola97/shadowsocks \\\n\
    -s "ss-server" \\\n\
    -S "-s 0.0.0.0 -p 6443 -m {SS_ENCRYPT} -k {PASSWD} -u {SS_PARAM}\" \\\n\
    -k "kcpserver" \\\n\
    -K "-l 0.0.0.0:6500  -t 127.0.0.1:6443 {KCP_SERVER_PARAM} " \\\n\
    -u "-s -l0.0.0.0:6501 -r 127.0.0.1:6443  {UDPSPEEDER_PARAM} -k {PASSWD}"'

    client_cmd = f'docker rm -f {client_name}{suffix};\\\n\
    docker run -dt \\\n\
    --restart=always \\\n\
    --name {client_name}{suffix} \\\n\
    -p {client_ss_port+client_offset}:6500 \\\n\
    -p {client_ss_port+client_offset}:6500/udp \\\n\
    -p {client_socks5_port+client_offset}:1080 \\\n\
    -p {client_socks5_port+client_offset}:1080/udp \\\n\
    sola97/shadowsocks \\\n\
    -s "ss-local" \\\n\
    -S "-s 127.0.0.1 -p 6500 -b 0.0.0.0 -l 1080 -u -m {SS_ENCRYPT} -k {PASSWD}  {SS_PARAM}" \\\n\
    -k "kcpclient"  \\\n\
    -K "-l :6500 -r {server_ip}:{server_kcptun_port+server_num*2} {KCP_CLIENT_PARAM}" \\\n\
    -u "-c -l[::]:6500  -r{server_ip}:{server_udpspeeder_port+server_num*2} {UDPSPEEDER_PARAM} -k {PASSWD}"'
    print(f"{CRED}↓SS + Kcptun + UDPspeeder↓{CEND}")
    print(f"服务端：\n{CBLUE}{server_cmd}{CEND}")
    print(f"客户端：\n{CBLUE}{client_cmd}{CEND}")
    print(f"{CRED}↑SS + Kcptun + UDPspeeder↑{CEND}")
    print(f"服务端原生SS端口：{server_ss_port+server_num}")
    print(f"客户端本地映射SS端口：{client_ss_port+client_offset}\n"
          f"SOCKS5端口：{client_socks5_port+client_offset}")
    print("密码为："+PASSWD) 
    print("\n")

def ss_kcptun_udpspeeder_dual_udp2raw(server_num=0, client_offset=0, suffix=""):
    server_cmd = f'docker rm -f {server_name}_{server_num};\\\n\
    docker run -dt \\\n\
    --restart=always \\\n\
    --cap-add=NET_ADMIN \\\n\
    --name {server_name}_{server_num} \\\n\
    -p {server_ss_port+server_num}:6443 \\\n\
    -p {server_ss_port+server_num}:6443/udp \\\n\
    -p {server_udp2raw_port+server_num*2}:4096 \\\n\
    -p {server_udp2raw_port+1+server_num*2}:4097 \\\n\
     sola97/shadowsocks \\\n\
    -s "ss-server" \\\n\
    -S "-s 0.0.0.0 -p 6443 -m {SS_ENCRYPT} -k {PASSWD} -u --fast-open" \\\n\
    -k "kcpserver" \\\n\
    -K "-l 0.0.0.0:6500  -t 127.0.0.1:6443 {KCP_SERVER_PARAM} " \\\n\
    -u "-s -l0.0.0.0:6501 -r 127.0.0.1:6443  {UDPSPEEDER_PARAM} -k {PASSWD}" \\\n\
    -t "-s -l0.0.0.0:4096 -r 127.0.0.1:6500    -k {PASSWD} {UDP2RAW_PARAM}" \\\n\
    -T "-s -l0.0.0.0:4097 -r 127.0.0.1:6501    -k {PASSWD} {UDP2RAW_PARAM}"'

    client_cmd = f'docker rm -f {client_name}{suffix};\\\n\
    docker run -dt \\\n\
    --cap-add=NET_ADMIN \\\n\
    --restart=always \\\n\
    --name {client_name}{suffix} \\\n\
    -p {client_ss_port+client_offset}:6500 \\\n\
    -p {client_ss_port+client_offset}:6500/udp \\\n\
    -p {client_socks5_port+client_offset}:1080 \\\n\
    -p {client_socks5_port+client_offset}:1080/udp \\\n\
    sola97/shadowsocks \\\n\
    -t "-c -l0.0.0.0:3333  -r{server_ip}:{server_udp2raw_port+server_num*2}  -k {PASSWD} {UDP2RAW_PARAM}\" \\\n\
    -T "-c -l0.0.0.0:3334  -r{server_ip}:{server_udp2raw_port+1+server_num*2}  -k {PASSWD} {UDP2RAW_PARAM}\" \\\n\
    -k "kcpclient"  \\\n\
    -K "-l :6500 -r 127.0.0.1:3333 {KCP_CLIENT_PARAM}" \\\n\
    -u "-c -l[::]:6500  -r127.0.0.1:3334 {UDPSPEEDER_PARAM} -k {PASSWD}" \\\n\
    -s "ss-local" \\\n\
    -S "-s 127.0.0.1 -p 6500 -b 0.0.0.0 -l 1080 -u -m {SS_ENCRYPT} -k {PASSWD}  {SS_PARAM}"'
    print(f"{CRED}↓SS + Kcptun+UDP2raw + UDPspeeder+UDP2raw↓{CEND}")
    print(f"服务端：\n{CBLUE}{server_cmd}{CEND}")
    print(f"客户端：\n{CBLUE}{client_cmd}{CEND}")
    print(f"{CRED}↑SS + Kcptun+UDP2raw + UDPspeeder+UDP2raw↑{CEND}")
    print(f"服务端原生SS端口：{server_ss_port+server_num}")
    print(f"客户端本地映射SS端口：{client_ss_port+client_offset}\n"
          f"SOCKS5端口：{client_socks5_port+client_offset}")
    print("密码为："+PASSWD) 
    print("\n")


def ss_kcptun_udpspeeder_udp2raw(server_num=0, client_offset=0,suffix=""):
    server_cmd = f'docker rm -f {server_name}_{server_num};\\\n\
    docker run -dt \\\n\
    --cap-add=NET_ADMIN \\\n\
    --restart=always \\\n\
    --name {server_name}_{server_num} \\\n\
    -p {server_ss_port+server_num}:6443 \\\n\
    -p {server_ss_port+server_num}:6443/udp \\\n\
    -p {server_kcptun_port+server_num*2}:6500/udp \\\n\
    -p {server_udp2raw_port+1+server_num*2}:4097 \\\n\
     sola97/shadowsocks \\\n\
    -s "ss-server" \\\n\
    -S "-s 0.0.0.0 -p 6443 -m {SS_ENCRYPT} -k {PASSWD} -u {SS_PARAM}\" \\\n\
    -k "kcpserver" \\\n\
    -K "-l 0.0.0.0:6500  -t 127.0.0.1:6443 {KCP_SERVER_PARAM} " \\\n\
    -u "-s -l0.0.0.0:6501 -r 127.0.0.1:6443  {UDPSPEEDER_PARAM} -k {PASSWD}"  \\\n\
    -t "-s -l0.0.0.0:4097 -r 127.0.0.1:6501    -k {PASSWD} {UDP2RAW_PARAM}"'

    client_cmd = f'docker rm -f {client_name}{suffix};\\\n\
    docker run -dt \\\n\
    --cap-add=NET_ADMIN \\\n\
    --restart=always \\\n\
    --name {client_name}{suffix} \\\n\
    -p {client_ss_port+client_offset}:6500 \\\n\
    -p {client_ss_port+client_offset}:6500/udp \\\n\
    -p {client_socks5_port+client_offset}:1080 \\\n\
    -p {client_socks5_port+client_offset}:1080/udp \\\n\
    sola97/shadowsocks \\\n\
    -t "-c -l0.0.0.0:3334  -r{server_ip}:{server_udp2raw_port+1+server_num*2}  -k {PASSWD} {UDP2RAW_PARAM}" \\\n\
    -k "kcpclient"  \\\n\
    -K "-l :6500 -r {server_ip}:{server_kcptun_port+server_num*2} {KCP_CLIENT_PARAM}" \\\n\
    -u "-c -l[::]:6500  -r127.0.0.1:3334 {UDPSPEEDER_PARAM} -k {PASSWD}" \\\n\
    -s "ss-local" \\\n\
    -S "-s 127.0.0.1 -p 6500 -b 0.0.0.0 -l 1080 -u -m {SS_ENCRYPT} -k {PASSWD}  {SS_PARAM}" '


    print(f"{CRED}↓SS + Kcptun + UDPspeeder+UDP2raw↓{CEND}")
    print(f"服务端：\n{CBLUE}{server_cmd}{CEND}")
    print(f"客户端：\n{CBLUE}{client_cmd}{CEND}")
    print(f"{CRED}↑SS + Kcptun + UDPspeeder+UDP2raw↑{CEND}")
    print(f"服务端原生SS端口：{server_ss_port+server_num}")
    print(f"客户端本地映射SS端口：{client_ss_port+client_offset}\n"
          f"SOCKS5端口：{client_socks5_port+client_offset}")
    print("密码为："+PASSWD)          
    print("\n")


if __name__ == '__main__':
    if not PASSWD:
        PASSWD = getRandomPassword(8)
    while True:
        input_ip=input("请输入服务器IP：")
        if re.match("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",input_ip):
            server_ip=input_ip
            break
        else:print("格式有误，请重新输入。")

    server_num=0
    client_offset=0

    sname_input=input(f"请输入服务端容器名(默认为{server_name}，回车保持默认)\n：")
    if sname_input:
        server_name=sname_input

    sn_input=input("请输入sserver容器的序号（用于运行多个容器的情况，默认为0，回车保持默认）\n：")
    if re.match("^\d+$",sn_input):
        server_num=int(sn_input)
        client_offset=int(sn_input)
    print(f"服务端docker容器名为：{server_name}_{server_num}")


    try:
        print("正在获取服务器IP的所在地...")
        with request.urlopen(f"http://ip-api.com/json/{server_ip}?lang=US-en") as f:
            data = f.read().decode('utf-8')
            client_name = "ss_"+str(json.loads(data)['countryCode']).lower()+"_"+str(json.loads(data)['region']).lower()
    except:
        print("获取失败")
        pass
    cname_input=input(f"请输入客户端容器名(默认为{client_name}，回车保持默认)\n：")
    if cname_input:
        client_name=cname_input

    print(f"客户端docker容器名为：{client_name}")
    cl_offset=input(f"客户端将使用{client_socks5_port+client_offset}端口，如需修改请输入新的偏移量，当前为{client_socks5_port}+{server_num}\n：")

    if re.match("^\d+$",cl_offset):
        client_offset=int(cl_offset)
    print(f"客户端SOCKS5端口为：{client_socks5_port+client_offset}")
    

    while True:
        print("请选择kcptun的参数")
        print("[0]."+get_tcp_param(0)["KCP_SERVER_PARAM"]+"   低丢包率下使用 [默认]")
        print("[1]." + get_tcp_param(1)["KCP_SERVER_PARAM"] + "   丢包率15%的时候，降到0.42%")
        print("[2]." + get_tcp_param(2)["KCP_SERVER_PARAM"] + "   丢包率30%的时候,降到0.63%")
        input_select = input("请输入选项：")
        if input_select in ("0","1","2",):
            KCP_SERVER_PARAM = get_tcp_param(int(input_select))['KCP_SERVER_PARAM']
            KCP_CLIENT_PARAM = get_tcp_param(int(input_select))['KCP_CLIENT_PARAM']
            print("当前kcptun参数："+get_tcp_param(int(input_select))['KCP_SERVER_PARAM'])
            break
        elif input_select=="":
            KCP_SERVER_PARAM = get_tcp_param(0)['KCP_SERVER_PARAM']
            KCP_CLIENT_PARAM = get_tcp_param(0)['KCP_CLIENT_PARAM']
            print("当前kcptun参数："+get_tcp_param(0)['KCP_SERVER_PARAM'])
            break
        else:
            print("输入错误，请重新输入")

    while True:
        print("请选择方案：")
        print("[0].退出")
        print("[1].SS + Kcptun + UDPspeeder + 单UDP2raw [默认 游戏推荐]")
        print("[2].SS + Kcptun + UDPspeeder")
        print("[3].SS + Kcptun + UDPspeeder + 双UDP2raw")
        print("[4].同时运行[2]和[3]")
        input_select = input("请输入选项：")
        if input_select == "" or input_select == "1":
            ss_kcptun_udpspeeder_udp2raw(server_num=server_num,client_offset=client_offset)
        if input_select == "2":
            ss_kcptun_udpspeeder(server_num=server_num,client_offset=client_offset)
        if input_select == "3":
            ss_kcptun_udpspeeder_dual_udp2raw(server_num=server_num, client_offset=client_offset)
        if input_select == "4":
            ss_kcptun_udpspeeder(server_num=server_num, client_offset=client_offset,suffix="")
            ss_kcptun_udpspeeder_udp2raw(server_num=server_num+1, client_offset=client_offset+1,suffix="_udp2raw")
        if input_select =="0":
            print("退出")
            break








