const express = require('express');
const fs = require('fs');
const app = express();
const PKG_NAME = 'Synosmartinfo';
const LOG_PATH = `/var/packages/${PKG_NAME}/var/${PKG_NAME}.log`;

function logMessage(message) {
    const now = new Date().toISOString().replace('T', ' ').split('.')[0];
    const logLine = `[${now}] ${message}\n`;
    fs.appendFile(LOG_PATH, logLine, { encoding: 'utf8' }, (err) => {
        if (err) console.error('Log File write failed:', err);
    });
}

app.use(express.static('/var/packages/SynoSmartInfo/web')); // 정적 HTML/JS 제공

app.post('/web/SynoSmartInfo/api/log', express.json(), (req, res) => {
    logMessage(req.body.message);
    res.json({ ok: true });
});

// 필요시 smartinfo api 등 추가

app.listen(8080, () => logMessage('main.js Server Started'));
