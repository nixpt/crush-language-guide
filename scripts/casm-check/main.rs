//! Helper for scripts/check-examples.py: runs the JSON forms the guide documents.
//!
//!   casm-check casm FILE     JSON CASM  -> Program::deserialize (version gate) -> CVM1 -> run
//!   casm-check cast FILE     JSON CAST  -> validate_json -> compile -> CVM1 -> run
//!   casm-check castvalidate FILE  JSON CAST -> validate_json -> compile -> lower (no run)
//!   casm-check castload FILE JSON CAST  -> Program::deserialize (the version-gated loader) only
//!   casm-check emit FILE     Crush source -> JSON CASM on stdout
//!   casm-check emit-cast FILE Crush source -> JSON CAST on stdout
//!   casm-check casmb FILE    JSON CASM -> binary (.casmb) -> deserialize again
//!   casm-check asm-ai FILE   CVM1 text assembly, run with the ai_native.* stub gates enabled
use crush_lang_sdk::compile::{casm_to_vm, compile_crush_to_casm, prepare_polyglot_blocks};
use crush_lang_sdk::{HostCapsBuilder, Runtime};

fn main() -> anyhow::Result<()> {
    let a: Vec<String> = std::env::args().collect();
    anyhow::ensure!(a.len() == 3, "usage: casm-check <casm|cast|castvalidate|castload|casmb|emit|emit-cast|asm-ai> FILE");
    let data = std::fs::read(&a[2])?;
    let text = || String::from_utf8(data.clone());
    match a[1].as_str() {
        "casm" => {
            let p = casm::Program::deserialize(&data, casm::Format::Json)?;
            print!("{}", Runtime::new().run(&casm_to_vm(&p)?)?.output);
        }
        "cast" => {
            let s = text()?;
            if let Err(errs) = crush_cast::validate_json(&s) {
                anyhow::bail!("invalid CAST: {errs:?}");
            }
            let p: crush_cast::Program = serde_json::from_str(&s)?;
            let c = crush_frontend::compile_cast_owned(p)?;
            print!("{}", Runtime::new().run(&casm_to_vm(&c)?)?.output);
        }
        "castvalidate" => {
            let s = text()?;
            if let Err(errs) = crush_cast::validate_json(&s) {
                anyhow::bail!("invalid CAST: {errs:?}");
            }
            let p: crush_cast::Program = serde_json::from_str(&s)?;
            casm_to_vm(&crush_frontend::compile_cast_owned(p)?)?;
            println!("valid, compiles, lowers");
        }
        "castload" => {
            let p = crush_cast::Program::deserialize(&data, crush_cast::Format::Json)?;
            println!("loaded cast_version {}", p.cast_version);
        }
        "emit" => {
            let p = compile_crush_to_casm(&text()?)?;
            println!("{}", String::from_utf8(p.serialize(casm::Format::Json)?)?);
        }
        "emit-cast" => {
            let mut p = crush_frontend::parse_source(&text()?)?;
            prepare_polyglot_blocks(&mut p);
            println!("{}", serde_json::to_string_pretty(&p)?);
        }
        "casmb" => {
            let p = casm::Program::deserialize(&data, casm::Format::Json)?;
            let bytes = p.serialize(casm::Format::Binary)?;
            let q = casm::Program::deserialize(&bytes, casm::Format::Binary)?;
            println!("round-tripped {} functions", q.functions.len());
        }
        "asm-ai" => {
            let caps = HostCapsBuilder::new().ai_native(true).build();
            let p = crush_lang_sdk::assemble(&text()?, Some(&["io.print"]), None)?;
            print!("{}", Runtime::new().with_host_caps(caps).run(&p)?.output);
        }
        other => anyhow::bail!("unknown command {other}"),
    }
    Ok(())
}
