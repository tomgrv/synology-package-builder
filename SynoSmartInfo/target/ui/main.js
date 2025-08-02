document.addEventListener('DOMContentLoaded', () => {
    const optionSelect = document.getElementById('optionSelect');
    const runBtn = document.getElementById('runBtn');
    const status = document.getElementById('status');
    const output = document.getElementById('output');
    const systemInfo = document.getElementById('systemInfo');

    // TEXT 응답 파싱
    function parseTextResponse(text) {
        const lines = text.split('\n');
        const obj = { success: false, message: '', data: null };

        if (lines[0].startsWith('SUCCESS: ')) {
            obj.success = true;
            obj.message = lines[0].slice(9);
        } else if (lines[0].startsWith('ERROR: ')) {
            obj.message = lines[0].slice(7);
        } else {
            obj.message = lines[0];
        }

        const s = lines.indexOf('DATA_START');
        const e = lines.indexOf('DATA_END');
        if (s !== -1 && e !== -1 && s < e) {
            obj.data = lines.slice(s + 1, e).join('\n');
        }
        return obj;
    }

    // 시스템 정보 파싱 함수
    function parseSystemInfo(data) {
        const info = {};
        data.split('\n').forEach(line => {
            const colonIndex = line.indexOf(': ');
            if (colonIndex !== -1) {
                const key = line.substring(0, colonIndex).trim();
                const value = line.substring(colonIndex + 2).trim();
                info[key] = value;
            }
        });
        return info;
    }

    // API 호출 함수
    function callAPI(action, params = {}) {
        const urlParams = new URLSearchParams();
        urlParams.append('action', action);
        Object.keys(params).forEach(key => {
            urlParams.append(key, params[key]);
        });

        return fetch('api.cgi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: urlParams.toString()
        })
        .then(res => res.text())
        .then(parseTextResponse);
    }

    // 시스템 정보 로드 함수
    function loadSystemInfo() {
        systemInfo.innerHTML = '<span style="color: #0066cc;">Loading system information...</span>';

        callAPI('info')
            .then(response => {
                if (response.success) {
                    const info = parseSystemInfo(response.data);
                    systemInfo.innerHTML = `
                        <strong>Unique ID:</strong> <span>${info.UNIQUE_ID || 'N/A'}</span><br>
                        <strong>Build Number:</strong> <span>${info.BUILD_NUMBER || 'N/A'}</span><br>
                        <strong>Model:</strong> <span>${info.MODEL || 'N/A'}</span><br>
                        <strong>DSM Version:</strong> <span>${info.DSM_VERSION || 'N/A'}</span>
                    `;
                } else {
                    systemInfo.innerHTML =
                        '<span style="color: red;">Failed to load system information: ' +
                        (response.message || 'Unknown error') +
                        '</span>';
                }
            })
            .catch(error => {
                console.error('System info error:', error);
                systemInfo.innerHTML =
                    '<span style="color: red;">Error loading system information: ' +
                    error.message +
                    '</span>';
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

        updateStatus('Running SMART scan... Please wait.', 'warning');
        output.textContent = 'SMART scan is in progress...\nThis operation may take up to 2 minutes.';
        setButtonsEnabled(false);

        callAPI('run', { option: selectedOption })
            .then(response => {
                if (response.success) {
                    updateStatus('Success: ' + response.message, 'success');

                    if (response.data && response.data.trim()) {
                        // ANSI 처리 제거: 순수 텍스트로 출력
                        output.textContent = response.data;
                    } else {
                        updateStatus('Loading result file...', 'warning');
                        setTimeout(() => {
                            fetch('/webman/3rdparty/Synosmartinfo/result/smart.result')
                                .then(res => res.text())
                                .then(text => {
                                    if (text && text.trim()) {
                                        // ANSI 처리 제거: 순수 텍스트로 출력
                                        output.textContent = text;
                                        updateStatus('SMART scan results loaded successfully', 'success');
                                    } else {
                                        output.textContent = 'Result file is empty.';
                                        updateStatus('Result file is empty', 'warning');
                                    }
                                })
                                .catch(err => {
                                    output.textContent = 'Cannot read result file: ' + err.message;
                                    updateStatus('Failed to read result file', 'error');
                                });
                        }, 1000);
                    }
                } else {
                    updateStatus('Failed: ' + response.message, 'error');

                    if (response.data && response.data.trim()) {
                        // ANSI 처리 제거: 순수 텍스트로 에러 세부정보 출력
                        output.textContent = 'Error: ' + response.message + '\n\nDetails:\n' + response.data;
                    } else {
                        output.textContent = 'Error: ' + response.message;
                    }
                }
            })
            .catch(error => {
                console.error('Run command error:', error);
                updateStatus('Error: ' + error.message, 'error');
                output.textContent = 'Error occurred: ' + error.message;
            })
            .finally(() => {
                setButtonsEnabled(true);
            });
    });

    // 페이지 로드 시 시스템 정보 자동 로드
    loadSystemInfo();
});
