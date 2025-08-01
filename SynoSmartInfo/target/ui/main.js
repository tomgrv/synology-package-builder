document.addEventListener('DOMContentLoaded', () => {
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

  function generateNewResult() {
    // 새로운 SMART 결과 생성 (서버사이드에서 실행)
    fetch('/webman/3rdparty/Synosmartinfo/generate_result.html', {
      method: 'POST'
    }).catch(() => {
      // 실패해도 무시 (백그라운드 작업)
    });
  }

  // 페이지 로드시 자동 호출
  fetchSmartInfo();

  // 새로고침 버튼 이벤트
  refreshBtn.addEventListener('click', () => {
    // 새로운 결과 생성을 위한 스크립트 실행 (백그라운드)
    generateNewResult();
    // 잠시 기다린 후 결과 파일 다시 읽기
    setTimeout(fetchSmartInfo, 2000);
  });
});
