# Amontoa Server Hub

Hub utilitário pessoal com 12 módulos, customização de dashboard por conta e controles de isolamento de dados. Desenvolvido com FastAPI + React 19 (Vite), empacotado e orquestrado com Docker Compose (com suporte a Docker Swarm), incluindo stack própria de MongoDB.

---

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) e **Docker Compose** (incluso no Docker Desktop ou via plugin `docker-compose-plugin` no Linux)
- Git

*(Opcional, apenas para desenvolvimento local sem containers de app: Python 3.11+ e Node.js 20+)*

---

## Inicialização e Build em Localhost (Docker Compose)

O modo mais simples e recomendado para rodar a aplicação completa localmente é utilizando o **Docker Compose**, que agora inclui a stack do MongoDB, o backend FastAPI e o frontend React.

### 1. Configurar as variáveis de ambiente

Copie o arquivo de exemplo de variáveis de ambiente:

```bash
cp .env_sample .env
# ou: cp .env.example .env
```

> **Nota:** Por padrão, o `.env` já vem pré-configurado para o Docker Compose com `MONGODB_URI=mongodb://mongodb:27017/amotoa`. A porta `27017` do MongoDB também é exposta para o seu localhost, permitindo conexão direta por ferramentas como MongoDB Compass ou mongosh.

### 2. Construir e inicializar a stack

Para construir as imagens do backend e frontend e iniciar todos os serviços (MongoDB, Backend e Frontend):

```bash
# Inicialização em segundo plano (detached):
docker compose up --build -d
```

Ou, se desejar acompanhar a saída de logs diretamente no terminal:

```bash
docker compose up --build
```

O compose aguardará a inicialização e o teste de saúde (*healthcheck*) do MongoDB antes de iniciar o backend.

### 3. Comandos úteis de gerenciamento

- **Acompanhar logs:**
  ```bash
  # Todos os serviços
  docker compose logs -f

  # Apenas backend ou frontend ou mongodb
  docker compose logs -f backend
  docker compose logs -f frontend
  docker compose logs -f mongodb
  ```

- **Ver status dos containers:**
  ```bash
  docker compose ps
  ```

- **Parar a stack:**
  ```bash
  docker compose down
  ```

- **Parar e limpar os volumes (reseta o banco MongoDB):**
  ```bash
  docker compose down -v
  ```

- **Reconstruir as imagens sem cache:**
  ```bash
  docker compose build --no-cache
  docker compose up -d
  ```

---

## Acesso aos Serviços

Após a inicialização, os serviços estarão acessíveis nos seguintes endereços:

| Serviço | Endereço | Descrição |
|---|---|---|
| **Frontend** | [http://localhost:3000](http://localhost:3000) | Interface do dashboard |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | API REST FastAPI |
| **Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Documentação interativa da API |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Documentação alternativa da API |
| **MongoDB** | `localhost:27017` | Banco de dados (Compass / mongosh) |

---

## Desenvolvimento Local (Híbrido / sem Docker na aplicação)

Se você preferir executar o backend e/ou frontend diretamente na máquina local com *hot-reload*, você pode utilizar o Docker apenas para o banco de dados MongoDB:

### 1. Iniciar apenas o MongoDB no Docker:
```bash
docker compose up mongodb -d
```

### 2. Rodar o Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Como o MongoDB está exposto na porta 27017 do host:
MONGODB_URI=mongodb://localhost:27017/amotoa uvicorn src.main:app --reload --port 8000
```

### 3. Rodar o Frontend:
```bash
cd frontend
npm install
npm run dev   # Executa em http://localhost:3000 (ou porta indicada pelo Vite)
```

---

## Deploy com Docker Swarm (Opcional)

Se preferir fazer o deploy em modo cluster/swarm:

```bash
# 1. Inicializar o Swarm (caso ainda não esteja ativo)
docker swarm init

# 2. Construir as imagens
docker build -t amontoa-backend:latest ./backend
docker build -t amontoa-frontend:latest ./frontend

# 3. Fazer deploy da stack
docker stack deploy -c docker-compose.yml amontoa
```

---

## Variáveis de Ambiente

Configurações disponíveis no arquivo `.env`:

| Variável | Descrição | Valor Padrão |
|---|---|---|
| `MONGODB_URI` | URI de conexão com o MongoDB | `mongodb://mongodb:27017/amotoa` (no Compose) ou `mongodb://localhost:27017/amotoa` (dev local) |
| `MONGODB_PORT` | Porta mapeada no host para o container do MongoDB | `27017` |
| `BACKEND_PORT` | Porta mapeada no host para o container do Backend | `8000` |
| `FRONTEND_PORT` | Porta mapeada no host para o container do Frontend | `3000` |
| `PROJECT_NAME` | Nome do projeto / identificador da aplicação | `"Amontoa Server Hub"` |
| `API_V1_STR` | Prefixo das rotas v1 da API | `/api` |
| `VITE_API_URL` | URL que a interface no navegador usa para chamar a API | `http://localhost:8000` |

---

## Funcionalidades

- **Grid com 12 módulos** com cards em estilo glassmorphism.
- **Alternador de contas** — troca dinâmica entre `car-j works` e `car-j home` sem barreiras de autenticação.
- **Painel de customização** — exibir/ocultar módulos por perfil de conta.
- **Isolamento de dados** — alternância de visibilidade Compartilhada (*Shared*) ou Separada (*Separated*) por módulo:
  - *Shared → Separated*: escolha qual conta herda os dados existentes.
  - *Separated → Shared*: os registros de ambas as contas são mesclados automaticamente.
- **Placeholder WIP** — módulos em construção exibem tela personalizada "em desenvolvimento".

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| **Backend** | Python 3.11 · FastAPI · Motor (Async MongoDB Driver) |
| **Frontend** | React 19 · Vite · Tailwind CSS · Axios · Lucide Icons |
| **Database** | MongoDB 7.0 (Container com persistência em volume `mongodb_data`) |
| **Infra/Orquestração** | Docker Compose · Docker Swarm (compatível) · Redes bridge |
