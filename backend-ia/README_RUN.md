# OpenS — Instrucciones rápidas para ejecutar el proyecto

Este documento proporciona un paso a paso mínimo y reproducible para levantar el proyecto OpenS localmente (backend + frontend). Asume que estás en Linux.

## Requisitos previos

- Python 3.11+
- Node.js 22+
- Git
- (Opcional) Ollama si quieres usar modelos locales
- Cuenta y proyecto en Supabase (para la base de datos)

## 1) Clonar el repositorio

```bash
git clone <repo-url> opens
cd opens
# o si ya lo tienes: cd /ruta/al/proyecto
```

## 2) Preparar variables de entorno

Copia la plantilla y edita las variables:

```bash
cd backend-ia
cp .env.example .env
# Edita backend-ia/.env y agrega SUPABASE_URL, SUPABASE_KEY y, si las tienes, GOOGLE_API_KEY y ELEVENLABS_API_KEY
```

Valores importantes a completar en `backend-ia/.env`:
- `SUPABASE_URL` → URL de tu proyecto Supabase
- `SUPABASE_KEY` → `service_role` key (no uses `anon` en desarrollo con privilegios)
- `GOOGLE_API_KEY` → (opcional) para Gemini
- `OLLAMA_BASE_URL` → `http://localhost:11434` si usas Ollama local

## 3) Crear tablas en Supabase

1. Abre tu proyecto en https://app.supabase.com
2. Ve a _SQL Editor_ → _New query_
3. Copia y pega el contenido de `Base de Datos/supabase_schema.sql` y ejecútalo

(Archivo: `Base de Datos/supabase_schema.sql`)

## 4) (Opcional) Instalar Ollama y modelos locales

Instala Ollama siguiendo sus instrucciones:

```bash
curl -fsSL https://ollama.com/install.sh | sh
# luego, por ejemplo:
ollama pull qwen2.5:7b
ollama pull llama3.2:3b
```

Verifica modelos:

```bash
ollama list
```

## 5) Ejecutar Backend (FastAPI)

Recomiendo crear un entorno virtual y luego instalar el paquete en modo editable:

```bash
# Desde la raiz del repo:
cd backend-ia   # omite esta linea si ya estas dentro de backend-ia
python3 -m venv .venv

# Activa el entorno segun tu shell
# bash/zsh:
source .venv/bin/activate
# fish:
# source .venv/bin/activate.fish

# Verifica que python y pip apunten al venv (deben incluir .venv)
which python3
which pip

python3 -m pip install --upgrade pip
python3 -m pip install -e ..
# (opcional) o instalar requirements si existen
# python3 -m pip install -r requirements.txt

# Iniciar la API
python3 main.py
# Alternativamente con uvicorn si está disponible:
# uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Si aparece el error `externally-managed-environment`, normalmente significa que no quedo activado el entorno virtual y estas intentando instalar en Python del sistema. Revisa el paso de activacion (en fish usa `activate.fish`) y repite la instalacion.

El backend quedará disponible en `http://localhost:8001`.

Comprobar salud:

```bash
curl http://localhost:8001/health
```

Comprobar modelos locales (si usas Ollama):

```bash
curl http://localhost:8001/api/v1/local-models
```

## 6) Ejecutar Frontend (Astro)

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

El frontend por defecto está en `http://localhost:5000` (ver salida de `npm run dev`).

## 7) Rutas útiles

- Health: `GET /health`
- Local models: `GET /api/v1/local-models`
- Preguntar al asistente: `POST /api/v1/assistant/ask`
- Listar pacientes: `GET /api/v1/patients`

## 8) Pruebas rápidas

- Desde el backend en ejecución prueba:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/local-models
```

- Desde el frontend, abre `http://localhost:5000` y navega a `/asistente`.

## 9) Resolución de problemas comunes

- Puerto en uso: revisa procesos con `ss -ltnp` o `ps aux | grep uvicorn`.
- Ollama no responde: asegúrate de que Ollama esté corriendo y que `OLLAMA_BASE_URL` apunte correctamente.
- Errores de Supabase: valida `SUPABASE_URL` y `SUPABASE_KEY`; revisa que las tablas existan y las políticas RLS no bloqueen consultas.

## 10) ¿Qué sigue?

- Para producción: securizar políticas RLS en Supabase, no usar `service_role` en clientes, desplegar backend con un server manager y configurar variables en el entorno de producción.

## 11) Ejecutar todo con Docker (Linux)

Se agregaron estos archivos para contenedores:

- `docker-compose.yml`
- `backend-ia/Dockerfile`
- `frontend/Dockerfile`

Paso a paso:

1. Asegura el archivo de variables del backend:

```bash
cp backend-ia/.env.example backend-ia/.env
# edita backend-ia/.env con tus credenciales reales
```

2. (Opcional) Si usarás Ollama local en tu host Linux, levanta Ollama antes:

```bash
ollama serve
```

3. Construye e inicia backend + frontend:

```bash
docker compose up --build -d
```

4. Revisa que ambos servicios estén arriba:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

5. Pruebas rápidas:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/local-models
```

6. Abre la app:

- Frontend: `http://localhost:5000`
- Backend: `http://localhost:8001`

7. Para detener todo:

```bash
docker compose down
```

Notas:

- Dentro de Docker, el frontend usa `http://backend:8001` para el proxy interno.
- Si Ollama corre en tu máquina host, el backend usa `host.docker.internal` (configurado en compose con `host-gateway`).

---

Si quieres, sustituyo el `README.md` principal por estas instrucciones o las incorporo como sección dentro de `README.md` existente. ¿Qué prefieres?