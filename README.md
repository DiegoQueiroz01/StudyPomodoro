# 🍅 Discord Study Pomodoro Bot

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-v2.3%2B-blueviolet.svg)](https://discordpy.readthedocs.io/)
[![Database](https://img.shields.io/badge/database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

O **Discord Study Pomodoro Bot** é um bot interativo voltado para produtividade e foco em comunidade. Ele integra a técnica **Pomodoro** aos canais de voz do Discord, monitorando participantes em tempo real, fornecendo feedbacks visuais ricos em `discord.Embed` e salvando o histórico de estudo de cada membro em um banco de dados **SQLite**.

---

## 🎯 Principais Funcionalidades

- ⏱️ **Gerenciador de Ciclos Pomodoro:**
  - Alternância automática entre fases de **Foco (25 min)**, **Pausa Curta (5 min)** e **Pausa Longa (15 min)** a cada 4 ciclos.
  - Temporizadores não-bloqueantes executados de forma totalmente assíncrona.

- 🔊 **Integração com Canais de Voz:**
  - Validação de presença do usuário em salas de voz.
  - **Rastreamento Dinâmico em Tempo Real:** Escuta entradas e saídas de membros durante a sessão através do evento `on_voice_state_update`.

- 📊 **Persistência de Dados e Perfil:**
  - Registro de minutos efetivamente estudados e total de ciclos concluídos por usuário no SQLite.
  - Comando `/perfil` para consulta das estatísticas individuais acumuladas.

- 🕹️ **Controle Total da Sessão:**
  - Comandos para iniciar (`/pomodoro_iniciar`), pausar (`/pomodoro_pausar`), retomar (`/pomodoro_continuar`), checar status (`/pomodoro_status`) e encerrar (`/pomodoro_parar`).

- 🎨 **Interface Rápida e Moderna:**
  - Suporte completo a **Slash Commands (`/`)**.
  - Notificações visualmente atraentes com cartões coloridos (`discord.Embed`).

- 🏗️ **Arquitetura Modular (Cogs):**
  - Código estruturado com separação clara de responsabilidades (Cogs, Services, Utilities e Database Layer).

---

## 📂 Arquitetura do Projeto

discord-pomodoro-bot/
├── src/
│   ├── cogs/                 # Módulos de comandos e ouvintes de eventos do Discord
│   │   └── pomodoro_cog.py
│   ├── services/             # Regras de negócio e camada de acesso ao banco
│   │   ├── database_service.py
│   │   └── pomodoro_service.py
│   ├── utils/                # Utilitários e fábrica de Embeds visuais
│   │   └── embed_factory.py
│   └── bot.py                # Ponto de entrada (Bootstrap do bot)
├── .env.example              # Modelo de variáveis de ambiente
├── .gitignore                # Exclusão de segredos e arquivos gerados
├── requirements.txt          # Dependências Python do projeto
└── README.md                 # Documentação oficial

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **API do Discord:** discord.py
- **Assincronismo:** asyncio
- **Banco de Dados:** SQLite3 (nativo do Python)
- **Segurança de Variáveis:** python-dotenv

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos
- Python 3.10 ou superior instalado na sua máquina.
- Uma aplicação de Bot criada no Discord Developer Portal com a **Server Members Intent** ativada.

### Passo a Passo

1. **Clone este repositório:**
   git clone https://github.com/SeuUsuario/discord-pomodoro-bot.git
   cd discord-pomodoro-bot

2. **Crie e ative o ambiente virtual:**
   - **Windows (PowerShell):**
     python -m venv venv
     .\venv\Scripts\Activate.ps1
   - **Linux / macOS:**
     python3 -m venv venv
     source venv/bin/activate

3. **Instale as dependências:**
   pip install -r requirements.txt

4. **Configure as Variáveis de Ambiente:**
   Crie um arquivo `.env` na raiz do projeto com base no arquivo `.env.example`:
   DISCORD_TOKEN=seu_token_aqui

5. **Inicie o Bot:**
   python src/bot.py

---

## 📌 Comandos do Bot

- `/pomodoro_iniciar`: Inicia uma nova sessão Pomodoro no seu canal de voz.
- `/pomodoro_pausar`: Congela temporariamente a contagem do temporizador.
- `/pomodoro_continuar`: Retoma a contagem de onde parou.
- `/pomodoro_status`: Exibe o tempo restante, a fase atual e os participantes ativos.
- `/pomodoro_parar`: Encerra a sessão atual do servidor.
- `/perfil`: Exibe seu tempo total acumulado de estudo e ciclos concluídos.
- `/ping`: Responde com a latência atual do bot.

---

## 🔒 Segurança

O arquivo `.env` contendo o Token de autenticação da API do Discord é expressamente mantido fora do controle de versão pelo `.gitignore`. **Nunca envie suas chaves de API para repositórios públicos.**

---

## 📝 Licença

Este projeto está sob a licença MIT.