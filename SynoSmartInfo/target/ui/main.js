const smartOutput = document.getElementById('smartOutput');
const refreshBtn = document.getElementById('refreshBtn');

function fetchSmartInfo() {
  smartOutput.textContent = "Loading...";
  
  // 정적 파일로 결과 읽기
  fetch('/webman/3rdparty/Synosmartinfo/result/smart.result')
    .then(res => {
      if (!res.ok) throw new Error("Network Error");
      return res.text();
    })
    .then(text => {
      smartOutput.textContent = text;
    })
    .catch(err => {
      smartOutput.textContent = "Error Occur: " + err.message;
    });
}

document.addEventListener('DOMContentLoaded', () => {
  fetchSmartInfo();          // DOM 준비 후 호출
  refreshBtn.addEventListener('click', () => {
    generateNewResult();
    setTimeout(fetchSmartInfo, 2000);
  });
});

function generateNewResult() {
  // 새로운 SMART 결과 생성 (서버사이드에서 실행)
  fetch('/webman/3rdparty/Synosmartinfo/generate_result.html', {
    method: 'POST'
  }).catch(() => {
    // 실패해도 무시 (백그라운드 작업)
  });
}
