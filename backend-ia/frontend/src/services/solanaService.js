export async function hashDiagnosis(text) {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
}

export async function anchorOnChain(hash, patientId, setStatusLabel) {
  setStatusLabel('Simulando firma de transacción en Solana...');
  // In a real frontend, we could use Phantom or Burner wallet here,
  // but the backend takes care of the actual Anchor submission in `seal_record`.
  // So here we just pass through or simulate the wait.
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ txSignature: 'sim_tx_sig_' + Math.random().toString(36).substring(7) });
    }, 1500);
  });
}
