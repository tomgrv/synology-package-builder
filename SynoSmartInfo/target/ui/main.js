const smartOutput = document.getElementById('smartOutput');
const refreshBtn = document.getElementById('refreshBtn');

function fetchSmartInfo() {
  smartOutput.textContent = "불러오는 중...";
  fetch('/web/SynoSmartInfo/api/smartinfo')
    .then(res => {
      if(!res.ok) throw new Error("네트워크 오류");
      return res.text();
    })
    .then(text => {
      smartOutput.textContent = text;
    })
    .catch(err => {
      smartOutput.textContent = "오류 발생: " + err.message;
    });
}

// 자동 호출
fetchSmartInfo();

// 새로고침 버튼 이벤트
refreshBtn.addEventListener('click', fetchSmartInfo);
