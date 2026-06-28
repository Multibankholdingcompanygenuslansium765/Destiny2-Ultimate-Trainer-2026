from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import aiohttp
from aiohttp import web
import websockets

from src.trainer import Trainer

log = logging.getLogger("Destiny2Trainer.WebDashboard")

class WebDashboard:
    def __init__(self, trainer: Trainer, port: int = 4200):
        self.trainer = trainer
        self.port = port
        self.app = web.Application()
        self.app.router.add_get("/", self.index_handler)
        self.app.router.add_get("/ws", self.websocket_handler)
        self.connected = set()

    async def index_handler(self, request):
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Trainer Dashboard</title>
    <style>
        body { background: #1a1a2e; color: #e94560; font-family: sans-serif; }
        .card { background: #16213e; padding: 20px; margin: 10px; border-radius: 8px; }
        .on { color: #0f0; }
        .off { color: #f00; }
    </style>
</head>
<body>
    <h1>Destiny 2 Trainer Dashboard</h1>
    <div id="features"></div>
    <script>
        const ws = new WebSocket(`ws://${location.host}/ws`);
        ws.onmessage = event => {
            const data = JSON.parse(event.data);
            const container = document.getElementById('features');
            container.innerHTML = '';
            for (const [feat, active] of Object.entries(data)) {
                const div = document.createElement('div');
                div.className = 'card';
                div.innerHTML = `${feat}: <span class="${active ? 'on' : 'off'}">${active ? 'ON' : 'OFF'}</span>`;
                container.appendChild(div);
            }
        };
    </script>
</body>
</html>"""
        return web.Response(text=html, content_type="text/html")

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.connected.add(ws)
        try:
            while True:
                # Send current feature states
                await ws.send_json(self.trainer.features)
                await asyncio.sleep(1)
        finally:
            self.connected.discard(ws)
        return ws

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        log.info(f"Web dashboard running on http://localhost:{self.port}")
        # Keep alive until cancelled
        while True:
            await asyncio.sleep(3600)
