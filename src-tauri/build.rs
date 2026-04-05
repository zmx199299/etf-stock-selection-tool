use std::env;
use std::fs;
use std::path::PathBuf;

fn ensure_sidecar_placeholder() {
    let manifest_dir =
        PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("missing CARGO_MANIFEST_DIR"));
    let target_triple = env::var("TAURI_ENV_TARGET_TRIPLE")
        .or_else(|_| env::var("TARGET"))
        .expect("missing target triple");

    let mut sidecar_path = manifest_dir
        .join("binaries")
        .join(format!("engine-{target_triple}"));

    if target_triple.contains("windows") {
        sidecar_path.set_extension("exe");
    }

    if sidecar_path.exists() {
        return;
    }

    if let Some(parent) = sidecar_path.parent() {
        fs::create_dir_all(parent).expect("failed to create sidecar directory");
    }

    fs::write(&sidecar_path, []).expect("failed to create sidecar placeholder");

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;

        let mut permissions = fs::metadata(&sidecar_path)
            .expect("failed to read sidecar metadata")
            .permissions();
        permissions.set_mode(0o755);
        fs::set_permissions(&sidecar_path, permissions).expect("failed to set sidecar permissions");
    }
}

fn main() {
    ensure_sidecar_placeholder();
    tauri_build::build()
}
