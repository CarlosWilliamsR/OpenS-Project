

---

# OpenS: El CRM Médico Inteligente con Arquitectura Híbrida

**OpenS** es un ecosistema digital diseñado para fortalecer la atención primaria de salud, especialmente en comunidades vulnerables. Evoluciona de un asistente clínico a un **CRM Médico Integral** que fusiona inteligencia artificial avanzada con un repositorio centralizado de historiales clínicos para empoderar a los profesionales de la salud.

## 🌟 Visión General

El sistema permite a médicos y enfermeros gestionar interacciones, seguimientos y diagnósticos desde una plataforma unificada y humanizada. Su objetivo principal es eliminar la "brecha de olvido institucional" en centros de salud con alta rotación de personal, garantizando que el historial del paciente sea un activo para su recuperación.

### Beneficios Clave

* 
**Para el Médico:** Reduce la carga administrativa y proporciona resúmenes precisos para la toma de decisiones.


* 
**Para el Paciente:** Recibe atención informada y empática, con herramientas de accesibilidad de voz para personas con discapacidades o de la tercera edad.


* 
**Resiliencia:** Garantiza **Cero Tiempo de Inactividad** mediante una arquitectura que funciona con o sin internet.



---

## 🏗️ Arquitectura del Sistema

OpenS utiliza una arquitectura desacoplada y modular que separa la interfaz de usuario de la lógica de negocio y los servicios de IA.

### Diagrama de Infraestructura

```
┌─────────────┐     ┌──────────────────────────────┐
│   Frontend   │────▶│   Backend (FastAPI :8001)     │
│  Astro :5000 │     │                              │
│              │     │  ┌──────────┐  ┌───────────┐ │
│  /           │     │  │ Gemini   │  │  Ollama   │ │
│  /auth       │     │  │ (Cloud)  │──▶│  (Local)  │ │
│  /asistente  │     │  └──────────┘  │           │ │
│  /doctor     │     │     Falla?     │ qwen2.5   │ │
│  /paciente   │     │     ──────▶    │ kimi-k2   │ │
│  /admin      │     │               │ llama3.2  │ │
│  /seguros    │     │               │ mistral   │ │
│              │     │               │ deepseek  │ │
│              │     │               │ phi4-mini │ │
│              │     │               │ gemma3    │ │
│              │     │               └───────────┘ │
│              │     │       │                     │
│              │     │  ┌────▼─────┐  ┌──────────┐ │
│              │     │  │ Supabase │  │ElevenLabs│ │
│              │     │  │   (DB)   │  │  (Voz)   │ │
│              │     │  └──────────┘  └──────────┘ │
└─────────────┘     └──────────────────────────────┘

```



---

## 🧠 Lógica de IA Híbrida (Fallback)

Para garantizar la disponibilidad en entornos con conectividad inestable (común en zonas rurales o ambulatorios populares), OpenS implementa una transición transparente entre la nube y modelos locales.

**Flujo de decisión:**

1. 
**Motor Cloud:** Utiliza **Google Gemini 2.5 Flash** para análisis complejos y alta velocidad.


2. 
**Motor Edge/Local:** Si la API Key no está configurada o hay un error de red, el sistema activa una cadena de modelos locales vía **Ollama**.


3. 
**Modelos Locales:** Se prueban en secuencia (**Qwen2.5, Kimi-k2, Llama3.2, Mistral**, etc.) hasta que uno responda con éxito.



---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Descripción |
| --- | --- | --- |
| **Frontend** | Astro 6 & Tailwind CSS 4 | Interfaz rápida y optimizada como PWA.

 |
| **Backend** | FastAPI (Python 3.11) | Centro de inteligencia y procesamiento de datos.

 |
| **IA Cloud** | Google Gemini 2.5 Flash | Motor principal de generación de lenguaje.

 |
| **IA Local** | Ollama (Qwen, Llama, etc.) | Respaldo para funcionamiento offline.

 |
| **Base de Datos** | Supabase (PostgreSQL) | Archivo digital seguro de memorias clínicas.

 |
| **Voz** | ElevenLabs | Accesibilidad mediante síntesis de voz hiperrealista.

 |

---

## 🚀 Endpoints Principales

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/health` | Estado detallado (IA y DB configuradas).

 |
| `GET` | `/api/v1/patients` | Lista de pacientes desde Supabase.
 
 |
| `POST` | `/api/v1/assistant/ask` | Consulta principal al asistente médico.

 |
| `POST` | `/api/v1/assistant/seal_record` | Sella diagnóstico en Solana y persiste metadata.
 
 |
| `POST` | `/api/v1/assistant/tts` | Generación de audio (alias de voz).
 
 |
| `POST` | `/api/v1/voice/generate` | Generación de audio con ElevenLabs.

 |
| `GET` | `/api/v1/patients/{id}/records` | Recuperación de historial clínico de Supabase.

 |

---

## 🆕 Mejoras recientes (mayo 2026)

* 
**Integración real Frontend ↔ Backend:** `patientService.js` ahora consume pacientes e historiales desde FastAPI/Supabase (sin datos mock).


* 
**Trazabilidad del motor de IA:** `POST /api/v1/assistant/ask` devuelve `engine_used` para identificar si la respuesta vino de Gemini, Ollama o fallback.


* 
**Mayor compatibilidad de respuestas:** la UI de pacientes soporta payloads en formato lista directa y en formato `{ patients }` / `{ records }`.


* 
**Persistencia clínica más completa:** al finalizar consulta se envía también metadata útil (`hash` y firma frontend) dentro de `notes`.

## 🔒 Seguridad y Ética

* 
**Prompt Estricto:** La IA tiene prohibido inventar datos o dar consejos médicos fuera del historial suministrado.


* 
**Privacidad:** Uso de modelos locales para datos extremadamente sensibles que no deben salir de la infraestructura local.


* 
**Gestión de Secretos:** Las claves de API (Google/Supabase) se gestionan mediante variables de entorno y no se incluyen en el código.





**Desarrollado para la Hackathon Dev3pack.**
