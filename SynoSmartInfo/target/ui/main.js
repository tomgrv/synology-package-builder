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
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('API call error:', error);
            throw new Error('API call failed: ' + error.message);
        });
    }

    // 시스템 정보 로드
    function loadSystemInfo() {
        callAPI('info')
        .then(data => {
            if (data.success) {
                systemInfo.innerHTML = `
                    <strong>Unique ID:</strong>
                    <span>${data.unique || 'N/A'}</span>
                    <strong>Build Number:</strong>
                    <span>${data.build || 'N/A'}</span>
                `;
            } else {
                systemInfo.innerHTML = '<span class="error">Failed to load system information: ' + (data.message || 'Unknown error') + '</span>';
            }
        })
        .catch(error => {
            systemInfo.innerHTML = '<span class="error">Error: ' + error.message + '</span>';
        });
    }

    // 상태 업데이트
    function updateStatus(message, type = 'success') {
        status.textContent = message;
        status.className = 'status ' + type;
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
            smartOutput.textContent = text || "No results available.";
            updateStatus("Results loaded successfully", "success");
        })
        .catch(err => {
            smartOutput.textContent = "No results available. Please run a scan first.";
            updateStatus("Error loading results: " + err.message, "warning");
        });
    }

    // 전체 SMART 스캔
    scanBtn.addEventListener('click', () => {
        updateStatus("Running SMART scan...", "warning");
        setButtonsEnabled(false);
        smartOutput.textContent = "Scanning drives, please wait...";

        callAPI('scan')
        .then(data => {
            if (data.success) {
                updateStatus("SMART scan completed successfully", "success");
                // 잠시 후 결과 로드
                setTimeout(fetchResults, 2000);
            } else {
                updateStatus("SMART scan failed: " + data.message, "error");
                smartOutput.textContent = "Scan failed: " + data.message;
            }
        })
        .catch(error => {
            updateStatus("Error: " + error.message, "error");
            smartOutput.textContent = "Error occurred: " + error.message;
        })
        .finally(() => {
            setButtonsEnabled(true);
        });
    });

    // 리포트 생성
    generateBtn.addEventListener('click', () => {
        updateStatus("Generating report...", "warning");
        setButtonsEnabled(false);

        callAPI('generate')
        .then(data => {
            if (data.success) {
                updateStatus("Report generated successfully", "success");
                setTimeout(fetchResults, 2000);
            } else {
                updateStatus("Report generation failed: " + data.message, "error");
            }
        })
        .catch(error => {
            updateStatus("Error: " + error.message, "error");
        })
        .finally(() => {
            setButtonsEnabled(true);
        });
    });

    // 결과 새로고침
    refreshBtn.addEventListener('click', () => {
        updateStatus("Refreshing results...", "warning");
        fetchResults();
    });

    // 드라이브 건강 상태 확인
    healthBtn.addEventListener('click', () => {
        const drive = driveInput.value.trim();
        if (!drive) {
            updateStatus("Please enter a drive name", "error");
            return;
        }

        updateStatus(`Checking health for drive ${drive}...`, "warning");
        setButtonsEnabled(false);

        callAPI('health', { drive: drive })
        .then(data => {
            if (data.success) {
                updateStatus(`Health check completed for drive ${drive}`, "success");
                smartOutput.textContent = `Health Check Results for ${drive}:\n\n${data.result || 'No detailed results available'}`;
            } else {
                updateStatus("Health check failed: " + data.message, "error");
                smartOutput.textContent = "Health check failed: " + data.message;
            }
        })
        .catch(error => {
            updateStatus("Error: " + error.message, "error");
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
            updateStatus("Please enter a drive name", "error");
            return;
        }

        const test = testType.value;
        updateStatus(`Starting ${test} test for drive ${drive}...`, "warning");
        setButtonsEnabled(false);

        callAPI('test', { drive: drive, test_type: test })
        .then(data => {
            if (data.success) {
                updateStatus(`${test} test started successfully for drive ${drive}`, "success");
                smartOutput.textContent = `${test} test started for drive ${drive}.\n\nThe test is running in the background.\nCheck drive status for progress.`;
            } else {
                updateStatus("Test failed: " + data.message, "error");
                smartOutput.textContent = "Test failed: " + data.message;
            }
        })
        .catch(error => {
            updateStatus("Error: " + error.message, "error");
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
