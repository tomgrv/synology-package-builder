document.addEventListener('DOMContentLoaded', () => {
    const optionSelect = document.getElementById('optionSelect');
    const runBtn = document.getElementById('runBtn');
    const status = document.getElementById('status');
    const output = document.getElementById('output');
    const systemInfo = document.getElementById('systemInfo');

    // API 호출 함수
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
            return res.text();
        })
        .then(text => {
            try {
                return JSON.parse(text);
            } catch (error) {
                console.error('JSON Parse Error:', error);
                console.error('Response Text:', text);
                throw new Error('Invalid JSON response from server');
            }
        });
    }

    // 시스템 정보 로드 함수
    function loadSystemInfo() {
        systemInfo.innerHTML = '<span style="color: #0066cc;">Loading system information...</span>';
        
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
            console.error('System info error:', error);
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

        updateStatus('SMART 검사 실행 중... 잠시만 기다려주세요.', 'warning');
        output.textContent = 'SMART 검사를 실행하고 있습니다...\n이 작업은 최대 2분까지 소요될 수 있습니다.';
        setButtonsEnabled(false);

        callAPI('run', { option: selectedOption })
        .then(data => {
            if (data.success) {
                updateStatus('성공: ' + data.message, 'success');
                
                if (data.result && data.result.trim()) {
                    // 결과가 있으면 표시
                    output.textContent = data.result;
                } else {
                    // 결과가 없으면 결과 파일 직접 읽기 시도
                    updateStatus('결과 파일을 읽는 중...', 'warning');
                    setTimeout(() => {
                        fetch('/webman/3rdparty/Synosmartinfo/result/smart.result')
                        .then(res => res.text())
                        .then(text => {
                            if (text && text.trim()) {
                                output.textContent = text;
                                updateStatus('SMART 검사 결과를 성공적으로 로드했습니다', 'success');
                            } else {
                                output.textContent = '결과 파일이 비어있습니다.';
                                updateStatus('결과 파일이 비어있습니다', 'warning');
                            }
                        })
                        .catch(err => {
                            output.textContent = '결과 파일을 읽을 수 없습니다: ' + err.message;
                            updateStatus('결과 파일 읽기 실패', 'error');
                        });
                    }, 1000);
                }
            } else {
                updateStatus('실패: ' + data.message, 'error');
                output.textContent = 'Error: ' + data.message;
                if (data.result) {
                    output.textContent += '\n\nDetails:\n' + data.result;
                }
            }
        })
        .catch(error => {
            console.error('Run command error:', error);
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
