const API_BASE = import.meta.env.PUBLIC_BACKEND_URL || 'http://localhost:8000/api/v1';

export default {
  async searchPatients(query, options = {}) {
    try {
      const res = await fetch(`${API_BASE}/patients`, options);
      if (!res.ok) throw new Error('Failed to fetch patients');
      const data = await res.json();
      if (!query) return data;
      return data.filter(p => p.name.toLowerCase().includes(query.toLowerCase()) || String(p.id) === query);
    } catch (err) {
      console.error(err);
      return [];
    }
  },

  async getPatient(id) {
    try {
      const patients = await this.searchPatients('');
      return patients.find(p => String(p.id) === String(id)) || null;
    } catch {
      return null;
    }
  },

  async getPatientRecords(patientId) {
    try {
      const res = await fetch(`${API_BASE}/patients/${patientId}/records`);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async askAssistant(patientId, prompt_text, model_preference = 'gemini') {
    const res = await fetch(`${API_BASE}/assistant/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_id: String(patientId), prompt_text })
    });
    if (!res.ok) throw new Error('AI backend error');
    return await res.json();
  },

  async synthesizeVoice(text) {
    const res = await fetch(`${API_BASE}/assistant/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error('TTS error');
    return await res.blob();
  },

  async generateDraftDiagnosis(patientId, conversation, doctorNotes, model) {
    const prompt = `Conversation:\n${JSON.stringify(conversation)}\nDoctor Notes:\n${doctorNotes}\nGenerate a professional medical diagnosis summary in Spanish.`;
    const res = await this.askAssistant(patientId, prompt, model);
    return { draft_diagnosis: res.response };
  },

  async finalizeConsultation(patientId, diagnosis, hash, txSignature, reason) {
    const res = await fetch(`${API_BASE}/assistant/seal_record`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_id: String(patientId), diagnosis_text: diagnosis, notes: reason })
    });
    if (!res.ok) throw new Error('Supabase Sync error');
    return await res.json();
  }
};
