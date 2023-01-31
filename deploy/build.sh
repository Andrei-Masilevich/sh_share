#!/bin/bash

THIS_DIR=$(cd $(dirname ${BASH_SOURCE}) && pwd)
source ${THIS_DIR}/lib_deploy.sh

main()
{
    local MODE=$1
    if [ -z $MODE ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Mode is required"
        exit 1
    fi

    local SHOW_PROMPT=1
    if [ "$(basename $0)" != "$(basename $BASH_SOURCE)" ]; then
        SHOW_PROMPT=0
    fi

    init_docker 1

    pushd ${THIS_DIR}/../src/faker > /dev/null

    $DOCKER build -t wfaker.sh_share .
    if [ $? -ne 0 ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Can't build faker image!"
        exit 1
    fi

    popd > /dev/null 

    if (( ! SH_SHARE_SERVICE_TELEGRAM_OFF )); then

        pushd ${THIS_DIR}/../src/notify > /dev/null

        $DOCKER build -t telegram.sh_share .
        if [ $? -ne 0 ]; then
            print_error "($(basename ${BASH_SOURCE}):${LINENO}) Can't build notify image!"
            exit 1
        fi

        popd > /dev/null 

    fi

    pushd ${THIS_DIR}/../src/ > /dev/null

    $DOCKER build -t service.sh_share .
    if [ $? -ne 0 ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Can't build service image!"
        exit 1
    fi

    popd > /dev/null

    local DANGLING_IMAGES=$($DOCKER images -q -f dangling=true)
    if [ -n "${DANGLING_IMAGES}" ]; then
        $DOCKER rmi ${DANGLING_IMAGES}
    fi

    $DOCKER pull $(get_mode_image_name $MODE)

    local TMP_TEST=$(${UNSUDO} mktemp /tmp/sh_share.test.XXXXXX)

    $DOCKER run --rm wfaker.sh_share > ${TMP_TEST}
    if [ $? -ne 0 ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Faker doesn't work properly!"
        exit 1
    fi

    local TEST_WORDS=$(cat ${TMP_TEST}| wc -w)
    if (( TEST_WORDS != 1 )); then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Faker doesn't work properly!"
        exit 1
    fi

    rm -f ${TMP_TEST}

    if (( SHOW_PROMPT )); then
        prompt "Images have been prepared to start compose."
        echo "Run start script."
    fi
}

main $@
