<div align="center">
  <img src="https://raw.githubusercontent.com/CarlosWilliamsR/OpenS-Project/main/public/logo.png" alt="OpenS Logo" width="150" height="150" />
  <h1>OpenS · CRM Médico Inteligente (AI + Voice + Web3)</h1>
  <p><em>Proyecto oficial para Solana Colosseum · evolución de la participación en Hackathon 3 Devpack.</em></p>

  [![Astro](https://img.shields.io/badge/Astro-FF5D01?style=for-the-badge&logo=astro&logoColor=white)](https://astro.build/)
  [![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
  [![Solana](https://img.shields.io/badge/Solana-14F195?style=for-the-badge&logo=solana&logoColor=black)](https://solana.com/)
  [![Anchor](https://img.shields.io/badge/Anchor-2E2E2E?style=for-the-badge&logo=solana&logoColor=14F195)](https://www.anchor-lang.com/)
  [![Ollama](https://img.shields.io/badge/Ollama-111111?style=for-the-badge)](https://ollama.com/)
  [![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
  [![ElevenLabs](https://img.shields.io/badge/ElevenLabs-000000?style=for-the-badge)](https://elevenlabs.io/)
  [![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
</div>

---

## 📌 ¿Qué es OpenS?

**OpenS** es un CRM médico asistido por IA para atención primaria, diseñado para operar en contextos reales con conectividad variable:

1. **IA clínica híbrida** (Gemini en nube + Qwen local vía Ollama como fallback).
2. **Síntesis de voz** (ElevenLabs con fallback local).
3. **Persistencia clínica** en Supabase/PostgreSQL.
4. **Inmutabilidad Web3** al sellar diagnósticos en **Solana Devnet** mediante un programa Anchor.

---

## 🖼️ Multimedia de la demo

| Home | Asistente | Admin |
| --- | --- | --- |
| <img src="multimedia/home.png" width="260" /> | <img src="multimedia/assistant.png" width="260" /> | <img src="multimedia/admin.png" width="260" /> |

<div align="center">
  <img src="multimedia/demo.gif" alt="OpenS Demo" width="820" />
</div>

---

## 🏗️ Arquitectura técnica (detallada)

```mermaid
graph TD
    subgraph Client["Frontend (Astro + TS + Tailwind)"]
        UI["UI clínica"]
        Pipeline["Pipeline de cierre"]
    end

    subgraph API["Backend (FastAPI / Python)"]
        Router["REST /api/v1"]
        AI["Asistente IA"]
        TTS["Síntesis de voz"]
        Seal["Seal Record (Web3)"]
    end

    subgraph Data["Persistencia"]
        Supa["Supabase (PostgreSQL)"]
    end

    subgraph Models["Motores de IA"]
        Gemini["Gemini 2.5 Flash (cloud)"]
        Ollama["Ollama local (Qwen)"]
    end

    subgraph Chain["Blockchain"]
        Anchor["Programa Anchor"]
        Sol["Solana Devnet"]
    end

    UI --> Router
    Pipeline --> Router
    Router --> AI
    AI --> Gemini
    AI --> Ollama
    Router --> TTS
    Router --> Supa
    Router --> Seal
    Seal --> Anchor
    Anchor --> Sol
    Seal --> Supa
```

### Flujo clínico end-to-end

```mermaid
sequenceDiagram
    participant D as Doctor UI
    participant B as FastAPI
    participant G as Gemini
    participant O as Ollama/Qwen
    participant E as ElevenLabs
    participant S as Solana/Anchor
    participant DB as Supabase

    D->>B: POST /assistant/ask
    alt Gemini disponible
      B->>G: Prompt clínico
      G-->>B: Respuesta IA
    else Fallback local
      B->>O: Prompt clínico
      O-->>B: Respuesta Qwen
    end
    B-->>D: Diagnóstico asistido

    D->>B: POST /assistant/tts
    B->>E: TTS request
    E-->>B: Audio mpeg
    B-->>D: Audio respuesta

    D->>B: POST /assistant/seal_record
    B->>S: register_record(hash)
    S-->>B: tx signature + PDA
    B->>DB: insert medical_records
    B-->>D: Estado final + solscan_url
```

---

## 🧰 Infraestructura y componentes

| Capa | Componente | Rol |
| --- | --- | --- |
| Frontend | Astro + TypeScript | Interfaz médica, dashboard y orquestación UX del pipeline. |
| Backend | FastAPI | API principal, integración con IA, TTS, Supabase y Solana. |
| IA Cloud | Gemini 2.5 Flash | Motor principal para respuestas clínicas. |
| IA Local | Ollama + Qwen2.5 | Fallback offline/edge cuando falla la nube. |
| Voz | ElevenLabs | Síntesis de voz de alta naturalidad. |
| Base de datos | Supabase PostgreSQL | Pacientes, historial médico y metadata de sellado. |
| Blockchain | Solana Devnet + Anchor | Registro inmutable de hash clínico y trazabilidad. |
| Observabilidad local | scripts de testing | Verificación de integraciones y smoke tests de API. |

---

## ⚙️ Requisitos

1. **Python 3.11+**
2. **Node.js 22+**
3. **Git**
4. **Ollama** (si usarás fallback local Qwen)
5. **Solana CLI + wallet devnet** (para sellado real)
6. Credenciales:
   - Supabase (`SUPABASE_URL`, `SUPABASE_KEY`)
   - Gemini (`GOOGLE_API_KEY` o `GEMINI_API_KEY`)
   - ElevenLabs (`ELEVENLABS_API_KEY`)
   - Solana (`SOLANA_PROGRAM_ID`, wallet local o `SOLANA_KEYPAIR_JSON`)

---

## 🚀 Ejecución local paso a paso

### 1) Clonar repositorio

```bash
git clone https://github.com/CarlosWilliamsR/OpenS-Project.git
cd OpenS-Project
```

### 2) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configura `backend/.env`:

```env
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODELS=qwen2.5:7b
SUPABASE_URL=
SUPABASE_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
SOLANA_PROGRAM_ID=8AcadEGS6Vmcj7kcQ8WroPoWioNkBhXFjkH8Db5hSVUX
```

Ejecutar backend:

```bash
python main.py
```

Backend: `http://localhost:8000`

### 3) Ollama + Qwen (fallback local)

```bash
ollama pull qwen2.5:7b
ollama list
```

### 4) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000`

Si desplegas backend en otro host, define:

```env
PUBLIC_BACKEND_URL=https://tu-backend.com/api/v1
```

---

## ✅ Tests de verificación (Supabase, ElevenLabs, Gemini, Qwen, Solana)

### A. Verificar integraciones externas

```bash
cd backend
source .venv/bin/activate
python test_integrations.py --strict
```

Valida:
1. Supabase
2. Gemini
3. Ollama/Qwen
4. ElevenLabs
5. Solana Devnet

### B. Verificar API end-to-end del backend

Con backend ya corriendo:

```bash
cd backend
source .venv/bin/activate
python test_backend.py --base-url http://localhost:8000 --strict
```

Valida endpoints:
- `/`
- `/api/v1/patients`
- `/api/v1/patients/{id}/records`
- `/api/v1/assistant/ask`
- `/api/v1/assistant/tts`
- `/api/v1/assistant/seal_record`

---

## 🧭 Paso a paso para desplegar (hackathon-ready)

### 1) Supabase

1. Crea proyecto Supabase.
2. Crea tablas `patients` y `medical_records`.
3. Usa `SUPABASE_URL` + `SUPABASE_KEY` en backend.
4. Si tu proyecto usa el nuevo comportamiento de Data API (2026), asegura grants explícitos:

```sql
grant select, insert, update, delete on public.patients to service_role;
grant select, insert, update, delete on public.medical_records to service_role;
alter table public.patients enable row level security;
alter table public.medical_records enable row level security;
```

### 2) Smart contract (Solana/Anchor)

1. Confirma `program_id` del contrato (`anchor_program/Anchor.toml` y `lib.rs`).
2. Mantén wallet de devnet con balance:

```bash
solana airdrop 2
```

3. Exporta `SOLANA_PROGRAM_ID` en backend.

### 3) Backend (Render/HF/DO)

1. Root: `backend/`
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Variables: todas las de `backend/.env`

### 4) Frontend (Vercel/Cloudflare)

1. Root: `frontend/`
2. Build command: `npm run build`
3. Variables: `PUBLIC_BACKEND_URL` apuntando al backend de producción.

---

## ⚠️ ¿Qué pasa si la demo no corre correctamente?

| Síntoma | Causa probable | Acción recomendada |
| --- | --- | --- |
| `Supabase permission denied` | Falta de grants o credenciales incorrectas | Revisa `SUPABASE_URL/SUPABASE_KEY`, grants explícitos y RLS. |
| Gemini no responde | API key inválida o agotada | Verifica `GOOGLE_API_KEY`; usa fallback Qwen con Ollama. |
| Qwen no responde | Ollama detenido o modelo ausente | `ollama list`, luego `ollama pull qwen2.5:7b`. |
| TTS falla | `ELEVENLABS_API_KEY` inválida/sin créditos | Revisa key y voice id; el backend tiene fallback de voz local. |
| Error en sellado Solana | Wallet sin saldo, RPC caído o program_id incorrecto | `solana airdrop 2`, revisa `SOLANA_PROGRAM_ID`, repite test backend. |
| Frontend no conecta al backend | URL de API incorrecta | Ajusta `PUBLIC_BACKEND_URL` o usa `http://localhost:8000/api/v1`. |

---

## 🔐 Seguridad y buenas prácticas

1. Nunca publiques `SUPABASE_KEY` de tipo `service_role` en frontend.
2. Mantén secretos solo en variables de entorno.
3. Usa RLS + políticas explícitas para acceso por rol.
4. No almacenes PHI sensible en logs.
5. Mantén rotación periódica de keys API.

---

## 👥 Equipo y créditos

- 💻 **Carlos Williams** — **Fundador y Desarrollador Principal**.
- 🎨 **Aysha Tovar** — UX/UI Design.
- 🤝 **Santiago Valecillos** — Colaborador (ediciones previas, no en esta edición).
- 🤝 **Gabriela Carpio** — Colaboradora (ediciones previas, no en esta edición).

Proyecto preparado para **Solana Colosseum Hackathon** y con continuidad desde **Hackathon 3 Devpack**.
