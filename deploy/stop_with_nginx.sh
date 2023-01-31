#!/bin/bash

THIS_DIR=$(cd $(dirname ${BASH_SOURCE}) && pwd)
source ${THIS_DIR}/lib_deploy.sh

__show_help()
{
    echo "Usage                                             "
    echo "  "$(basename $0) "(options)                      "
    echo "Stop service and make cleanup image processes.    "
    echo "__________________________________________________"
    echo " -a  All. Remove cron reload task.                "
    echo
}

main()
{
    local CLEANUP_ALL=
    while getopts 'ah' OPTION; do
    case "$OPTION" in
        a) 
        CLEANUP_ALL=1
        ;;
        h|?)
        __show_help
        [ $OPTION = h ] && exit 0
        [ $OPTION = ? ] && exit 1
        ;;
    esac
    done

    local MODE=nginx

    if [ ! -f ${THIS_DIR}/compose-with-$MODE.yaml ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Compose file 'compose-with-$MODE.yaml' was not found"
        exit 1
    fi

    init_docker

    local HAS_STOPPED=

    local PS_IMAGES=$(${DOCKER} ps -q -a --filter="name=telegram.sh_share")
    if [ -n "${PS_IMAGES}" ]; then
        ${DOCKER} kill ${PS_IMAGES} # speed up. Grasefull stop is not required
        ${DOCKER} rm -f ${PS_IMAGES}
        HAS_STOPPED=1
    fi

    PS_IMAGES=$(${DOCKER} ps -q -a --filter="name=service.sh_share")
    if [ -n "${PS_IMAGES}" ]; then
        ${DOCKER} stop ${PS_IMAGES}
        ${DOCKER} rm -f ${PS_IMAGES}
        HAS_STOPPED=1
    fi

    PS_IMAGES=$(${DOCKER} ps -q -a --filter="name=nginx.sh_share")
    if [ -n "${PS_IMAGES}" ]; then
        ${DOCKER} stop ${PS_IMAGES}
        ${DOCKER} rm -f ${PS_IMAGES}
        HAS_STOPPED=1
    fi

    local VRT_NETWORKS=$(${DOCKER} network ls -q --filter='name=sh_share')
    if [ -n "${VRT_NETWORKS}" ]; then
        ${DOCKER} network rm ${VRT_NETWORKS}
        HAS_STOPPED=1
    fi

    if (( CLEANUP_ALL )); then
        # It could have been added by Ansible
        if [ -n "$(crontab -l | grep -v 'sh_share/start.sh ')" ]; then
            crontab -l | grep -v 'sh_share/start.sh ' | egrep -v '^#' | crontab -
            HAS_STOPPED=1
        fi 
    fi

    if (( HAS_STOPPED )); then
        prompt "Has been stopped."
    fi

    return 0
}

main $@

