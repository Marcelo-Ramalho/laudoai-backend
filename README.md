# LaudoAI — Backend API

Backend do LaudoAI construído com FastAPI + Supabase + Whisper + Claude API.

## Stack

- **Framework:** FastAPI
- **Banco:** Supabase (PostgreSQL)
- **IA Voz:** Whisper (OpenAI)
- **IA Texto:** Claude API (Anthropic)
- **Deploy:** Railway

## Instalação local

```bash
# Clonar e entrar na pasta
cd laudoai-backend

# Instalar dependências
pip install -r requirements.txt

# Copiar variáveis de ambiente
cp .env.example .env
# Preencher as chaves no .env

# Copiar banco de patologias
# Coloque o arquivo banco_patologias_laudoai_v3.json na raiz do projeto

# Rodar
uvicorn main:app --reload
```

## Endpoints

### Users
- `POST /users/` — criar engenheiro
- `GET /users/{id}` — buscar por ID
- `GET /users/email/{email}` — buscar por email
- `PATCH /users/{id}` — atualizar perfil
- `DELETE /users/{id}` — deletar conta (LGPD)

### Laudos
- `POST /laudos/` — criar laudo
- `GET /laudos/{id}` — buscar laudo com itens
- `GET /laudos/user/{user_id}` — listar laudos do engenheiro
- `PATCH /laudos/{id}` — atualizar laudo
- `DELETE /laudos/{id}` — deletar laudo

### Itens do Laudo
- `POST /laudos/{id}/itens/voz` — adicionar item por áudio
- `POST /laudos/{id}/itens/texto` — adicionar item por texto
- `DELETE /laudos/{id}/itens/{item_id}` — deletar item

## Documentação automática

Com o servidor rodando acesse:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deploy no Railway

1. Push pro GitHub
2. Conectar repositório no Railway
3. Adicionar variáveis de ambiente
4. Deploy automático

## Fluxo de processamento de anomalia

```
Áudio do engenheiro
    ↓
Whisper API → Transcrição PT-BR
    ↓
Busca no banco de patologias (JSON) → Jaccard similarity
    ↓ (se não achar)
Claude API → JSON estruturado
    ↓
Salva no Supabase
```
