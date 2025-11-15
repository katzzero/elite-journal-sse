# 🚀 Elite Dangerous SSE Server

Servidor SSE (Server-Sent Events) local para transmitir eventos do Elite Dangerous em tempo real na rede local.

## 📋 Características

- ✅ **Monitoramento em tempo real** dos arquivos de journal do Elite Dangerous
- ✅ **SSE (Server-Sent Events)** para streaming eficiente de dados
- ✅ **Interface web** integrada para visualização de eventos
- ✅ **Instalação automática** de dependências
- ✅ **Detecção automática** da pasta de journals
- ✅ **Acesso na rede local** - conecte de qualquer dispositivo
- ✅ **Suporte multiplataforma** (Windows, Linux com Proton)
- ✅ **Reconexão automática** em caso de desconexão

## 🎯 Como funciona

O servidor monitora os arquivos de journal do Elite Dangerous (formato JSON line-delimited) localizados em:
- **Windows**: `C:\Users\<Usuario>\Saved Games\Frontier Developments\Elite Dangerous\`
- **Linux/Proton**: `~/.steam/steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous`

Quando novos eventos são detectados, eles são transmitidos via SSE para todos os clientes conectados.

## 🛠️ Instalação

### Requisitos

- Python 3.8 ou superior
- Elite Dangerous instalado

### Instalação Rápida

1. Clone ou baixe este repositório
2. Execute o script de instalação:

**Windows:**
```bash
python setup.py
```

**Linux/Mac:**
```bash
python3 setup.py
```

O script irá:
- ✅ Verificar a versão do Python
- ✅ Instalar todas as dependências automaticamente
- ✅ Detectar a pasta de journals do Elite Dangerous
- ✅ Criar scripts de inicialização convenientes

## 🚀 Uso

### Iniciar o Servidor

**Windows:**
```bash
start_server.bat
```

**Linux/Mac:**
```bash
./start_server.sh
```

Ou diretamente:
```bash
python server.py
```

### Acessar a Interface

1. **No mesmo computador**: 
   - Abra o navegador em: `http://localhost:8000`

2. **De outros dispositivos na rede local**:
   - Descubra seu IP local (comando `ipconfig` no Windows ou `ip addr` no Linux)
   - Acesse: `http://<seu-ip-local>:8000`
   - Exemplo: `http://192.168.1.100:8000`

### Conectar via SSE

Para integrar com sua própria aplicação:

```javascript
const eventSource = new EventSource('http://localhost:8000/events');

// Evento de conexão
eventSource.addEventListener('connected', (e) => {
    const data = JSON.parse(e.data);
    console.log('Conectado:', data);
});

// Eventos específicos do Elite Dangerous
eventSource.addEventListener('FSDJump', (e) => {
    const data = JSON.parse(e.data);
    console.log('Salto hiperespacial:', data);
});

// Todos os eventos
eventSource.onmessage = (e) => {
    const data = JSON.parse(e.data);
    console.log('Evento:', data);
};
```

## 📡 Endpoints da API

### `GET /events`
Endpoint SSE principal que transmite todos os eventos do Elite Dangerous.

**Headers de resposta:**
- `Content-Type: text/event-stream`
- `Cache-Control: no-cache`
- `Connection: keep-alive`

**Formato dos eventos:**
```
event: FSDJump
data: {"event":"FSDJump","timestamp":"2025-11-15T10:12:34Z","StarSystem":"Sol",...}
```

### `GET /health`
Endpoint de health check.

**Resposta:**
```json
{
    "status": "ok",
    "monitoring": true,
    "current_journal": "Journal.2025-11-15T101234.01.log"
}
```

### `GET /`
Interface web integrada para visualização de eventos.

## ⚙️ Configuração Avançada

### Configurar pasta de journals customizada

Se seus arquivos de journal estão em um local diferente:

**Windows:**
```cmd
set ELITE_JOURNAL_PATH=C:\Caminho\Custom\Para\Journals
python server.py
```

**Linux/Mac:**
```bash
export ELITE_JOURNAL_PATH=/caminho/custom/para/journals
python3 server.py
```

### Configurar porta customizada

Edite o arquivo `server.py` e modifique a variável `PORT`:

```python
PORT = 8080  # Altere para a porta desejada
```

## 🔧 Tecnologias Utilizadas

- **FastAPI** - Framework web moderno e rápido
- **Uvicorn** - Servidor ASGI de alta performance
- **Watchdog** - Monitoramento de sistema de arquivos
- **SSE (Server-Sent Events)** - Protocolo de streaming unidirecional

## 📊 Tipos de Eventos Suportados

O servidor transmite TODOS os eventos do Elite Dangerous, incluindo:

- `Fileheader` - Cabeçalho do arquivo de journal
- `Location` - Localização atual
- `FSDJump` - Salto hiperespacial
- `Docked` / `Undocked` - Docagem/desacoplamento
- `SupercruiseEntry` / `SupercruiseExit` - Entrada/saída do supercruise
- `Scan` - Escaneamento de corpos celestes
- `Materials` - Coleta de materiais
- `Bounty` - Recompensas
- `MissionAccepted` / `MissionCompleted` - Missões
- E muitos outros...

## 🔒 Segurança

- O servidor é configurado para escutar em `0.0.0.0` permitindo acesso apenas na rede local
- Não há autenticação - adequado apenas para uso em rede local confiável
- Para exposição na internet, implemente autenticação adicional

## 🐛 Solução de Problemas

### Servidor não encontra os arquivos de journal

1. Verifique se o Elite Dangerous está gerando os journals:
   - Jogue alguns minutos
   - Verifique manualmente a pasta de Saved Games

2. Configure manualmente via variável de ambiente `ELITE_JOURNAL_PATH`

### Não consigo acessar de outros dispositivos

1. Verifique o firewall do Windows/Linux
2. Certifique-se de que a porta 8000 está liberada
3. Use o IP local correto (não use 127.0.0.1 ou localhost)

### Eventos não aparecem em tempo real

1. Certifique-se de que o Elite Dangerous está rodando
2. Verifique se há atividade no jogo (alguns eventos só ocorrem durante gameplay)
3. Observe os logs do servidor no terminal

## 📝 Licença

MIT License - Sinta-se livre para usar, modificar e distribuir.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Enviar pull requests

## 📧 Suporte

Para questões e suporte, abra uma issue no repositório.

---

**Fly safe, Commander! o7**
