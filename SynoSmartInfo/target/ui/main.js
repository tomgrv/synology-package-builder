const smartOutput = document.getElementById('smartOutput');
const refreshBtn = document.getElementById('refreshBtn');

function fetchSmartInfo() {
  smartOutput.textContent = "Loading...";
  // 올바른 CGI 경로로 수정
  fetch('/web/Synosmartinfo/cgi-bin/smart_result.cgi')
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

fetchSmartInfo();
refreshBtn.addEventListener('click', fetchSmartInfo);
