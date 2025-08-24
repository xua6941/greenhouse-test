const express = require("express");
const http = require("http");
const WebSocket = require("ws");
const fs = require("fs");
const chokidar = require("chokidar");
const path = require("path");

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

app.use(express.static(path.join(__dirname, 'public'))); // index.html, main.js, models 폴더 등 제공
app.use('/sensor_logs', express.static(path.join(__dirname, 'sensor_logs')));

app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.get('/sensor-data.json', (req, res) => {
    fs.readFile('received_sensor_data.json', 'utf8', (err, data) => {
        if (err) {
            res.status(500).send('Error reading sensor data');
        } else {
            res.setHeader('Content-Type', 'application/json');
            res.send(data);
        }
    });
});

wss.on("connection", (ws) => {
    console.log("Client connected");
    ws.send(JSON.stringify({ type: "connected", message: "WebSocket 연결 완료" }));
});

// JSON 파일 변경 감지 및 브로드캐스트
const jsonPath = path.join(__dirname, "received_sensor_data.json");

chokidar.watch(jsonPath).on("change", () => {
    const json = fs.readFileSync(jsonPath, "utf-8");
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(json);
        }
    });
});

// Render는 환경변수 PORT 자동 제공
const PORT = process.env.PORT || 3009;
server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});