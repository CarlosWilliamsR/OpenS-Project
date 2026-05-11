const envBase = import.meta.env.PUBLIC_BACKEND_URL || '';

function normalizeApiBase(base) {
  if (!base) return null;
  const sanitized = String(base).replace(/\/+$/, '');
  return sanitized.endsWith('/api/v1') ? sanitized : `${sanitized}/api/v1`;
}

const API_BASES = [
  normalizeApiBase(envBase),
  '/api/v1',
  'http://localhost:8000/api/v1',
  'http://localhost:8001/api/v1'
].filter((value, index, list) => Boolean(value) && list.indexOf(value) === index);

async function fetchAny(path, options = {}) {
  let lastError = null;
  for (const base of API_BASES) {
    try {
      const response = await fetch(`${base}${path}`, options);
      if (!response.ok) {
        lastError = new Error(`Backend error ${response.status} on ${base}${path}`);
        continue;
      }
      return response;
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') throw error;
      lastError = error;
    }
  }
  throw lastError || new Error(`No backend available for ${path}`);
}

async function fetchJson(path, options = {}) {
  const response = await fetchAny(path, options);
  return response.json();
}

function normalizePatients(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.patients)) return payload.patients;
  return [];
}

function normalizeRecords(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.records)) return payload.records;
  return [];
}

export default {
  async searchPatients(query = '', options = {}) {
    const payload = await fetchJson('/patients', { signal: options.signal });
    const patients = normalizePatients(payload);
    const normalizedQuery = String(query || '').trim().toLowerCase();
    if (!normalizedQuery) return patients;
    return patients.filter((patient) => {
      const byName = String(patient?.name || '').toLowerCase().includes(normalizedQuery);
      const byId = String(patient?.id || '') === normalizedQuery;
      return byName || byId;
    });
  },

  async getPatient(id, options = {}) {
    const patients = await this.searchPatients('', options);
    const found = patients.find((patient) => String(patient?.id) === String(id));
    return found || { id, name: `Paciente ${id}` };
  },

  async getPatientRecords(patientId, options = {}) {
    const payload = await fetchJson(`/patients/${patientId}/records`, { signal: options.signal });
    return normalizeRecords(payload);
  },

  async askAssistant(patientId, prompt_text, model_preference = 'gemini') {
    const data = await fetchJson('/assistant/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_id: Number(patientId), prompt_text, model_preference })
    });
    if (!data.engine_used) {
      data.engine_used = 'fallback';
    }
    return data;
  },

  async synthesizeVoice(text) {
    const response = await fetchAny('/assistant/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    return response.blob();
  },

  async generateDraftDiagnosis(patientId, conversation, doctorNotes, model) {
    const prompt = `Conversation:\n${JSON.stringify(conversation)}\nDoctor Notes:\n${doctorNotes}\nGenerate a professional medical diagnosis summary in Spanish.`;
    const res = await this.askAssistant(patientId, prompt, model);
    return { draft_diagnosis: res.response };
  },

  async finalizeConsultation(patientId, diagnosis, hash, txSignature, reason) {
    const notes = [reason, hash && `hash:${hash}`, txSignature && `frontend_tx:${txSignature}`]
      .filter(Boolean)
      .join(' | ');
    return fetchJson('/assistant/seal_record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_id: Number(patientId), diagnosis_text: diagnosis, notes })
    });
  }
};
