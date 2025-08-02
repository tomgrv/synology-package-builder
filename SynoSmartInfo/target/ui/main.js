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
    
        for (let i = lines.length - 1; i >= 0; i--) {
            if (lines[i].startsWith('SUCCESS: ')) {
                obj.success = true;
                obj.message = lines[i].slice(9);
                break;
            }
            if (lines[i].startsWith('ERROR: ')) {
                obj.success = false;
                obj.message = lines[i].slice(7);
                break;
            }
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
        console.log('parseSystemInfo:', info);
        return info;
    }

    // API 호출 함수
    function callAPI(action, params = {}) {
        const urlParams = new URLSearchParams();
        urlParams.append('action', action);
        Object.keys(params).forEach(key => {
            urlParams.append(key, params[key]);
        });

        // 실제 POST 데이터 확인
        console.log('callAPI:', action, params, urlParams.toString());

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
                console.log('System info response:', response);
                if (response.success) {
                    const info = parseSystemInfo(response.data);
                    systemInfo.innerHTML = `
                        <p class="sys-item"><strong>Unique ID:</strong> ${info.UNIQUE_ID || 'N/A'}</p>
                        <p class="sys-item"><strong>Build Number:</strong> ${info.BUILD_NUMBER || 'N/A'}</p>
                        <p class="sys-item"><strong>Model:</strong> ${info.MODEL || 'N/A'}</p>
                        <p class="sys-item"><strong>DSM Version:</strong> ${info.DSM_VERSION || 'N/A'}</p>
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
                    (error.message || error) +
                    '</span>';
            });
    }

    // 상태 업데이트 함수
    function updateStatus(message, type = 'info') {
        status.textContent = message;
        status.className = 'status ' + type;
        console.log(`[status ${type}] ${message}`);
    }

    // 버튼 상태 관리
    function setButtonsEnabled(enabled) {
        runBtn.disabled = !enabled;
        optionSelect.disabled = !enabled;
    }

    // SMART 결과 파일 fetch 함수
    function fetchSmartResult() {
        return fetch('/webman/3rdparty/Synosmartinfo/result/smart.result')
            .then(res => {
                if (!res.ok) throw new Error('Result file fetch failed');
                // Last-Modified 헤더 로깅
                return res.text().then(text => {
                    const lastModified = res.headers.get('last-modified');
                    console.log('smart.result fetch:', { lastModified, text: text.slice(0, 100) }); // 처음 100자만 미리보기
                    return { text, lastModified };
                });
            });
    }

    runBtn.addEventListener('click', () => {
        const selectedOption = optionSelect.value;

        updateStatus('Starting SMART scan... Please wait.', 'warning');
        output.textContent = 'Initiating SMART scan...\nPlease wait up to 2 minutes.';
        setButtonsEnabled(false);

        let timeoutId, intervalId;
        let initialModifiedTime = null;
        const timeoutMs = 4 * 60 * 1000; // 4 minutes timeout
        const pollInterval = 2000; // 2 seconds

        // 1. run 명령 요청 및 응답 로깅
        callAPI('run', { option: selectedOption })
            .then(response => {
                console.log('run response:', response);
                if (!response.success) {
                    throw new Error(response.message || 'Run command failed');
                }

                // 2. 초기 스마트 결과 파일 수정 시각 확인
                return fetchSmartResult()
                    .then(({ lastModified, text }) => {
                        initialModifiedTime = lastModified;
                        updateStatus('SMART scan started. Waiting for results...', 'info');

                        return new Promise((resolve, reject) => {
                            intervalId = setInterval(() => {
                                fetchSmartResult()
                                    .then(({ text, lastModified }) => {
                                        console.log('poll:', { lastModified, text: text.slice(0, 100) });
                                        if (lastModified && lastModified !== initialModifiedTime && text.trim()) {
                                            clearInterval(intervalId);
                                            clearTimeout(timeoutId);
                                            updateStatus('SMART scan results loaded', 'success');
                                            output.textContent = text;
                                            resolve();
                                        } else {
                                            // 기다리는 중 로그
                                            updateStatus('Waiting for SMART scan to complete...', 'info');
                                        }
                                    })
                                    .catch(err => {
                                        clearInterval(intervalId);
                                        clearTimeout(timeoutId);
                                        reject(new Error('Error fetching result file: ' + err.message));
                                    });
                            }, pollInterval);

                            timeoutId = setTimeout(() => {
                                clearInterval(intervalId);
                                reject(new Error('SMART scan timed out after 4 minutes'));
                            }, timeoutMs);
                        });
                    });
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
