#!/bin/bash
###############################################################################
# Change Panel Size Service - Shell Script Version                          #
# 이 스크립트는 Python 서비스 대신 shell script로 동작합니다               #
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

# 종료 처리
cleanup() {
    log_message "Received termination signal, shutting down..."
    remove_pid
    exit 0
}

# 신호 처리 설정
trap cleanup TERM INT

# 스토리지 스크립트 설정
setup_storage_script() {
    # 디렉터리 생성
    mkdir -p "${BIN_DIR}"
    
    # 소스 스크립트 복사
    SOURCE_SCRIPT="/Users/yujin/Documents/dev/tcrp-package/new/bin/storagepanel.sh"
    if [ -f "${SOURCE_SCRIPT}" ] && [ ! -f "${STORAGE_SCRIPT}" ]; then
        cp "${SOURCE_SCRIPT}" "${STORAGE_SCRIPT}"
        chmod +x "${STORAGE_SCRIPT}"
        log_message "Copied storage script to ${STORAGE_SCRIPT}"
    elif [ ! -f "${STORAGE_SCRIPT}" ]; then
        log_message "ERROR: Storage script not found at ${SOURCE_SCRIPT}"
        return 1
    fi
    
    return 0
}

# 스토리지 명령 실행
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
    
    # 명령 실행
    if "${STORAGE_SCRIPT}" ${args} >> "${LOG_FILE}" 2>&1; then
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
    
    # 스토리지 스크립트 설정
    if ! setup_storage_script; then
        log_message "Failed to setup storage script"
        exit 1
    fi
    
    # PID 파일 작성
    write_pid
    
    # 파라미터 처리
    case "${1}" in
        "apply")
            HDD_BAY="${2}"
            SSD_BAY="${3}"
            if [ -z "${HDD_BAY}" ] || [ -z "${SSD_BAY}" ]; then
                log_message "ERROR: Missing parameters for apply command"
                exit 1
            fi
            execute_storage_command "${HDD_BAY}" "${SSD_BAY}"
            exit $?
            ;;
        "restore")
            execute_storage_command "-r"
            exit $?
            ;;
        "daemon"|"")
            # 데몬 모드로 실행
            log_message "Running in daemon mode..."
            
            # 백그라운드에서 실행될 때는 계속 실행 상태 유지
            while true; do
                sleep 30
                
                # PID 파일이 삭제되면 종료
                if [ ! -f "${PID_FILE}" ]; then
                    log_message "PID file missing, service stopping..."
                    break
                fi
                
                # 프로세스가 여전히 실행 중인지 확인
                if [ -f "${PID_FILE}" ]; then
                    PID=$(cat "${PID_FILE}" 2>/dev/null)
                    if [ -n "${PID}" ] && [ "${PID}" = "$$" ]; then
                        # 정상 동작 중
                        continue
                    else
                        log_message "PID mismatch, service may have been replaced"
                        break
                    fi
                fi
            done
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
    
    # 정리
    remove_pid
    log_message "Change Panel Size service stopped"
}

# 메인 함수 실행
main "$@"
