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
        """Configura a interface gráfica"""
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cores personalizadas
        bg_color = '#1e1e1e'
        fg_color = '#ffffff'
        accent_color = '#4CAF50'
        
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', background=accent_color, foreground=fg_color)
        style.map('TButton', background=[('active', '#45a049')])
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="🚀 Elite Dangerous SSE Server",
            font=('Arial', 20, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Frame de controle
        control_frame = ttk.LabelFrame(main_frame, text="Controle do Servidor", padding="10")
        control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Botões de controle
        self.start_button = tk.Button(
            control_frame,
            text="▶️ Iniciar Servidor",
            command=self.start_server,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=10
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = tk.Button(
            control_frame,
            text="⏸️ Parar Servidor",
            command=self.stop_server,
            bg='#f44336',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=10,
            state='disabled'
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.browse_button = tk.Button(
            control_frame,
            text="📁 Selecionar Pasta",
            command=self.browse_journal_path,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=10
        )
        self.browse_button.grid(row=0, column=2, padx=5)
        
        # Frame de status
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Labels de status
        self.status_label = tk.Label(
            status_frame,
            text="Status: Parado",
            font=('Arial', 10, 'bold'),
            bg='#1e1e1e',
            fg='red'
        )
        self.status_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.path_label = ttk.Label(
            status_frame,
            text=f"📂 Pasta: {self.journal_path}",
            font=('Arial', 9)
        )
        self.path_label.grid(row=1, column=0, sticky=tk.W, padx=5)
        
        self.url_label = ttk.Label(
            status_frame,
            text=f"🌐 URL: http://localhost:{self.port}",
            font=('Arial', 9)
        )
        self.url_label.grid(row=2, column=0, sticky=tk.W, padx=5)
        
        self.events_count_label = ttk.Label(
            status_frame,
            text="📡 Eventos recebidos: 0",
            font=('Arial', 9)
        )
        self.events_count_label.grid(row=3, column=0, sticky=tk.W, padx=5)
        
        # Notebook (abas)
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(3, weight=1)
        
        # Aba de eventos
        events_frame = ttk.Frame(notebook)
        notebook.add(events_frame, text="Eventos")
        
        # Lista de eventos
        self.events_text = scrolledtext.ScrolledText(
            events_frame,
            wrap=tk.WORD,
            font=('Courier New', 9),
            bg='#2d2d2d',
            fg='#00ff00',
            insertbackground='white'
        )
        self.events_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Botão limpar eventos
        clear_events_btn = tk.Button(
            events_frame,
            text="🗑️ Limpar Eventos",
            command=self.clear_events,
            bg='#FF9800',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=10,
            pady=5
        )
        clear_events_btn.pack(pady=5)
        
        # Aba de logs
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="Logs")
        
        # Área de logs
        self.logs_text = scrolledtext.ScrolledText(
            logs_frame,
            wrap=tk.WORD,
            font=('Courier New', 9),
            bg='#2d2d2d',
            fg='#ffffff',
            insertbackground='white'
        )
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Botão limpar logs
        clear_logs_btn = tk.Button(
            logs_frame,
            text="🗑️ Limpar Logs",
            command=self.clear_logs,
            bg='#FF9800',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=10,
            pady=5
        )
        clear_logs_btn.pack(pady=5)
        
        # Aba de estatísticas
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Estatísticas")
        
        self.stats_text = scrolledtext.ScrolledText(
            stats_frame,
            wrap=tk.WORD,
            font=('Courier New', 10),
            bg='#2d2d2d',
            fg='#ffffff',
            insertbackground='white'
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configura redimensionamento
        for i in range(3):
            main_frame.columnconfigure(i, weight=1)
    
    def log(self, message, level="INFO"):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        self.logs_text.insert(tk.END, log_message)
        self.logs_text.see(tk.END)
        print(log_message.strip())
    
    def update_status(self, text, color):
        """Atualiza o status do servidor"""
        self.status_label.config(text=f"Status: {text}", fg=color)
    
    def browse_journal_path(self):
        """Abre diálogo para selecionar pasta de journals"""
        folder = filedialog.askdirectory(
            title="Selecione a pasta de Journals do Elite Dangerous",
            initialdir=str(self.journal_path)
        )
        if folder:
            self.journal_path = Path(folder)
            self.path_label.config(text=f"📂 Pasta: {self.journal_path}")
            self.log(f"Pasta de journals alterada para: {self.journal_path}")
    
    def start_server(self):
        """Inicia o servidor SSE"""
        if self.server_running:
            messagebox.showwarning("Aviso", "O servidor já está rodando!")
            return
        
        # Verifica se a pasta existe
        if not self.journal_path.exists():
            messagebox.showerror(
                "Erro",
                f"Pasta de journals não encontrada:\n{self.journal_path}\n\n"
                "Por favor, selecione a pasta correta."
            )
            return
        
        self.log("Iniciando servidor SSE...")
        self.update_status("Iniciando...", "yellow")
        
        # Inicia monitoramento
        if start_monitoring(self.journal_path):
            # Inicia servidor em thread separada
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
            
            # Inicia monitoramento de eventos via SSE
            self.start_event_monitoring()
        else:
            self.log("Erro ao iniciar monitoramento", "ERROR")
            self.update_status("Erro", "red")
            messagebox.showerror("Erro", "Não foi possível iniciar o monitoramento")
    
    def run_server(self):
        """Executa o servidor uvicorn"""
        try:
            uvicorn.run(
                app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
        except Exception as e:
            self.log(f"Erro no servidor: {e}", "ERROR")
    
    def stop_server(self):
        """Para o servidor SSE"""
        if not self.server_running:
            return
        
        self.log("Parando servidor...")
        self.update_status("Parando...", "yellow")
        
        stop_monitoring()
        
        self.server_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.browse_button.config(state='normal')
        
        self.update_status("Parado", "red")
        self.log("Servidor parado")
        
        # Nota: O uvicorn não para graciosamente em thread, mas o processo pai controla
        messagebox.showinfo(
            "Informação",
            "Para parar completamente o servidor, feche o aplicativo."
        )
    
    def start_event_monitoring(self):
        """Inicia monitoramento de eventos via SSE"""
        thread = threading.Thread(target=self.monitor_events, daemon=True)
        thread.start()
    
    def monitor_events(self):
        """Monitora eventos do servidor SSE"""
        import sseclient
        import requests
        
        # Aguarda servidor iniciar
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
        """Processa um evento recebido"""
        self.event_count += 1
        self.events_list.append({"type": event_type, "data": data})
        
        # Atualiza contador
        self.events_count_label.config(text=f"📡 Eventos recebidos: {self.event_count}")
        
        # Adiciona evento à área de texto
        timestamp = datetime.now().strftime("%H:%M:%S")
        event_text = f"[{timestamp}] {event_type}\n{json.dumps(data, indent=2)}\n{'='*60}\n"
        
        self.events_text.insert(tk.END, event_text)
        self.events_text.see(tk.END)
        
        # Atualiza estatísticas
        self.update_stats()
        
        # Limita número de eventos exibidos
        if self.event_count % 50 == 0:
            self.events_text.delete(1.0, "10.0")
    
    def update_stats(self):
        """Atualiza estatísticas"""
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
        """Limpa a lista de eventos"""
        self.events_text.delete(1.0, tk.END)
        self.log("Eventos limpos")
    
    def clear_logs(self):
        """Limpa os logs"""
        self.logs_text.delete(1.0, tk.END)


def main():
    """Função principal"""
    root = tk.Tk()
    app = EliteSSEGUI(root)
    
    def on_closing():
        if app.server_running:
            if messagebox.askokcancel("Sair", "O servidor ainda está rodando. Deseja realmente sair?"):
                stop_monitoring()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
