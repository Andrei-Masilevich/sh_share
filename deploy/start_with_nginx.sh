#!/bin/bash

THIS_DIR=$(cd $(dirname ${BASH_SOURCE}) && pwd)
source ${THIS_DIR}/lib_deploy.sh

main()
{
    init_custom_environment CUSTOM_ENVIRONMENT $1

    local MODE=nginx

    if [ ! -f ${THIS_DIR}/compose-with-$MODE.yaml ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Compose file 'compose-with-$MODE.yaml' was not found"
        exit 1
    fi

    local STOP_SCRIPT=${THIS_DIR}/stop_with_$MODE.sh
    if [ ! -f ${STOP_SCRIPT} ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Stop script '${STOP_SCRIPT}' was not found"
        exit 1
    fi

    . ${STOP_SCRIPT} "${MODE}"

    init_docker

    local INSTALLED_FAKER=$($DOCKER images -q wfaker.sh_share)
    if [ ! -n "${INSTALLED_FAKER}" ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Build is required. Run \"build.sh $MODE\" script."
        exit 1
    fi

    if (( ! SH_SHARE_SERVICE_TELEGRAM_OFF )); then

        local INSTALLED_NOTIFIER=$($DOCKER images -q telegram.sh_share)
        if [ ! -n "${INSTALLED_NOTIFIER}" ]; then
            print_error "($(basename ${BASH_SOURCE}):${LINENO}) Build is required. Run \"build.sh $MODE\" script."
            exit 1
        fi

    fi

    local INSTALLED_SERVICE=$($DOCKER images -q service.sh_share)
    if [ ! -n "${INSTALLED_SERVICE}" ]; then
        print_error "Build is required. Run \"build.sh $MODE\" script."
        exit 1
    fi

    local SHADOW=$($DOCKER run --rm wfaker.sh_share 2>/dev/null)
    if [ ! -n "${SHADOW}" ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Faker doesn't work properly!"
        exit 1
    fi

    local TEST_WORDS=$(cat ${TMP_TEST}| wc -w)
    if (( TEST_WORDS != 1 )); then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Faker doesn't work properly!"
        exit 1
    fi

    export SH_SHARE_SERVICE_SHADOW=${SHADOW}
    
    if (( SH_SHARE_SERVICE_TELEGRAM_OFF )); then
        $DOCKER compose -f ${THIS_DIR}/compose-with-$MODE.yaml --env-file "${CUSTOM_ENVIRONMENT}" up -d
    else
        $DOCKER compose -f ${THIS_DIR}/compose-with-${MODE}-telegram.yaml --env-file "${CUSTOM_ENVIRONMENT}" up -d
    fi
    if [ $? -ne 0 ]; then
        print_error "($(basename ${BASH_SOURCE}):${LINENO}) Can't start service"
        exit 1
    fi

    prompt "Has been run at 8080/8443. Map these port to the corresponding 80/443. "
    echo "Current shadow: ${SHADOW}                                                "
    echo "Forward interface and ports (80/443) for service publishing.             "
    echo
    echo "Restart this service with command:                                       "
    echo "  start nginx \"${CUSTOM_ENVIRONMENT}\"                                  "
    echo "Stop:                                                                    "
    echo "  stop nginx                                                             "
    echo

    return 0
}

main $@

