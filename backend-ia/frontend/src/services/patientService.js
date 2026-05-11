const API_BASE = import.meta.env.PUBLIC_BACKEND_URL || 'http://localhost:8000/api/v1';

export default {
  async searchPatients(query, options = {}) {
    // This would typically query Supabase via Backend or directly.
    // For resilience, if no backend, return local mock or fallback.
    return [
      { id: 1, name: "Carlos Williams", age: 45 },
      { id: 2, name: "Ana Martínez", age: 32 }
    ].filter(p => p.name.toLowerCase().includes(query.toLowerCase()) || String(p.id) === query);
  },

  async getPatient(id) {
    return { id, name: "Carlos Williams", age: 45 };
  },

  async getPatientRecords(patientId) {
    // Should fetch from backend Supabase endpoint
    return [];
  },

  async askAssistant(patientId, prompt_text, model_preference = 'gemini') {
    const res = await fetch(`${API_BASE}/assistant/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_id: patientId, prompt_text })
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
      body: JSON.stringify({ patient_id: patientId, diagnosis_text: diagnosis, notes: reason })
    });
    if (!res.ok) throw new Error('Supabase Sync error');
    return await res.json();
  }
};
