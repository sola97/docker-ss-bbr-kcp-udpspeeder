#!/bin/bash

SS_CONFIG=${SS_CONFIG:-""}
SS_MODULE=${SS_MODULE:-"ss-server"}
KCP_CONFIG=${KCP_CONFIG:-""}
KCP_MODULE=${KCP_MODULE:-"kcpserver"}
RNGD_FLAG=${RNGD_FLAG:-"false"}
UDPSPEEDER_MODULE="speederv2"
UDPSPEEDER_CONFIG=${UDPSPEEDER_CONFIG:-""}
UDP2RAW_MODULE="udp2raw"
UDP2RAW_CONFIG_ONE=${UDP2RAW_CONFIG_ONE:-""}
UDP2RAW_CONFIG_TWO=${UDP2RAW_CONFIG_TWO:-""}
delay=0
while getopts "S:s:K:k:u:t:T:g" OPT; do
    case $OPT in
        S)
            SS_CONFIG=$OPTARG;;
        s)
            SS_MODULE=$OPTARG;;
        K)
            KCP_CONFIG=$OPTARG;;
        k)
            KCP_MODULE=$OPTARG;;
        u)
            UDPSPEEDER_CONFIG=$OPTARG;;
        t)
            UDP2RAW_CONFIG_ONE=$OPTARG;;
        T) 
            UDP2RAW_CONFIG_TWO=$OPTARG;;
        g)
            RNGD_FLAG="true";;

    esac
done

if [ "${RNGD_FLAG}" == "true" ]; then
    echo -e "\033[32mUse /dev/urandom to quickly generate high-quality random numbers......\033[0m"
    rngd -r /dev/urandom
fi

if [ "${KCP_CONFIG}" != "" ]; then
    echo -e "\033[32mStarting kcptun......\033[0m"
    ${KCP_MODULE} ${KCP_CONFIG} 2>&1 &
else
    echo -e "\033[33mKcptun not started......\033[0m"
fi

if [ "${UDPSPEEDER_CONFIG}" != "" ]; then
    echo -e "\033[32mStarting UDPSpeeder......\033[0m"
    ${UDPSPEEDER_MODULE} ${UDPSPEEDER_CONFIG} 2>&1 &
else
    echo -e "\033[33mUDPSpeeder not started......\033[0m"
fi

if [ "${UDP2RAW_CONFIG_ONE}" != "" ]; then
    delay=`expr $delay + 5`
    echo -e "\033[32mStarting first udp2raw......\033[0m"
    ${UDP2RAW_MODULE} ${UDP2RAW_CONFIG_ONE} 2>&1 &
else
    echo -e "\033[33mfirst udp2raw not started......\033[0m"
fi
if [ "${UDP2RAW_CONFIG_TWO}" != "" ]; then
    sleep $delay
    echo -e "\033[32mStarting second udp2raw......\033[0m"
    ${UDP2RAW_MODULE} ${UDP2RAW_CONFIG_TWO} 2>&1 &
else
    echo -e "\033[33msecond udp2raw not started......\033[0m"
fi

if [ "${SS_CONFIG}" != "" ]; then
    echo -e "\033[32mStarting shadowsocks......\033[0m"
    ${SS_MODULE} ${SS_CONFIG}
else
    echo -e "\033[31mError: SS_CONFIG is blank!\033[0m"
    exit 1
fi
