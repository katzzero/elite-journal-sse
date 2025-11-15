#!/usr/bin/env python3
"""
Elite Dangerous SSE Server - GUI
Interface gráfica para monitorar e controlar o servidor SSE
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import asyncio
import json
import requests
from datetime import datetime
from pathlib import Path
import sys
import os

# Importa o servidor
try:
    from server import app, start_monitoring, stop_monitoring, DEFAULT_JOURNAL_PATH
    import uvicorn
except ImportError:
    messagebox.showerror("Erro", "Não foi possível importar o módulo server.py")
    sys.exit(1)


class EliteSSEGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Elite Dangerous SSE Server - Monitor")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')

        # Variáveis de controle
        self.server_running = False
        self.server_thread = None
        self.uvicorn_server = None
        self.event_source = None
        self.journal_path = DEFAULT_JOURNAL_PATH
        self.event_count = 0
        self.events_list = []

        # Configurações
        self.host = "0.0.0.0"
        self.port = 8000

        self.setup_ui()
        self.update_status("Servidor parado", "red")

    def setup_ui(self):
        # ... (inafectado, igual ao anterior)
        # -----------CÓDIGO OMITIDO POR BREVIDADE-----------
        pass

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        self.logs_text.insert(tk.END, log_message)
        self.logs_text.see(tk.END)
        print(log_message.strip())

    def update_status(self, text, color):
        self.status_label.config(text=f"Status: {text}", fg=color)

    def browse_journal_path(self):
        folder = filedialog.askdirectory(
            title="Selecione a pasta de Journals do Elite Dangerous",
            initialdir=str(self.journal_path)
        )
        if folder:
            self.journal_path = Path(folder)
            self.path_label.config(text=f"📂 Pasta: {self.journal_path}")
            self.log(f"Pasta de journals alterada para: {self.journal_path}")

    def start_server(self):
        if self.server_running:
            messagebox.showwarning("Aviso", "O servidor já está rodando!")
            return
        if not self.journal_path.exists():
            messagebox.showerror(
                "Erro",
                f"Pasta de journals não encontrada:\n{self.journal_path}\n\n"
                "Por favor, selecione a pasta correta."
            )
            return
        self.log("Iniciando servidor SSE...")
        self.update_status("Iniciando...", "yellow")
        if start_monitoring(self.journal_path):
            self.server_thread = threading.Thread(
                target=self.run_server,
                daemon=True
            )
            self.server_thread.start()
            self.server_running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.browse_button.config(state='disabled')
            self.update_status("Rodando", "green")
            self.log("Servidor iniciado com sucesso!")
            self.log(f"Acesse: http://localhost:{self.port}")
            self.start_event_monitoring()
        else:
            self.log("Erro ao iniciar monitoramento", "ERROR")
            self.update_status("Erro", "red")
            messagebox.showerror("Erro", "Não foi possível iniciar o monitoramento")

    def run_server(self):
        try:
            config = uvicorn.Config(app, host=self.host, port=self.port, log_level="info")
            self.uvicorn_server = uvicorn.Server(config)
            self.uvicorn_server.run()
        except Exception as e:
            self.log(f"Erro no servidor: {e}", "ERROR")

    def stop_server(self):
        if not self.server_running:
            return
        self.log("Parando servidor...")
        self.update_status("Parando...", "yellow")
        if self.uvicorn_server:
            self.uvicorn_server.should_exit = True
            self.server_thread.join(timeout=5)
            self.uvicorn_server = None
        stop_monitoring()
        self.server_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.browse_button.config(state='normal')
        self.update_status("Parado", "red")
        self.log("Servidor parado")
        # Agora o processo Uvicorn é finalizado sem interação manual

    def start_event_monitoring(self):
        thread = threading.Thread(target=self.monitor_events, daemon=True)
        thread.start()

    def monitor_events(self):
        import sseclient
        import requests
        import time
        time.sleep(2)
        try:
            url = f"http://localhost:{self.port}/events"
            response = requests.get(url, stream=True, timeout=None)
            client = sseclient.SSEClient(response)
            for event in client.events():
                if not self.server_running:
                    break
                try:
                    data = json.loads(event.data)
                    self.process_event(event.event, data)
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    self.log(f"Erro ao processar evento: {e}", "ERROR")
        except Exception as e:
            self.log(f"Erro na conexão SSE: {e}", "ERROR")

    def process_event(self, event_type, data):
        self.event_count += 1
        self.events_list.append({"type": event_type, "data": data})
        self.events_count_label.config(text=f"📡 Eventos recebidos: {self.event_count}")
        timestamp = datetime.now().strftime("%H:%M:%S")
        event_text = f"[{timestamp}] {event_type}\n{json.dumps(data, indent=2)}\n{'='*60}\n"
        self.events_text.insert(tk.END, event_text)
        self.events_text.see(tk.END)
        self.update_stats()
        if self.event_count % 50 == 0:
            self.events_text.delete(1.0, "10.0")

    def update_stats(self):
        event_types = {}
        for event in self.events_list:
            event_type = event["type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1
        stats = f"Total de eventos: {self.event_count}\n\n"
        stats += "Eventos por tipo:\n"
        stats += "=" * 40 + "\n"
        for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
            stats += f"{event_type}: {count}\n"
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)

    def clear_events(self):
        self.events_text.delete(1.0, tk.END)
        self.log("Eventos limpos")

    def clear_logs(self):
        self.logs_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = EliteSSEGUI(root)
    def on_closing():
        if app.server_running:
            if messagebox.askokcancel("Sair", "O servidor ainda está rodando. Deseja realmente sair?"):
                app.stop_server()
                root.destroy()
        else:
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
