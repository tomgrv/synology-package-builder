const smartOutput = document.getElementById('smartOutput');
const refreshBtn = document.getElementById('refreshBtn');

function fetchSmartInfo() {
  smartOutput.textContent = "Loading...";
  fetch('/web/SynoSmartInfo/api/smartinfo')
    .then(res => {
      if (!res.ok) throw new Error("Network Error");
      return res.text();
    })
    .then(text => {
      smartOutput.textContent = text;
    })
    .catch(err => {
      smartOutput.textContent = "Error Occur: " + err.message;
      // 서버에 로그 전송
      fetch('/web/SynoSmartInfo/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: `fetchSmartInfo error: ${err.message}` })
      });
    });
}

fetchSmartInfo();
refreshBtn.addEventListener('click', fetchSmartInfo);
