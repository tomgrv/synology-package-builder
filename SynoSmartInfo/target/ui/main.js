document.addEventListener('DOMContentLoaded', () => {
    const optionSelect = document.getElementById('optionSelect');
    const runBtn = document.getElementById('runBtn');
    const status = document.getElementById('status');
    const output = document.getElementById('output');

    // fetch 대신 CGI API 호출 - 여기서 'action=run'에 option 파라미터 전달
    function callAPI(option) {
        const formData = new FormData();
        formData.append('action', 'run');
        formData.append('option', option);

        return fetch('api.cgi', {
            method: 'POST',
            body: formData
        })
        .then(res => {
            if (!res.ok) {
                throw new Error(`HTTP ${res.status} - ${res.statusText}`);
            }
            return res.json();
        });
    }

    runBtn.addEventListener('click', () => {
        const selectedOption = optionSelect.value;

        status.textContent = '실행 중... 잠시만 기다려주세요.';
        status.style.color = '#0066cc';
        output.textContent = '';

        runBtn.disabled = true;
        optionSelect.disabled = true;

        callAPI(selectedOption)
            .then(data => {
                if (data.success) {
                    status.textContent = '성공: ' + data.message;
                    status.style.color = 'green';

                    // 출력이 있을 경우 표시
                    if (data.result) {
                        output.textContent = data.result;
                    } else {
                        output.textContent = '결과가 없습니다.';
                    }
                } else {
                    status.textContent = '실패: ' + data.message;
                    status.style.color = 'red';
                }
            })
            .catch(err => {
                status.textContent = '오류: ' + err.message;
                status.style.color = 'red';
                output.textContent = '';
            })
            .finally(() => {
                runBtn.disabled = false;
                optionSelect.disabled = false;
            });
    });
});
