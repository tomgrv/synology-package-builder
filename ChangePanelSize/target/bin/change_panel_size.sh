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
    
    # 소스 스크립트 복사 - 패키지 내에서 찾기
    PACKAGE_SOURCE="${PKG_ROOT}/target/bin/storagepanel.sh"
    DEV_SOURCE="/usr/local/packages/Changepanelsize/bin/storagepanel.sh"
    
    if [ ! -f "${STORAGE_SCRIPT}" ]; then
        if [ -f "${PACKAGE_SOURCE}" ]; then
            cp "${PACKAGE_SOURCE}" "${STORAGE_SCRIPT}"
            chmod +x "${STORAGE_SCRIPT}"
            log_message "Copied storage script from package to ${STORAGE_SCRIPT}"
        elif [ -f "${DEV_SOURCE}" ]; then
            cp "${DEV_SOURCE}" "${STORAGE_SCRIPT}"
            chmod +x "${STORAGE_SCRIPT}"
            log_message "Copied storage script from dev location to ${STORAGE_SCRIPT}"
        else
            log_message "ERROR: Storage script not found in package or dev locations"
            return 1
        fi
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
    
    # HDD 베이 숫자를 RACK_X_Bay 형식으로 변환하는 함수
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
            
            # apply 모드는 PID 파일 없이 바로 실행
            execute_storage_command "${HDD_BAY}" "${SSD_BAY}"
            exit $?
            ;;
        "restore")
            # restore 모드는 PID 파일 없이 바로 실행
            execute_storage_command "-r"
            exit $?
            ;;
        "daemon"|"")
            # 데몬 모드만 PID 파일 생성
            write_pid
            log_message "Running in daemon mode..."
            
            # 백그라운드에서 실행될 때는 계속 실행 상태 유지
            DAEMON_RUNNING=true
            while [ "$DAEMON_RUNNING" = "true" ]; do
                # 더 긴 간격으로 체크 (5분)
                sleep 300
                
                # PID 파일이 삭제되면 종료
                if [ ! -f "${PID_FILE}" ]; then
                    log_message "PID file missing, service stopping..."
                    DAEMON_RUNNING=false
                    break
                fi
                
                # 프로세스가 여전히 실행 중인지 확인
                PID=$(cat "${PID_FILE}" 2>/dev/null)
                if [ -n "${PID}" ] && [ "${PID}" = "$$" ]; then
                    # 정상 동작 중 - 주기적으로 상태 로그
                    log_message "Daemon running normally (PID $$)"
                else
                    log_message "PID mismatch, service may have been replaced"
                    DAEMON_RUNNING=false
                    break
                fi
            done
            # 데몬 모드에서만 정리 작업 수행
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
