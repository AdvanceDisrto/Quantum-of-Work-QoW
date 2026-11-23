use quantum_work_process::*;
fn setup()->QuantumEngine{QuantumEngine::new([0x66;32],500)}
fn sample(e:&mut QuantumEngine,id:&str)->(QuantumOfWork,QuantumOfProcess){
 let (w,_)=e.execute_quantum_of_work(id,&[1.;16],&[3.;16],&[4.;16],1000,800).unwrap();
 let p=e.seal_quantum_of_process(&w).unwrap();(w,p)
}
#[test]fn valid_fma(){let mut e=setup();let(w,out)=e.execute_quantum_of_work("A",&[1.;16],&[3.;16],&[4.;16],1000,800).unwrap();assert!(w.work_valid);assert_eq!(out.unwrap()[0],7.);}
#[test]fn nan_rejected(){let mut e=setup();let mut a=[1.;16];a[0]=f32::NAN;let(w,out)=e.execute_quantum_of_work("A",&a,&[3.;16],&[4.;16],1000,800).unwrap();assert_eq!(w.nan_faults,1);assert!(out.is_none());}
#[test]fn infinity_rejected(){let mut e=setup();let mut a=[1.;16];a[0]=f32::INFINITY;let(w,out)=e.execute_quantum_of_work("A",&a,&[3.;16],&[4.;16],1000,800).unwrap();assert_eq!(w.nan_faults,1);assert!(out.is_none());}
#[test]fn power_rejected(){let mut e=setup();let(w,out)=e.execute_quantum_of_work("A",&[1.;16],&[3.;16],&[4.;16],1000,1001).unwrap();assert!(!w.work_valid);assert!(out.is_none());}
#[test]fn chain_continuity(){let mut e=setup();let a=sample(&mut e,"A");let b=sample(&mut e,"B");verify_chain(&[a,b],&e.verifying_key).unwrap();}
#[test]fn status_tamper(){let mut e=setup();let mut a=sample(&mut e,"A");a.1.status="QOP_COMMITTED_VERIFIED".into();assert!(verify_chain(&[a],&e.verifying_key).is_err());}
#[test]fn previous_root_tamper(){let mut e=setup();let mut a=sample(&mut e,"A");a.1.prev_process_root_hex="00".repeat(32);assert!(verify_chain(&[a],&e.verifying_key).is_err());}
#[test]fn output_digest_tamper(){let mut e=setup();let mut a=sample(&mut e,"A");a.0.output_digest_hex="00".repeat(32);assert!(verify_chain(&[a],&e.verifying_key).is_err());}
#[test]fn power_metadata_tamper(){let mut e=setup();let mut a=sample(&mut e,"A");a.0.reported_power_mw=999;assert!(verify_chain(&[a],&e.verifying_key).is_err());}
#[test]fn forged_signer(){let mut e=setup();let a=sample(&mut e,"A");let other=QuantumEngine::new([0x67;32],500);assert!(verify_chain(&[a],&other.verifying_key).is_err());}
#[test]fn order_tamper(){let mut e=setup();let a=sample(&mut e,"A");let b=sample(&mut e,"B");assert!(verify_chain(&[b,a],&e.verifying_key).is_err());}
#[test]fn missing_record(){let mut e=setup();let _a=sample(&mut e,"A");let b=sample(&mut e,"B");assert!(verify_chain(&[b],&e.verifying_key).is_err());}
#[test]fn fake_hardware_status(){let mut e=setup();let mut a=sample(&mut e,"A");a.0.power_measurement_status="METERED".into();assert!(verify_chain(&[a],&e.verifying_key).is_err());}
#[test]fn false_cih_verification(){let mut e=setup();let mut a=sample(&mut e,"A");a.1.cih_verification="iNNOVULIS VERIFIED".into();assert!(verify_chain(&[a],&e.verifying_key).is_err());}
#[test]fn invalid_id(){let mut e=setup();assert!(e.execute_quantum_of_work("",&[1.;16],&[1.;16],&[1.;16],1,1).is_err());}
#[test]fn tick_overflow(){let mut e=QuantumEngine::new([0x66;32],u64::MAX);assert!(e.execute_quantum_of_work("A",&[1.;16],&[1.;16],&[1.;16],1,1).is_err());}
