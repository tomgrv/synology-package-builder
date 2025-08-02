document.addEventListener('DOMContentLoaded', () => {
    const smartOutput = document.getElementById('smartOutput');
    const status = document.getElementById('status');
    const systemInfo = document.getElementById('systemInfo');
    
    const scanBtn = document.getElementById('scanBtn');
    const generateBtn = document.getElementById('generateBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const healthBtn = document.getElementById('healthBtn');
    const testBtn = document.getElementById('testBtn');
    
    const driveInput = document.getElementById('driveInput');
    const testType = document.getElementById('testType');

    // API 호출 함수
    function callAPI(action, params = {}) {
        const formData = new FormData();
        formData.append('action', action);
        
        Object.keys(params).forEach(key => {
            formData.append(key, params[key]);
        });

        return fetch('api.cgi', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .catch(error => {
            throw new Error('API call failed: ' + error.message);
        });
    }

    // 시스템 정보 로드
    function loadSystemInfo() {
        callAPI('info')
        .then(data => {
            if (data.success) {
                systemInfo.innerHTML = `
                    <strong>Unique ID:</strong> ${data.unique || 'N/A'}<br>
                    <strong>Build Number:</strong> ${data.build || 'N/A'}
                `;
            } else {
                systemInfo.innerHTML = 'Failed to load system information';
            }
        })
        .catch(error => {
            systemInfo.innerHTML = 'Error: ' + error.message;
        });
    }

    // 상태 업데이트
    function updateStatus(message, isError = false) {
        status.textContent = message;
        status.className = 'status ' + (isError ? 'error' : 'success');
    }

    // 버튼 상태 관리
    function setButtonsEnabled(enabled) {
        [scanBtn, generateBtn, refreshBtn, healthBtn, testBtn].forEach(btn => {
            btn.disabled = !enabled;
        });
    }

    // 결과 파일 읽기
    function fetchResults() {
        fetch('/webman/3rdparty/Synosmartinfo/result/smart.result')
        .then(res => {
            if (!res.ok) throw new Error("Result file not found");
            return res.text();
        })
        .then(text => {
            smartOutput.textContent = text;
            updateStatus("Results loaded successfully");
        })
        .catch(err => {
            smartOutput.textContent = "No results available. Please run a scan first.";
            updateStatus("Error loading results: " + err.message, true);
        });
    }

    // 전체 SMART 스캔
    scanBtn.addEventListener('click', () => {
        updateStatus("Running SMART scan...");
        setButtonsEnabled(false);
        smartOutput.textContent = "Scanning drives, please wait...";

        callAPI('scan')
        .then(data => {
            if (data.success) {
                updateStatus("SMART scan completed successfully");
                // 잠시 후 결과 로드
                setTimeout(fetchResults, 1000);
            } else {
                updateStatus("SMART scan failed: " + data.message, true);
                smartOutput.textContent = "Scan failed: " + data.message;
            }
        })
        .catch(error => {
            updateStatus("Error: " + error.message, true);
            smartOutput.textContent = "Error occurred: " + error.message;
        })
        .finally(() => {
            setButtonsEnabled(true);
        });
    });

    // 리포트 생성
    generateBtn.addEventListener('click', () => {
        updateStatus("Generating report...");
        setButtonsEnabled(false);

        callAPI('generate')
        .then(data => {
            if (data.success) {
                updateStatus("Report generated successfully");
                setTimeout(fetchResults, 1000);
            } else {
                updateStatus("Report generation failed: " + data.message, true);
            }
        })
        .catch(error => {
            updateStatus("Error: " + error.message, true);
        })
        .finally(() => {
            setButtonsEnabled(true);
        });
    });

    // 결과 새로고침
    refreshBtn.addEventListener('click', () => {
        updateStatus("Refreshing results...");
        fetchResults();
    });

    // 드라이브 건강 상태 확인
    healthBtn.addEventListener('click', () => {
        const drive = driveInput.value.trim();
        if (!drive) {
            updateStatus("Please enter a drive name", true);
            return;
        }

        updateStatus(`Checking health for drive ${drive}...`);
        setButtonsEnabled(false);

        callAPI('health', { drive: drive })
        .then(data => {
            if (data.success) {
                updateStatus(`Health check completed for drive ${drive}`);
                smartOutput.textContent = `Health Check Results for ${drive}:\n\n${data.result}`;
            } else {
                updateStatus("Health check failed: " + data.message, true);
                smartOutput.textContent = "Health check failed: " + data.message;
            }
        })
        .catch(error => {
            updateStatus("Error: " + error.message, true);
            smartOutput.textContent = "Error occurred: " + error.message;
        })
        .finally(() => {
            setButtonsEnabled(true);
        });
    });

    // SMART 테스트 시작
    testBtn.addEventListener('click', () => {
        const drive = driveInput.value.trim();
        if (!drive) {
            updateStatus("Please enter a drive name", true);
            return;
        }

        const test = testType.value;
        updateStatus(`Starting ${test} test for drive ${drive}...`);
        setButtonsEnabled(false);

        callAPI('test', { drive: drive, test_type: test })
        .then(data => {
            if (data.success) {
                updateStatus(`${test} test started successfully for drive ${drive}`);
                smartOutput.textContent = `${test} test started for drive ${drive}.\n\nCheck drive status for progress.`;
            } else {
                updateStatus("Test failed: " + data.message, true);
                smartOutput.textContent = "Test failed: " + data.message;
            }
        })
        .catch(error => {
            updateStatus("Error: " + error.message, true);
            smartOutput.textContent = "Error occurred: " + error.message;
        })
        .finally(() => {
            setButtonsEnabled(true);
        });
    });

    // 초기 로드
    loadSystemInfo();
    fetchResults();
});
