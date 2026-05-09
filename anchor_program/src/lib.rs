use anchor_lang::prelude::*;

declare_id!("INSERT_PROGRAM_ID_HERE");

pub const SYSTEM_PROVIDER_PUBKEY: Pubkey = Pubkey::new_from_array([0u8; 32]);

#[program]
pub mod opens_anchor {
    use super::*;

    pub fn register_record(
        ctx: Context<RegisterRecord>,
        patient_id: [u8; 32],
        medical_hash: [u8; 32],
        timestamp: i64,
    ) -> Result<()> {
        let record = &mut ctx.accounts.record_account;
        let authority = &ctx.accounts.authority;

        if record.doctor_pubkey == Pubkey::default() {
            // First-time initialization: bind the doctor to the record.
            record.patient_id = patient_id;
            record.doctor_pubkey = authority.key();
        } else {
            let is_doctor = authority.key() == record.doctor_pubkey;
            let is_system_provider = authority.key() == SYSTEM_PROVIDER_PUBKEY;

            require!(is_doctor || is_system_provider, ErrorCode::Unauthorized);
            require!(record.patient_id == patient_id, ErrorCode::PatientIdMismatch);
        }

        record.medical_hash = medical_hash;
        record.timestamp = timestamp;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct RegisterRecord<'info> {
    #[account(
        init_if_needed,
        payer = authority,
        space = MedicalRecord::LEN,
        seeds = [b"record", patient_id.as_ref()],
        bump
    )]
    pub record_account: Account<'info, MedicalRecord>,

    #[account(mut)]
    pub authority: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[account]
pub struct MedicalRecord {
    pub patient_id: [u8; 32],
    pub medical_hash: [u8; 32],
    pub doctor_pubkey: Pubkey,
    pub timestamp: i64,
}

impl MedicalRecord {
    pub const LEN: usize = 8 + 32 + 32 + 32 + 8;
}

#[error_code]
pub enum ErrorCode {
    #[msg("Unauthorized authority to modify this record.")]
    Unauthorized,

    #[msg("Patient ID does not match the PDA seed.")]
    PatientIdMismatch,
}
