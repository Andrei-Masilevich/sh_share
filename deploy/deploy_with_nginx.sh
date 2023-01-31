#!/bin/bash

THIS_DIR=$(cd $(dirname ${BASH_SOURCE}) && pwd)
source ${THIS_DIR}/lib_deploy.sh

main()
{
    local AUTH_MODE=$1

    check_auth_mode $AUTH_MODE

    if [ "$AUTH_MODE" != $SH_SHARE_AUTH_NONE ]; then
        print_error "Auth is not supported for NGINX mode"
        exit 1
    fi

    shift

    init_custom_environment CUSTOM_ENVIRONMENT $1

    local BUILD_SCRIPT=${THIS_DIR}/build.sh
    if [ ! -f ${BUILD_SCRIPT} ]; then
        print_error "Build script was not found!"
        exit 1    
    fi

    local START_SCRIPT=${THIS_DIR}/start_with_nginx.sh
    if [ ! -f ${START_SCRIPT} ]; then
        print_error "Start script was not found!"
        exit 1    
    fi

    pushd $(pwd) > /dev/null

    . ${BUILD_SCRIPT} nginx
    local RES_CODE=$?
    if [ $RES_CODE -ne 0 ]; then
        exit $RES_CODE
    fi

    popd > /dev/null

    . ${START_SCRIPT} "${CUSTOM_ENVIRONMENT}"
}

main $@
