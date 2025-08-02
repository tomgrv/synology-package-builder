document.addEventListener('DOMContentLoaded', () => {
    const optionSelect = document.getElementById('optionSelect');
    const runBtn = document.getElementById('runBtn');
    const status = document.getElementById('status');
    const output = document.getElementById('output');
    const systemInfo = document.getElementById('systemInfo');

    // TEXT 응답 파싱
    function parseTextResponse(text){
      const lines=text.split('\n');
      const obj={success:false,message:'',data:null};
    
      if(lines[0].startsWith('SUCCESS: ')){
          obj.success=true;
          obj.message=lines[0].slice(9);
      }else if(lines[0].startsWith('ERROR: ')){
          obj.message=lines[0].slice(7);
      }else{
          obj.message=lines[0];
      }
    
      const s=lines.indexOf('DATA_START');
      const e=lines.indexOf('DATA_END');
      if(s!==-1&&e!==-1&&s<e){
          obj.data=lines.slice(s+1,e).join('\n');
      }
      return obj;
    }
    
    // API 호출 함수
    function callAPI(action, params = {}) {
        const urlParams = new URLSearchParams();
        urlParams.append('action', action);
        
        Object.keys(params).forEach(key => {
            urlParams.append(key, params[key]);
        });

        return fetch('api.cgi', {
            method:'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body:urlParams})
        .then(res=>res.text())
        .then(parseTextResponse);
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

        updateStatus('Running SMART scan... Please wait.', 'warning');
        output.textContent = 'SMART scan is in progress...\nThis operation may take up to 2 minutes.';
        setButtonsEnabled(false);

        callAPI('run', { option: selectedOption })
        .then(data => {
            if (data.success) {
                updateStatus('Success: ' + data.message, 'success');
                
                if (data.result && data.result.trim()) {
                    // ANSI 컬러 코드를 HTML로 변환하여 표시
                    var ansi_up = new AnsiUp();
                    var html = ansi_up.ansi_to_html(data.result);
                    output.innerHTML = html;
                } else {
                    // 결과가 없으면 결과 파일 직접 읽기 시도
                    updateStatus('Loading result file...', 'warning');
                    setTimeout(() => {
                        fetch('/webman/3rdparty/Synosmartinfo/result/smart.result')
                        .then(res => res.text())
                        .then(text => {
                            if (text && text.trim()) {
                                var ansi_up = new AnsiUp();
                                var html = ansi_up.ansi_to_html(text);
                                output.innerHTML = html;
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
                updateStatus('Failed: ' + data.message, 'error');
                
                // 실패한 경우에도 ANSI 컬러 적용
                if (data.result && data.result.trim()) {
                    var ansi_up = new AnsiUp();
                    var html = ansi_up.ansi_to_html('Error: ' + data.message + '\n\nDetails:\n' + data.result);
                    output.innerHTML = html;
                } else {
                    output.textContent = 'Error: ' + data.message;
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
//
