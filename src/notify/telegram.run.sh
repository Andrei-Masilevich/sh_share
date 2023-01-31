#!/bin/bash

ACCEPT_COMMAND=${SH_SHARE_SERVICE_TELEGRAM_ACCEPT_COMMAND}
if [ -z ${ACCEPT_COMMAND} ]; then
    echo "Telegram command is required" >&2
    exit 1
fi

NOTIFY_URL="https://${SH_SHARE_SERVICE_DOMAIN}/${SH_SHARE_SERVICE_SHADOW}"
CONFIG_TPL_FILE=$1
CONFIG_FILE=./notify.yaml

if [ ! -f ${CONFIG_FILE} ]; then
    if [ ! -f ${CONFIG_TPL_FILE} ]; then
        echo "Config file template is required" >&2
        exit 1
    fi

    if [[ ! -n "${SH_SHARE_SERVICE_TELEGRAM_BOT_TOKEN}" || ! -n "${SH_SHARE_SERVICE_TELEGRAM_CHANNEL_ID}" ]]; then
        echo "Telegram credentials are required" >&2
        exit 1
    fi

    cat ${CONFIG_TPL_FILE} \
            | sed s+'${NOTIFY_COMMAND}'+${ACCEPT_COMMAND}+ \
            | sed s+'${NOTIFY_MESSAGE}'+${NOTIFY_URL}+ \
            | sed s+'${TELEGRAM_BOT_TOKEN}'+${SH_SHARE_SERVICE_TELEGRAM_BOT_TOKEN}+ \
            | sed s+'${TELEGRAM_CHANNEL_ID}'+${SH_SHARE_SERVICE_TELEGRAM_CHANNEL_ID}+ \
            > ${CONFIG_FILE}
fi

exec python ./telegram/notify.py -d ${CONFIG_FILE}
