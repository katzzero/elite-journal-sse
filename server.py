#!/usr/bin/env python3
"""
Elite Dangerous SSE Server
Servidor SSE para transmitir eventos do Elite Dangerous em tempo real
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, AsyncGenerator
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configurações
HOST = "0.0.0.0"  # Permite acesso na rede local
PORT = 8000

# Detecta automaticamente a pasta de journals do Elite Dangerous
if sys.platform == "win32":
    DEFAULT_JOURNAL_PATH = Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous"
else:
    # Para Wine/Proton no Linux
    DEFAULT_JOURNAL_PATH = Path.home() / ".steam" / "steam" / "steamapps" / "compatdata" / "359320" / "pfx" / "drive_c" / "users" / "steamuser" / "Saved Games" / "Frontier Developments" / "Elite Dangerous"

app = FastAPI(title="Elite Dangerous SSE Server")

# Configurar CORS para permitir acesso de qualquer origem na rede local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fila global para armazenar eventos
event_queue = asyncio.Queue()


class JournalEventHandler(FileSystemEventHandler):
    """Handler para monitorar mudanças nos arquivos de journal"""
    
    def __init__(self, journal_path: Path):
        self.journal_path = journal_path
        self.current_file: Optional[Path] = None
        self.file_position = 0
        self.find_latest_journal()
    
    def find_latest_journal(self):
        """Encontra o arquivo de journal mais recente"""
        try:
            journal_files = sorted(
                self.journal_path.glob("Journal.*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if journal_files:
                self.current_file = journal_files[0]
                self.file_position = self.current_file.stat().st_size
                print(f"📁 Monitorando: {self.current_file.name}")
        except Exception as e:
            print(f"❌ Erro ao procurar journals: {e}")
    
    def on_modified(self, event):
        """Chamado quando um arquivo é modificado"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Verifica se é um arquivo de journal
        if file_path.suffix == ".log" and file_path.name.startswith("Journal."):
            # Se é um arquivo novo mais recente, atualiza
            if self.current_file is None or file_path.stat().st_mtime > self.current_file.stat().st_mtime:
                self.current_file = file_path
                self.file_position = 0
                print(f"📁 Novo journal detectado: {file_path.name}")
            
            # Lê novas linhas do arquivo
            self.read_new_events()
    
    def read_new_events(self):
        """Lê novos eventos do arquivo de journal"""
        if not self.current_file or not self.current_file.exists():
            return
        
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                f.seek(self.file_position)
                
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event_data = json.loads(line)
                            # Adiciona metadados
                            event_data["_server_timestamp"] = datetime.utcnow().isoformat() + "Z"
                            event_data["_journal_file"] = self.current_file.name
                            
                            # Adiciona à fila de forma não-bloqueante
                            asyncio.run_coroutine_threadsafe(
                                event_queue.put(event_data),
                                asyncio.get_event_loop()
                            )
                            print(f"📡 Evento: {event_data.get('event', 'Unknown')}")
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON inválido: {e}")
                
                self.file_position = f.tell()
        except Exception as e:
            print(f"❌ Erro ao ler eventos: {e}")


# Observer global
observer: Optional[Observer] = None
event_handler: Optional[JournalEventHandler] = None


def start_monitoring(journal_path: Path):
    """Inicia o monitoramento dos arquivos de journal"""
    global observer, event_handler
    
    if not journal_path.exists():
        print(f"❌ Pasta de journals não encontrada: {journal_path}")
        print(f"   Por favor, configure o caminho correto.")
        return False
    
    print(f"🔍 Iniciando monitoramento em: {journal_path}")
    
    event_handler = JournalEventHandler(journal_path)
    observer = Observer()
    observer.schedule(event_handler, str(journal_path), recursive=False)
    observer.start()
    
    print("✅ Monitoramento iniciado com sucesso!")
    return True


def stop_monitoring():
    """Para o monitoramento"""
    global observer
    if observer:
        observer.stop()
        observer.join()
        print("🛑 Monitoramento parado")


async def event_generator(request: Request) -> AsyncGenerator[str, None]:
    """Gerador de eventos SSE"""
    try:
        # Envia evento de conexão estabelecida
        yield f"event: connected\n"
        yield f"data: {{\"message\": \"Conectado ao servidor Elite Dangerous SSE\", \"timestamp\": \"{datetime.utcnow().isoformat()}Z\"}}\n\n"
        
        while True:
            # Verifica se o cliente ainda está conectado
            if await request.is_disconnected():
                print("👋 Cliente desconectado")
                break
            
            try:
                # Aguarda por novos eventos com timeout
                event_data = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                
                # Formata o evento SSE
                event_name = event_data.get("event", "unknown")
                yield f"event: {event_name}\n"
                yield f"data: {json.dumps(event_data)}\n\n"
                
            except asyncio.TimeoutError:
                # Envia heartbeat a cada 30 segundos
                yield f": heartbeat\n\n"
                
    except Exception as e:
        print(f"❌ Erro no gerador de eventos: {e}")
    finally:
        print("🔌 Conexão SSE encerrada")


@app.get("/events")
async def sse_endpoint(request: Request):
    """Endpoint SSE principal"""
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/", response_class=HTMLResponse)
async def root():
    """Página inicial com cliente de teste"""
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Elite Dangerous SSE - Monitor</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: #fff;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .status {
                background: rgba(255,255,255,0.1);
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
                backdrop-filter: blur(10px);
            }
            .status.connected {
                background: rgba(76, 175, 80, 0.3);
            }
            .status.disconnected {
                background: rgba(244, 67, 54, 0.3);
            }
            .events-container {
                background: rgba(0,0,0,0.3);
                border-radius: 10px;
                padding: 20px;
                max-height: 600px;
                overflow-y: auto;
                backdrop-filter: blur(10px);
            }
            .event {
                background: rgba(255,255,255,0.1);
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 8px;
                border-left: 4px solid #4CAF50;
                animation: slideIn 0.3s ease;
            }
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateX(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            .event-type {
                font-weight: bold;
                color: #4CAF50;
                margin-bottom: 5px;
            }
            .event-timestamp {
                color: #aaa;
                font-size: 0.85em;
                margin-bottom: 8px;
            }
            .event-data {
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                background: rgba(0,0,0,0.3);
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }
            .controls {
                margin-bottom: 20px;
                text-align: center;
            }
            button {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                margin: 0 5px;
                transition: background 0.3s;
            }
            button:hover {
                background: #45a049;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Elite Dangerous - Monitor de Eventos</h1>
            
            <div id="status" class="status disconnected">
                <strong>Status:</strong> <span id="status-text">Desconectado</span>
            </div>
            
            <div class="controls">
                <button id="clearBtn" onclick="clearEvents()">🗑️ Limpar Eventos</button>
                <button id="toggleBtn" onclick="toggleConnection()">▶️ Conectar</button>
            </div>
            
            <div class="events-container" id="events">
                <p style="text-align: center; color: #aaa;">Aguardando eventos...</p>
            </div>
        </div>
        
        <script>
            let eventSource = null;
            let isConnected = false;
            const eventsContainer = document.getElementById('events');
            const statusDiv = document.getElementById('status');
            const statusText = document.getElementById('status-text');
            const toggleBtn = document.getElementById('toggleBtn');
            
            function connect() {
                if (isConnected) return;
                
                eventSource = new EventSource('/events');
                
                eventSource.addEventListener('connected', (e) => {
                    const data = JSON.parse(e.data);
                    updateStatus('Conectado', true);
                    addEvent('connected', data, data.timestamp);
                });
                
                // Listener genérico para todos os eventos
                eventSource.onmessage = (e) => {
                    try {
                        const data = JSON.parse(e.data);
                        addEvent(data.event || 'unknown', data, data.timestamp);
                    } catch (err) {
                        console.error('Erro ao processar evento:', err);
                    }
                };
                
                // Listeners para eventos específicos do Elite Dangerous
                const eventTypes = [
                    'Fileheader', 'Location', 'FSDJump', 'Docked', 'Undocked',
                    'SupercruiseEntry', 'SupercruiseExit', 'Scan', 'Materials',
                    'CargoTransfer', 'MissionAccepted', 'MissionCompleted',
                    'Bounty', 'ShipTargeted', 'ReceiveText'
                ];
                
                eventTypes.forEach(eventType => {
                    eventSource.addEventListener(eventType, (e) => {
                        const data = JSON.parse(e.data);
                        addEvent(eventType, data, data.timestamp);
                    });
                });
                
                eventSource.onerror = (e) => {
                    console.error('Erro SSE:', e);
                    updateStatus('Erro na conexão', false);
                    disconnect();
                };
                
                isConnected = true;
            }
            
            function disconnect() {
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                updateStatus('Desconectado', false);
                isConnected = false;
            }
            
            function toggleConnection() {
                if (isConnected) {
                    disconnect();
                    toggleBtn.textContent = '▶️ Conectar';
                } else {
                    connect();
                    toggleBtn.textContent = '⏸️ Desconectar';
                }
            }
            
            function updateStatus(text, connected) {
                statusText.textContent = text;
                statusDiv.className = 'status ' + (connected ? 'connected' : 'disconnected');
            }
            
            function addEvent(type, data, timestamp) {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'event';
                
                const eventType = document.createElement('div');
                eventType.className = 'event-type';
                eventType.textContent = `📡 ${type}`;
                
                const eventTimestamp = document.createElement('div');
                eventTimestamp.className = 'event-timestamp';
                eventTimestamp.textContent = new Date(timestamp || data._server_timestamp).toLocaleString('pt-BR');
                
                const eventData = document.createElement('div');
                eventData.className = 'event-data';
                eventData.textContent = JSON.stringify(data, null, 2);
                
                eventDiv.appendChild(eventType);
                eventDiv.appendChild(eventTimestamp);
                eventDiv.appendChild(eventData);
                
                // Remove mensagem de aguardando
                if (eventsContainer.querySelector('p')) {
                    eventsContainer.innerHTML = '';
                }
                
                eventsContainer.insertBefore(eventDiv, eventsContainer.firstChild);
                
                // Limita a 50 eventos
                while (eventsContainer.children.length > 50) {
                    eventsContainer.removeChild(eventsContainer.lastChild);
                }
            }
            
            function clearEvents() {
                eventsContainer.innerHTML = '<p style="text-align: center; color: #aaa;">Aguardando eventos...</p>';
            }
            
            // Auto-conecta ao carregar
            window.addEventListener('load', () => {
                connect();
                toggleBtn.textContent = '⏸️ Desconectar';
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health():
    """Endpoint de health check"""
    return {
        "status": "ok",
        "monitoring": observer is not None and observer.is_alive() if observer else False,
        "current_journal": event_handler.current_file.name if event_handler and event_handler.current_file else None
    }


@app.on_event("startup")
async def startup_event():
    """Evento de inicialização"""
    print("="*60)
    print("🚀 Elite Dangerous SSE Server")
    print("="*60)
    
    # Permite configurar caminho customizado via variável de ambiente
    custom_path = os.getenv("ELITE_JOURNAL_PATH")
    journal_path = Path(custom_path) if custom_path else DEFAULT_JOURNAL_PATH
    
    print(f"📂 Pasta de journals: {journal_path}")
    
    if start_monitoring(journal_path):
        print(f"🌐 Servidor disponível em: http://localhost:{PORT}")
        print(f"🌐 Acesso na rede local: http://<seu-ip>:{PORT}")
        print(f"📡 Endpoint SSE: http://localhost:{PORT}/events")
        print("="*60)
    else:
        print("\n⚠️  AVISO: Monitoramento não iniciado!")
        print(f"   Configure a variável de ambiente ELITE_JOURNAL_PATH")
        print(f"   com o caminho correto dos seus arquivos de journal.")
        print("="*60)


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de encerramento"""
    stop_monitoring()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True
    )
