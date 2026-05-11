# 🚀 Guía de Despliegue - OpenS (Colosseum Hackathon)

Esta guía detalla el paso a paso para desplegar **OpenS** utilizando herramientas gratuitas y los beneficios del **GitHub Student Developer Pack 2026**.

## 🏗️ 1. Despliegue del Frontend (Astro)

Recomendamos **Vercel** o **Cloudflare Pages**, ya que ambos tienen soporte nativo para Astro y ofrecen una capa gratuita (Hobby) excelente.

### Usando Vercel (Gratis)
1. Inicia sesión en [Vercel](https://vercel.com/) con tu cuenta de GitHub.
2. Haz clic en **Add New Project** y selecciona el repositorio de `OpenS-Project`.
3. En la sección **Framework Preset**, selecciona **Astro**.
4. En **Root Directory**, selecciona la carpeta `frontend/` (si está en la raíz déjalo en `./`).
5. **Environment Variables:** Añade cualquier variable de entorno que esté en tu `frontend/.env` (ej. URLs de tu backend de producción, SUPABASE_URL, etc.).
6. Haz clic en **Deploy**. ¡Listo! Tendrás un link público en segundos.

## 🧠 2. Despliegue del Backend (FastAPI + AI)

El backend requiere Python y manejar integraciones. Las mejores opciones gratuitas o de estudiantes son:

### Opción A: Render (Capa Gratuita)
1. Ve a [Render.com](https://render.com) e inicia sesión.
2. Crea un nuevo **Web Service** conectado a tu repo de GitHub.
3. **Root Directory**: `backend-ia`
4. **Environment**: `Python 3`
5. **Build Command**: `pip install -r requirements.txt`
6. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. **Environment Variables**:
   Pega el contenido de tu `.env` (GOOGLE_API_KEY, SUPABASE_URL, ELEVENLABS_API_KEY, SOLANA_PROGRAM_ID, etc.).
8. Selecciona el plan **Free** y haz clic en Deploy.

### Opción B: Hugging Face Spaces (Gratis / Docker)
Como ya tienes un `Dockerfile` en `backend-ia`:
1. Ve a [Hugging Face Spaces](https://huggingface.co/spaces).
2. Crea un **New Space**.
3. Selecciona **Docker** como el SDK.
4. Sube tu código o conéctalo con tu repositorio de GitHub.
5. Configura los **Secrets** (en la pestaña de settings) con las variables de tu `.env`.
6. HF Spaces levantará automáticamente tu contenedor con FastAPI.

### Opción C: DigitalOcean (GitHub Student Pack)
El GitHub Student Pack te otorga créditos de DigitalOcean.
1. Crea un **App Platform** en DO o lanza un **Droplet**.
2. Conecta el repo y DO detectará automáticamente el Dockerfile o la app en Python.
3. El costo se descontará de los créditos estudiantiles gratuitos.

## 🗄️ 3. Base de Datos (Supabase)
Como ya estás utilizando Supabase Cloud, la base de datos ya está desplegada.
Asegúrate de:
1. Desactivar RLS (Row Level Security) temporalmente o configurar las políticas correctas de RLS para producción.
2. Usar las credenciales (URL y KEY) en el backend (Render/HF) de producción.

## ⛓️ 4. Blockchain (Solana Devnet)
El Smart Contract (Anchor Program) ya se encuentra desplegado en la Devnet.
- El `SOLANA_PROGRAM_ID` actual es válido para demostraciones.
- Para la demo de la hackathon, la Devnet es perfecta. Si en un futuro pasan a Mainnet, solo debes re-desplegar usando `anchor deploy --provider.cluster mainnet` y actualizar el `SOLANA_PROGRAM_ID` en el `.env` de producción.

---
> **Nota:** Si deseas que realice alguno de estos despliegues de forma automatizada por ti ahora mismo usando el CLI (ej. Vercel CLI / Hugging Face), por favor házmelo saber en el chat y lo haré encantado.
