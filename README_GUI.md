# 🚀 Elite Dangerous SSE Server - Interface Gráfica

## Sobre

Interface gráfica (GUI) para o servidor SSE do Elite Dangerous, permitindo controlar e monitorar o servidor de forma visual e intuitiva.

## Recursos

### 🎮 Controle do Servidor
- **Iniciar/Parar Servidor**: Botões para controlar o servidor SSE
- **Seleção de Pasta**: Escolha a pasta dos journals do Elite Dangerous
- **Status em Tempo Real**: Visualização do status do servidor

### 📡 Monitoramento de Eventos
- **Eventos em Tempo Real**: Visualiza todos os eventos do Elite Dangerous conforme ocorrem
- **Contador de Eventos**: Acompanhe quantos eventos foram recebidos
- **Formato JSON**: Eventos exibidos em formato JSON legível

### 📋 Logs do Sistema
- **Logs Detalhados**: Visualização de todos os logs do servidor
- **Timestamps**: Cada log com horário preciso
- **Níveis de Log**: INFO, ERROR, etc.

### 📊 Estatísticas
- **Contagem por Tipo**: Visualize quantos eventos de cada tipo foram recebidos
- **Total de Eventos**: Estatística geral de eventos processados

## Instalação

### Pré-requisitos

```bash
# Clone o repositório (se ainda não fez)
git clone https://github.com/katzzero/elite-journal-sse.git
cd elite-journal-sse

# Instale as dependências
pip install -r requirements.txt
```

### Dependências da GUI

A GUI utiliza `tkinter`, que já vem incluído no Python. As dependências adicionais são:

- `requests`: Para comunicação HTTP
- `sseclient-py`: Para receber eventos SSE

## Como Usar

### Iniciando a GUI

```bash
python gui.py
```

### Passo a Passo

1. **Execute o aplicativo**
   ```bash
   python gui.py
   ```

2. **Selecione a pasta de journals** (opcional)
   - Clique em "📁 Selecionar Pasta"
   - Navegue até a pasta onde o Elite Dangerous salva os journals
   - Padrão no Windows: `%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous`

3. **Inicie o servidor**
   - Clique em "▶️ Iniciar Servidor"
   - O status mudará para "Rodando" (verde)

4. **Monitore os eventos**
   - Abra o Elite Dangerous
   - Os eventos aparecerão automaticamente na aba "Eventos"
   - Acompanhe os logs na aba "Logs"
   - Veja as estatísticas na aba "Estatísticas"

5. **Pare o servidor quando terminar**
   - Clique em "⏸️ Parar Servidor"
   - Feche o aplicativo

## Interface

### Painel de Controle

```
┌────────────────────────────────────────┐
│  🚀 Elite Dangerous SSE Server  │
├────────────────────────────────────────┤
│ [▶️ Iniciar] [⏸️ Parar] [📁 Pasta] │
├────────────────────────────────────────┤
│ Status: Rodando ✅              │
│ 📂 Pasta: C:\Users\...         │
│ 🌐 URL: http://localhost:8000  │
│ 📡 Eventos recebidos: 42         │
└────────────────────────────────────────┘
```

### Abas

#### 1. 📡 Eventos
- Mostra todos os eventos em tempo real
- Formato JSON identado
- Auto-scroll para o último evento
- Botão para limpar eventos antigos

#### 2. 📋 Logs
- Logs do sistema com timestamps
- Mensagens de erro e informação
- Botão para limpar logs

#### 3. 📊 Estatísticas
- Total de eventos recebidos
- Contagem por tipo de evento
- Ordenado por frequência

## Execução em Paralelo

### Método 1: GUI com Servidor Integrado (Recomendado)

```bash
# Execute apenas a GUI - ela inicia o servidor automaticamente
python gui.py
```

A GUI:
- ✅ Inicia o servidor em uma thread separada
- ✅ Monitora eventos via SSE
- ✅ Permite controlar o servidor visualmente
- ✅ Exibe logs e estatísticas em tempo real

### Método 2: Servidor e GUI Separados

```bash
# Terminal 1: Inicie o servidor
python server.py

# Terminal 2: Inicie a GUI (conecta ao servidor existente)
python gui.py
```

## Atalhos de Teclado

| Atalho | Ação |
|--------|-------|
| `Ctrl+Q` | Fechar aplicativo |
| `Ctrl+L` | Limpar eventos |
| `Ctrl+K` | Limpar logs |

## Arquitetura

```
┌────────────────────────────────────────┐
│           gui.py (Tkinter)           │
│  [🖥️ Interface Gráfica do Usuário]  │
└────────────────┬───────────────────────┘
                 │
                 │ (Thread separada)
                 │
┌────────────────┴───────────────────────┐
│         server.py (FastAPI)         │
│    [🌐 Servidor SSE + Monitor]     │
└────────────────┬───────────────────────┘
                 │
                 │ (Watchdog)
                 │
┌────────────────┴───────────────────────┐
│    Elite Dangerous Journal Files    │
│          [📁 *.log]                │
└────────────────────────────────────────┘
```

### Fluxo de Dados

1. **Elite Dangerous** gera eventos → Grava em `Journal.*.log`
2. **Watchdog** detecta mudanças nos arquivos
3. **Server.py** lê novos eventos e transmite via SSE
4. **GUI** recebe eventos via SSE e atualiza a interface

## Personalização

### Alterar Porta

Edite o arquivo `gui.py`:

```python
self.port = 8000  # Altere para a porta desejada
```

### Alterar Cores

Edite as variáveis de cores no método `setup_ui()`:

```python
bg_color = '#1e1e1e'      # Cor de fundo
fg_color = '#ffffff'       # Cor do texto
accent_color = '#4CAF50'   # Cor de destaque
```

## Troubleshooting

### Erro: "Porta já em uso"

**Problema**: Outra aplicação está usando a porta 8000.

**Solução**:
1. Feche outros processos usando a porta
2. Ou altere a porta no arquivo `gui.py`

### Erro: "Pasta de journals não encontrada"

**Problema**: O caminho padrão dos journals não existe.

**Solução**:
1. Clique em "📁 Selecionar Pasta"
2. Navegue até a pasta correta dos journals do Elite Dangerous

### GUI não recebe eventos

**Possíveis causas**:
1. Servidor não está rodando
2. Elite Dangerous não está gerando eventos
3. Pasta de journals incorreta

**Solução**:
1. Verifique se o status está "Rodando" (verde)
2. Abra o Elite Dangerous e realize algumas ações
3. Verifique os logs na aba "Logs"

## Recursos Futuros

- [ ] Filtros de eventos
- [ ] Exportação de eventos para CSV/JSON
- [ ] Notificações desktop para eventos específicos
- [ ] Temas de cor (escuro/claro)
- [ ] Gráficos de estatísticas
- [ ] Histórico de sessões
- [ ] Integração com APIs externas (EDDN, EDSM, etc.)

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## Contato

- **GitHub**: [katzzero](https://github.com/katzzero)
- **Repositório**: [elite-journal-sse](https://github.com/katzzero/elite-journal-sse)

---

**Developed with ❤️ by [KatzZero](https://github.com/katzzero)**
