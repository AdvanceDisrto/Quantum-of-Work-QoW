use blake3::Hasher;
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
pub const PENDING: &str = "PENDING PROOF OF PROCESS — CIH VERIFICATION";
pub const GENESIS: &[u8] = b"iNNOVULIS/QoW-QoP/genesis/v2";
fn digest(b:&[u8])->[u8;32]{*blake3::hash(b).as_bytes()}
fn decode32(s:&str)->Result<[u8;32],String>{
    hex::decode(s).map_err(|_|"bad hex".to_string())?.try_into().map_err(|_|"bad digest size".to_string())
}
#[derive(Debug,Clone,Serialize,Deserialize)]
pub struct QuantumOfWork {
    pub work_id:String, pub lane_count:u32, pub ops_executed:u64,
    pub power_budget_mw:u32, pub reported_power_mw:u32,
    pub power_measurement_status:String, pub nan_faults:u32,
    pub input_digest_hex:String, pub output_digest_hex:String,
    pub qow_digest_hex:String, pub work_valid:bool, pub rejection_reason:String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
pub struct QuantumOfProcess {
    pub process_seq:u64, pub chronos_start_tick:u64, pub chronos_end_tick:u64,
    pub bound_qow_digest_hex:String, pub prev_process_root_hex:String,
    pub next_process_root_hex:String, pub status:String,
    pub cih_verification:String, pub signer_pubkey_hex:String, pub signature_hex:String,
}
fn qow_payload(w:&QuantumOfWork)->Vec<u8>{
    let mut b=Vec::new();b.extend_from_slice(b"iNNOVULIS/QoW/v2\0");
    b.extend_from_slice(&(w.work_id.len() as u32).to_le_bytes());b.extend_from_slice(w.work_id.as_bytes());
    b.extend_from_slice(&w.lane_count.to_le_bytes());b.extend_from_slice(&w.ops_executed.to_le_bytes());
    b.extend_from_slice(&w.power_budget_mw.to_le_bytes());b.extend_from_slice(&w.reported_power_mw.to_le_bytes());
    for s in [&w.power_measurement_status,&w.input_digest_hex,&w.output_digest_hex,&w.rejection_reason]{
        b.extend_from_slice(&(s.len() as u32).to_le_bytes());b.extend_from_slice(s.as_bytes());
    }
    b.extend_from_slice(&w.nan_faults.to_le_bytes());b.push(u8::from(w.work_valid));b
}
pub fn verify_qow(w:&QuantumOfWork)->Result<(),String>{
    if w.work_id.is_empty()||w.work_id.len()>128||w.lane_count!=16||w.ops_executed!=32{
        return Err("invalid QoW metadata".into());
    }
    decode32(&w.input_digest_hex)?;decode32(&w.output_digest_hex)?;
    let expected_valid=w.nan_faults==0 && w.reported_power_mw<=w.power_budget_mw;
    if w.work_valid!=expected_valid || w.power_measurement_status!="SIMULATED_UNVERIFIED" {
        return Err("QoW invariant or provenance mismatch".into());
    }
    if (w.work_valid && !w.rejection_reason.is_empty()) ||
        (!w.work_valid && w.rejection_reason!="QOW_INVARIANT_VIOLATION"){
        return Err("QoW rejection status mismatch".into());
    }
    if w.qow_digest_hex!=hex::encode(digest(&qow_payload(w))){return Err("QoW digest mismatch".into());}
    Ok(())
}
fn transition(prev:&[u8;32],p:&QuantumOfProcess,qow:&[u8;32])->[u8;32]{
    let mut h=Hasher::new();
    h.update(b"iNNOVULIS/QoP/transition/v2\0");
    h.update(prev);h.update(&p.process_seq.to_le_bytes());
    h.update(&p.chronos_start_tick.to_le_bytes());h.update(&p.chronos_end_tick.to_le_bytes());
    h.update(qow);h.update(p.status.as_bytes());*h.finalize().as_bytes()
}
fn signed_bytes(p:&QuantumOfProcess)->Vec<u8>{
    let mut b=Vec::new();b.extend_from_slice(b"iNNOVULIS/QoP/sign/v2\0");
    for s in [&p.bound_qow_digest_hex,&p.prev_process_root_hex,&p.next_process_root_hex,
        &p.status,&p.cih_verification,&p.signer_pubkey_hex]{
        b.extend_from_slice(&(s.len() as u32).to_le_bytes());b.extend_from_slice(s.as_bytes());
    }
    b.extend_from_slice(&p.process_seq.to_le_bytes());
    b.extend_from_slice(&p.chronos_start_tick.to_le_bytes());b.extend_from_slice(&p.chronos_end_tick.to_le_bytes());b
}
pub struct QuantumEngine {
    signing_key:SigningKey,pub verifying_key:VerifyingKey,pub chronos_tick:u64,
    pub process_seq:u64,pub process_chain_root:[u8;32],
}
impl QuantumEngine {
    pub fn new(seed:[u8;32],initial_tick:u64)->Self{
        let signing_key=SigningKey::from_bytes(&seed);
        let verifying_key=signing_key.verifying_key();
        Self{signing_key,verifying_key,chronos_tick:initial_tick,process_seq:0,
            process_chain_root:digest(GENESIS)}
    }
    pub fn execute_quantum_of_work(&mut self,id:&str,a:&[f32;16],b:&[f32;16],c:&[f32;16],
        budget:u32,reported_power:u32)->Result<(QuantumOfWork,Option<[f32;16]>),String>{
        if id.is_empty()||id.len()>128 {return Err("invalid work id".into());}
        self.chronos_tick=self.chronos_tick.checked_add(1).ok_or("tick overflow")?;
        let mut input=Hasher::new();
        for i in 0..16{input.update(&a[i].to_le_bytes());input.update(&b[i].to_le_bytes());input.update(&c[i].to_le_bytes());}
        let out=std::array::from_fn(|i|a[i].mul_add(b[i],c[i]));
        let faults=out.iter().filter(|v|!v.is_finite()).count() as u32;
        let mut output=Hasher::new();for v in &out{output.update(&v.to_le_bytes());}
        let valid=faults==0 && reported_power<=budget;
        let mut w=QuantumOfWork{work_id:id.into(),lane_count:16,ops_executed:32,
            power_budget_mw:budget,reported_power_mw:reported_power,
            power_measurement_status:"SIMULATED_UNVERIFIED".into(),nan_faults:faults,
            input_digest_hex:hex::encode(input.finalize().as_bytes()),
            output_digest_hex:hex::encode(output.finalize().as_bytes()),
            qow_digest_hex:String::new(),work_valid:valid,
            rejection_reason:if valid{String::new()}else{"QOW_INVARIANT_VIOLATION".into()}};
        w.qow_digest_hex=hex::encode(digest(&qow_payload(&w)));
        Ok((w,if valid{Some(out)}else{None}))
    }
    pub fn seal_quantum_of_process(&mut self,w:&QuantumOfWork)->Result<QuantumOfProcess,String>{
        verify_qow(w)?;
        let seq=self.process_seq.checked_add(1).ok_or("sequence overflow")?;
        let start=self.chronos_tick;
        let end=start.checked_add(1).ok_or("tick overflow")?;
        let mut p=QuantumOfProcess{
            process_seq:seq,chronos_start_tick:start,chronos_end_tick:end,
            bound_qow_digest_hex:w.qow_digest_hex.clone(),
            prev_process_root_hex:hex::encode(self.process_chain_root),
            next_process_root_hex:String::new(),
            status:if w.work_valid{"QOP_COMMITTED_SOFTWARE_CHECKED".into()}else{"QOP_SEALED_NEGATIVE_REJECT".into()},
            cih_verification:PENDING.into(),signer_pubkey_hex:hex::encode(self.verifying_key.to_bytes()),
            signature_hex:String::new()};
        let next=transition(&self.process_chain_root,&p,&decode32(&p.bound_qow_digest_hex)?);
        p.next_process_root_hex=hex::encode(next);
        p.signature_hex=hex::encode(self.signing_key.sign(&signed_bytes(&p)).to_bytes());
        self.process_seq=seq;self.chronos_tick=end;self.process_chain_root=next;
        Ok(p)
    }
}
pub fn verify_chain(records:&[(QuantumOfWork,QuantumOfProcess)],trusted:&VerifyingKey)->Result<(),String>{
    if records.is_empty(){return Err("empty chain".into());}
    let mut prev=digest(GENESIS);
    let mut last_tick=None;
    for (idx,(w,p)) in records.iter().enumerate(){
        verify_qow(w)?;
        if p.process_seq!=(idx as u64)+1 || p.bound_qow_digest_hex!=w.qow_digest_hex ||
            p.prev_process_root_hex!=hex::encode(prev) || p.cih_verification!=PENDING ||
            p.signer_pubkey_hex!=hex::encode(trusted.to_bytes()) ||
            p.chronos_end_tick<=p.chronos_start_tick ||
            last_tick.is_some_and(|t|p.chronos_start_tick<=t) {
            return Err("QOP_CHAIN_BREAK: metadata, order, trust or QoW binding".into());
        }
        let expected_status=if w.work_valid{"QOP_COMMITTED_SOFTWARE_CHECKED"}else{"QOP_SEALED_NEGATIVE_REJECT"};
        if p.status!=expected_status{return Err("QOP_CHAIN_BREAK: status".into());}
        let next=transition(&prev,p,&decode32(&p.bound_qow_digest_hex)?);
        if p.next_process_root_hex!=hex::encode(next){return Err("QOP_CHAIN_BREAK: root".into());}
        let sig=Signature::from_slice(&hex::decode(&p.signature_hex).map_err(|_|"bad signature hex")?)
            .map_err(|_|"bad signature")?;
        trusted.verify(&signed_bytes(p),&sig).map_err(|_|"QOP_CHAIN_BREAK: signature")?;
        prev=next;last_tick=Some(p.chronos_end_tick);
    }
    Ok(())
}
