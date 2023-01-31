#!/bin/bash

function print_error()
{
    echo $@ >&2
}

function __init_sudo()
{
    if [[ $EUID -ne 0 ]]; then
        SUDO="sudo"
        LOGIN=${USER}
        UNSUDO=""
    else
        SUDO=""
        LOGIN=$(who | awk '{print $1; exit}')
        UNSUDO="sudo -u ${LOGIN}"
    fi
}

function init_docker()
{
    __init_sudo

    if [ -z $(which docker) ]; then
        local INSTALL_DOCKER=$1
        if (( INSTALL_DOCKER )); then
            ${SUDO} curl -sSL get.docker.com | sh
            if [[ $? -ne 0 || -z $(which docker) ]]; then
                print_error "Docker is required but can not have install automatically!"
                exit 1
            fi
        else
            print_error "Docker is required!"
            exit 1
        fi
    fi

    if [ -n "${SUDO}" ]; then
        local USER_GROUPS_=($(${UNSUDO} groups))
        local SUDO_REQUIRED=1
        for group in "${USER_GROUPS_[@]}"; do 
            if [ "${group}" == "docker" ]; then
                SUDO_REQUIRED=0
                break
            fi
        done

        if (( SUDO_REQUIRED )); then
            DOCKER="$SUDO docker"
            return 0
        fi
    fi

    DOCKER="docker"
}

function get_mode_image_name()
{
    local MODE=$1
    if [ -z $MODE ]; then
        print_error "Mode is required"
        exit 1
    fi

    case "$MODE" in
        nginx) 
        echo "nginx"
        ;;
        squid)
        echo "ubuntu/squid"
        ;;
        *)
        print_error "Mode \"$MODE\" is not supported"
        exit 1
        ;;
    esac
}

function check_mode()
{
    get_mode_image_name $@ >/dev/null
}

__PROMPT_SEPARATOR_CHAR='!'

function prompt()
{
    local MESSAGE=$1
    local SYMBOL=$2

    if [ -z $SYMBOL ]; then
        SYMBOL=$__PROMPT_SEPARATOR_CHAR
    else
        SYMBOL=${SYMBOL::1}
    fi

    local LINE_L=$((${#MESSAGE}))
    local SYMB_I=0
    for ((;SYMB_I<$LINE_L; SYMB_I=SYMB_I+1)) do
        printf $SYMBOL
    done
    echo
    echo ${MESSAGE}
}

SH_SHARE_AUTH_NONE='--'
SH_SHARE_AUTH_BASIC='basic'
SH_SHARE_AUTH_DIGEST='digest'

function check_auth_mode()
{
    local MODE=$1
    if [ -z $MODE ]; then
        print_error "Auth mode is required"
        exit 1
    fi

    case "$MODE" in
        $SH_SHARE_AUTH_NONE) 
        ;;
        $SH_SHARE_AUTH_BASIC)
        ;;
        $SH_SHARE_AUTH_DIGEST)
        ;;
        *)
        print_error "Auth mode \"$MODE\" is not supported"
        exit 1
        ;;
    esac
}

function init_custom_environment()
{
    declare -n CUSTOM_ENVIRONMENT_=$1 
    local _CUSTOM_ENVIRONMENT=$2
    if [ -z ${_CUSTOM_ENVIRONMENT} ]; then
        local THIS_DIR=$(cd $(dirname ${BASH_SOURCE}) && pwd)
        _CUSTOM_ENVIRONMENT=${THIS_DIR}/../.env
    fi

    if [ ! -f ${_CUSTOM_ENVIRONMENT} ]; then
        print_error "Custom environment file is not found"
        exit 1
    fi

    . ${_CUSTOM_ENVIRONMENT}
    if [ -n "${SH_SHARE_SERVICE_TELEGRAM_OFF}" ]; then
        if [[ ${SH_SHARE_SERVICE_TELEGRAM_OFF} =~ ^[Tt]+[Rr]+[Uu]+[Ee]+$ ]]; then
            SH_SHARE_SERVICE_TELEGRAM_OFF=1
        else
            SH_SHARE_SERVICE_TELEGRAM_OFF=0
        fi
    fi

    CUSTOM_ENVIRONMENT_="$(realpath ${_CUSTOM_ENVIRONMENT})"
}
