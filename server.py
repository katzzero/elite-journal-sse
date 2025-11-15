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
main_asyncio_loop: Optional[asyncio.AbstractEventLoop] = None

class JournalEventHandler(FileSystemEventHandler):
    """Handler para monitorar mudanças nos arquivos de journal"""
    def __init__(self, journal_path: Path, main_loop: asyncio.AbstractEventLoop):
        self.journal_path = journal_path
        self.main_loop = main_loop
        self.current_file: Optional[Path] = None
        self.file_position = 0
        self.find_latest_journal()
    def find_latest_journal(self):
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
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.suffix == ".log" and file_path.name.startswith("Journal."):
            if self.current_file is None or file_path.stat().st_mtime > self.current_file.stat().st_mtime:
                self.current_file = file_path
                self.file_position = 0
                print(f"📁 Novo journal detectado: {file_path.name}")
            self.read_new_events()
    def read_new_events(self):
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
                            event_data["_server_timestamp"] = datetime.utcnow().isoformat() + "Z"
                            event_data["_journal_file"] = self.current_file.name
                            # Corrigido: injeta corrotina usando o loop principal passado pela main
                            asyncio.run_coroutine_threadsafe(
                                event_queue.put(event_data),
                                self.main_loop
                            )
                            print(f"📡 Evento: {event_data.get('event', 'Unknown')}")
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON inválido: {e}")
                self.file_position = f.tell()
        except Exception as e:
            print(f"❌ Erro ao ler eventos: {e}")

observer: Optional[Observer] = None
event_handler: Optional[JournalEventHandler] = None

def start_monitoring(journal_path: Path):
    global observer, event_handler, main_asyncio_loop
    if not journal_path.exists():
        print(f"❌ Pasta de journals não encontrada: {journal_path}")
        print(f"   Por favor, configure o caminho correto.")
        return False
    print(f"🔍 Iniciando monitoramento em: {journal_path}")
    if main_asyncio_loop is None:
        main_asyncio_loop = asyncio.get_running_loop()
    event_handler = JournalEventHandler(journal_path, main_asyncio_loop)
    observer = Observer()
    observer.schedule(event_handler, str(journal_path), recursive=False)
    observer.start()
    print("✅ Monitoramento iniciado com sucesso!")
    return True

def stop_monitoring():
    global observer
    if observer:
        observer.stop()
        observer.join()
        print("🛑 Monitoramento parado")

async def event_generator(request: Request) -> AsyncGenerator[str, None]:
    try:
        yield f"event: connected\n"
        yield f"data: {{\"message\": \"Conectado ao servidor Elite Dangerous SSE\", \"timestamp\": \"{datetime.utcnow().isoformat()}Z\"}}\n\n"
        while True:
            if await request.is_disconnected():
                print("👋 Cliente desconectado")
                break
            try:
                event_data = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                event_name = event_data.get("event", "unknown")
                yield f"event: {event_name}\n"
                yield f"data: {json.dumps(event_data)}\n\n"
            except asyncio.TimeoutError:
                yield f": heartbeat\n\n"
    except Exception as e:
        print(f"❌ Erro no gerador de eventos: {e}")
    finally:
        print("🔌 Conexão SSE encerrada")

@app.get("/events")
async def sse_endpoint(request: Request):
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
    html_content = """(mantido igual)"""
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "monitoring": observer is not None and observer.is_alive() if observer else False,
        "current_journal": event_handler.current_file.name if event_handler and event_handler.current_file else None
    }

@app.on_event("startup")
async def startup_event():
    print("="*60)
    print("🚀 Elite Dangerous SSE Server")
    print("="*60)
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
    stop_monitoring()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True
    )
