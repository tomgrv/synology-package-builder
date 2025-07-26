#!/bin/bash
###############################################################################
# Change Panel Size Service - Shell Script Version                            #
# 이 스크립트는 Python 서비스 대신 shell script로 동작합니다                            #
###############################################################################

# 설정
PKG_ROOT="/var/packages/Changepanelsize"
VAR_DIR="${PKG_ROOT}/var"
LOG_FILE="${VAR_DIR}/change_panel_size.log"
PID_FILE="${VAR_DIR}/change_panel_size.pid"
BIN_DIR="${PKG_ROOT}/target/bin"
STORAGE_SCRIPT="${BIN_DIR}/storagepanel.sh"

# 로그 디렉터리 생성
mkdir -p "${VAR_DIR}"

# 로그 함수
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# PID 파일 관리 함수
write_pid() {
    echo $$ > "${PID_FILE}"
    log_message "PID $$ written to ${PID_FILE}"
}

remove_pid() {
    if [ -f "${PID_FILE}" ]; then
        rm -f "${PID_FILE}"
        log_message "PID file removed"
    fi
}

# 종료 처리 함수
cleanup() {
    log_message "Received termination signal, shutting down..."
    remove_pid
    exit 0
}

# 신호 처리 설정 (종료 신호 수신 시 cleanup 호출)
trap cleanup TERM INT

# ====== setup_storage_script 함수 및 복사 부분 제거 ======

# 스토리지 명령 실행 함수 (sudo 권한으로 실행)
# /etc/sudoers.d/Changepanelsize 파일 생성은 StoragePanel Addon 설치 시 처리함
execute_storage_command() {
    local args="$*"
    log_message "Executing storage command: ${STORAGE_SCRIPT} ${args}"

    if [ ! -f "${STORAGE_SCRIPT}" ]; then
        log_message "ERROR: Storage script not found: ${STORAGE_SCRIPT}"
        return 1
    fi

    if [ ! -x "${STORAGE_SCRIPT}" ]; then
        chmod +x "${STORAGE_SCRIPT}"
    fi

    # sudo 명령 실행 (로그 파일에 출력 및 에러 리다이렉션)
    if sudo "${STORAGE_SCRIPT}" ${args} >> "${LOG_FILE}" 2>&1; then
        log_message "Storage command executed successfully"
        return 0
    else
        local exit_code=$?
        log_message "Storage command failed with exit code: ${exit_code}"
        return ${exit_code}
    fi
}

# 메인 함수
main() {
    log_message "Starting Change Panel Size service (shell version)..."

    # HDD 베이 숫자를 RACK_XX_Bay 형식으로 변환하는 함수
    convert_hdd_bay() {
        local bay_num="$1"
        case "${bay_num}" in
            0) echo "RACK_0_Bay" ;;
            2) echo "RACK_2_Bay" ;;
            4) echo "RACK_4_Bay" ;;
            8) echo "RACK_8_Bay" ;;
            10) echo "RACK_10_Bay" ;;
            12) echo "RACK_12_Bay" ;;
            16) echo "RACK_16_Bay" ;;
            20) echo "RACK_20_Bay" ;;
            24) echo "RACK_24_Bay" ;;
            60) echo "RACK_60_Bay" ;;
            *) log_message "ERROR: Unsupported HDD bay number: ${bay_num}"
               return 1 ;;
        esac
    }

    # SSD 베이 숫자를 NxM 형식으로 변환하는 함수
    convert_ssd_bay() {
        local bay_num="$1"
        if [ "${bay_num}" -le 8 ]; then
            echo "1X${bay_num}"
        else
            # 8 단위로 행(row) 수 계산 후 "rowsX8" 형태 반환
            local rows=$((bay_num / 8 + (bay_num % 8 > 0 ? 1 : 0)))
            echo "${rows}X8"
        fi
    }

    # 파라미터 처리
    case "${1}" in
        "apply")
            HDD_BAY="${2}"
            SSD_BAY="${3}"
            if [ -z "${HDD_BAY}" ] || [ -z "${SSD_BAY}" ]; then
                log_message "ERROR: Missing parameters for apply command"
                exit 1
            fi

            log_message "Applying configuration: HDD_BAY=${HDD_BAY}, SSD_BAY=${SSD_BAY}"

            # apply 명령은 PID 파일 없이 바로 실행
            execute_storage_command "${HDD_BAY}" "${SSD_BAY}"
            exit $?
            ;;
        "restore")
            # restore 명령 역시 PID 파일 없이 바로 실행
            execute_storage_command "-r"
            exit $?
            ;;
        "daemon"|"")
            # 데몬 모드일 때만 PID 파일 작성
            write_pid
            log_message "Running in daemon mode..."

            DAEMON_RUNNING=true
            while [ "$DAEMON_RUNNING" = "true" ]; do
                # 5분 간격으로 상태 확인
                sleep 300

                # PID 파일이 없으면 종료
                if [ ! -f "${PID_FILE}" ]; then
                    log_message "PID file missing, service stopping..."
                    DAEMON_RUNNING=false
                    break
                fi

                # PID 파일 내용과 현재 프로세스 PID 일치 여부 검사
                PID=$(cat "${PID_FILE}" 2>/dev/null)
                if [ -n "${PID}" ] && [ "${PID}" = "$$" ]; then
                    # 정상 동작 로그 기록
                    log_message "Daemon running normally (PID $$)"
                else
                    log_message "PID mismatch, service may have been replaced"
                    DAEMON_RUNNING=false
                    break
                fi
            done

            # 데몬 종료 시 PID 파일 제거 및 로그 기록
            remove_pid
            log_message "Change Panel Size service stopped"
            ;;
        "-h"|"--help")
            echo "Change Panel Size Service - Shell Version"
            echo "Usage: $0 [command] [options]"
            echo "Commands:"
            echo "  apply <HDD_BAY> <SSD_BAY>  - Apply storage configuration"
            echo "  restore                    - Restore original configuration"
            echo "  daemon                     - Run as daemon (default)"
            echo "  -h, --help                 - Show this help"
            exit 0
            ;;
        *)
            log_message "ERROR: Unknown command: ${1}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
}

# 메인 함수 실행
main "$@"
