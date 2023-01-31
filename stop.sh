#!/bin/bash

THIS_DIR=$(cd $(dirname ${BASH_SOURCE}) && pwd)
source ${THIS_DIR}/deploy/lib_deploy.sh

main()
{
    local MODE=$1
    if [ -z $MODE ]; then
        print_error "Mode is required"
        exit 1
    fi

    shift
    
    check_mode $MODE

    local IMPL_SCRIPT=${THIS_DIR}/deploy/stop_with_$MODE.sh
    if [ ! -f ${IMPL_SCRIPT} ]; then
        print_error "Stop script was not found for mode = \"$MODE\"!"
        exit 1  
    fi

    . ${IMPL_SCRIPT} $@
}

main $@
