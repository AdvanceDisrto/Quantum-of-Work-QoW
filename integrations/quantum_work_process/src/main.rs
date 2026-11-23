use quantum_work_process::*;
use serde::{Deserialize,Serialize};
use std::{env,fs};
#[derive(Serialize,Deserialize)]
struct Record{qow:QuantumOfWork,qop:QuantumOfProcess}
fn run()->Result<(),Box<dyn std::error::Error>>{
 let args:Vec<String>=env::args().collect();
 if args.len()!=1 && args.get(1).map(String::as_str)!=Some("self-test"){return Err("usage: quantum_work_process [self-test]".into());}
 // Fixed test key is a PUBLIC TEST FIXTURE, not a deployable root.
 let mut e=QuantumEngine::new([0x33;32],1_000_000);
 let a=std::array::from_fn(|i|(i+1) as f32);
 let b=[2.0;16];let c=[10.0;16];
 let (w1,out)=e.execute_quantum_of_work("VALID_FMA16",&a,&b,&c,1500,1424)?;
 let out=out.ok_or("valid output missing")?;
 assert_eq!(out[0],12.0);assert_eq!(out[15],42.0);
 let p1=e.seal_quantum_of_process(&w1)?;
 let mut nan=a;nan[0]=f32::NAN;
 let (w2,out2)=e.execute_quantum_of_work("NAN_REJECT",&nan,&b,&c,1500,1424)?;
 assert!(!w2.work_valid && out2.is_none() && w2.nan_faults==1);
 let p2=e.seal_quantum_of_process(&w2)?;
 let (w3,out3)=e.execute_quantum_of_work("POWER_REJECT",&a,&b,&c,1500,1527)?;
 assert!(!w3.work_valid && out3.is_none());
 let p3=e.seal_quantum_of_process(&w3)?;
 let records=vec![(w1,p1),(w2,p2),(w3,p3)];
 verify_chain(&records,&e.verifying_key)?;
 let mut forged=records.clone();forged[0].1.status="QOP_FORGED_OVERRIDE".into();
 assert!(verify_chain(&forged,&e.verifying_key).is_err());
 fs::create_dir_all("build_qow_qop")?;
 let bundle=serde_json::json!({"status":PENDING,"power_provenance":"SIMULATED_UNVERIFIED",
 "signer_pubkey_hex":hex::encode(e.verifying_key.to_bytes()),
 "final_process_chain_root":hex::encode(e.process_chain_root),
 "records":records.iter().map(|(qow,qop)|serde_json::json!({"qow":qow,"qop":qop})).collect::<Vec<_>>()});
 fs::write("build_qow_qop/qow_qop_pending_chain.json",serde_json::to_vec_pretty(&bundle)?)?;
 println!("PASS QoW valid FMA16; NaN rejection; reported-power breach rejection");
 println!("PASS QoP three signed transitions; forged status rejected");
 println!("{}",PENDING);
 Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("ERROR: {e}");std::process::exit(1);}}
