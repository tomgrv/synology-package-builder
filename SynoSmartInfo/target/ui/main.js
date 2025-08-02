document.addEventListener('DOMContentLoaded', () => {
    const optionSelect = document.getElementById('optionSelect');
    const runBtn = document.getElementById('runBtn');
    const status = document.getElementById('status');
    const output = document.getElementById('output');
    const systemInfo = document.getElementById('systemInfo');

    // 시스템 정보 파싱 함수 (텍스트 -> 키값 객체)
    function parseSystemInfo(data) {
        if (!data) return {};
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

    // API 호출 함수 (JSON 응답 기대)
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
        .then(res => {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json();  // JSON 파싱
        });
    }

    // 시스템 정보 로드 함수
    function loadSystemInfo() {
        callAPI('info')
        .then(data => {
            if (data.success) {
                systemInfo.innerHTML = `
                    <strong>MODEL:</strong>
                    <span>${data.model || 'N/A'}</span>
                    <strong>PLATFORM:</strong>
                    <span>${data.platform || 'N/A'}</span>
                    <strong>DSM_VERSION:</strong>
                    <span>${data.version || 'N/A'}</span>
                    <strong>Update:</strong>
                    <span>${data.smallfix || 'N/A'}</span>
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

    // 스마트 결과 파일 fetch 함수 (필요시 유지 또는 제거)
    function fetchSmartResult() {
        return fetch('/webman/3rdparty/Synosmartinfo/result/smart.result')
            .then(res => {
                if (!res.ok) throw new Error('Result file fetch failed');
                return res.text().then(text => {
                    return { text, lastModified: res.headers.get('last-modified') };
                });
            });
    }

    runBtn.addEventListener('click', () => {
        const selectedOption = optionSelect.value;

        updateStatus('Starting SMART scan... Please wait.', 'warning');
        output.textContent = 'Initiating SMART scan...\nPlease wait up to 2 minutes.';
        setButtonsEnabled(false);

        callAPI('run', { option: selectedOption })
            .then(response => {
                if (response.success) {
                    updateStatus('Success: ' + response.message, 'success');

                    if (response.result && response.result.trim()) {
                        output.textContent = response.result;
                    } else {
                        output.textContent = 'No SMART result data returned.';
                    }
                } else {
                    updateStatus('Failed: ' + response.message, 'error');
                    output.textContent = 'Error: ' + response.message;
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
//
