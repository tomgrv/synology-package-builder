document.addEventListener('DOMContentLoaded', () => {
    const optionSelect = document.getElementById('optionSelect');
    const runBtn = document.getElementById('runBtn');
    const status = document.getElementById('status');
    const output = document.getElementById('output');
    const systemInfo = document.getElementById('systemInfo');

    // API 호출 함수 - URLSearchParams 사용으로 변경
    function callAPI(action, params = {}) {
        const urlParams = new URLSearchParams();
        urlParams.append('action', action);
        
        Object.keys(params).forEach(key => {
            urlParams.append(key, params[key]);
        });

        return fetch('api.cgi', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: urlParams.toString()
        })
        .then(res => {
            if (!res.ok) {
                throw new Error(`HTTP ${res.status} - ${res.statusText}`);
            }
            return res.json();
        });
    }

    // 시스템 정보 로드 함수
    function loadSystemInfo() {
        callAPI('info')
        .then(data => {
            if (data.success) {
                systemInfo.innerHTML = `
                    <strong>Unique ID:</strong>
                    <span>${data.unique || 'N/A'}</span>
                    <strong>Build Number:</strong>
                    <span>${data.build || 'N/A'}</span>
                    <strong>Model:</strong>
                    <span>${data.model || 'N/A'}</span>
                    <strong>DSM Version:</strong>
                    <span>${data.version || 'N/A'}</span>
                `;
            } else {
                systemInfo.innerHTML = '<span style="color: red;">Failed to load system information: ' + (data.message || 'Unknown error') + '</span>';
            }
        })
        .catch(error => {
            systemInfo.innerHTML = '<span style="color: red;">Error loading system information: ' + error.message + '</span>';
        });
    }

    // 상태 업데이트 함수
    function updateStatus(message, type = 'info') {
        status.textContent = message;
        status.className = 'status ' + type;
    }

    // 버튼 상태 관리
    function setButtonsEnabled(enabled) {
        runBtn.disabled = !enabled;
        optionSelect.disabled = !enabled;
    }

    // RUN 버튼 이벤트
    runBtn.addEventListener('click', () => {
        const selectedOption = optionSelect.value;

        updateStatus('실행 중... 잠시만 기다려주세요.', 'warning');
        output.textContent = 'Processing...';
        setButtonsEnabled(false);

        callAPI('run', { option: selectedOption })
        .then(data => {
            if (data.success) {
                updateStatus('성공: ' + data.message, 'success');
                
                if (data.result) {
                    output.textContent = data.result;
                } else {
                    output.textContent = '결과가 없습니다.';
                }
            } else {
                updateStatus('실패: ' + data.message, 'error');
                output.textContent = 'Error: ' + data.message;
            }
        })
        .catch(error => {
            updateStatus('오류: ' + error.message, 'error');
            output.textContent = 'Error occurred: ' + error.message;
        })
        .finally(() => {
            setButtonsEnabled(true);
        });
    });

    // 페이지 로드 시 시스템 정보 자동 로드
    loadSystemInfo();
});
