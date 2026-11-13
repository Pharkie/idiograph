//! The window's key (agentlock, 2 November 2026). What governs agents, a project's tick for agents, the list of
//! names to replace and the agents' setting up, is answered by the server only with a key made at each start, so
//! that no other program on this machine, a shell's curl among them, can act for him. The window makes it here from the system's own random source, hands
//! it to the server it starts on the server's standard input (main.rs `start_server`), a pipe no other
//! program reads, and to its page in the script every window runs before the page's own (`window_script`).
//! It is never in an argument, an environment variable, a file or the log.

use std::sync::OnceLock;

static KEY: OnceLock<String> = OnceLock::new();

/// The environment variable that tells the server its key is on its standard input. It never holds the key.
pub const FROM: &str = "IDIOGRAPH_WINDOW_KEY";

/// This start's key, 64 hex characters from 32 random bytes, made once.
pub fn key() -> &'static str {
    KEY.get_or_init(|| {
        let mut bytes = [0u8; 32];
        fill(&mut bytes);
        bytes.iter().map(|b| format!("{b:02x}")).collect()
    })
}

/// 32 bytes from the system's own random source: /dev/urandom on a Mac and Linux.
#[cfg(unix)]
fn fill(bytes: &mut [u8; 32]) {
    use std::io::Read;
    let read = std::fs::File::open("/dev/urandom").and_then(|mut f| f.read_exact(bytes));
    if read.is_err() {
        // a system with no /dev/urandom has no window either, but the app never starts keyless
        mixed(bytes);
    }
}

/// 32 bytes from the system's own random source: BCryptGenRandom on Windows, the system's preferred one.
#[cfg(windows)]
fn fill(bytes: &mut [u8; 32]) {
    #[link(name = "bcrypt")]
    extern "system" {
        fn BCryptGenRandom(algorithm: *mut core::ffi::c_void, buffer: *mut u8, count: u32, flags: u32) -> i32;
    }
    const BCRYPT_USE_SYSTEM_PREFERRED_RNG: u32 = 2;
    let status = unsafe {
        BCryptGenRandom(std::ptr::null_mut(), bytes.as_mut_ptr(), bytes.len() as u32, BCRYPT_USE_SYSTEM_PREFERRED_RNG)
    };
    if status != 0 {
        mixed(bytes);
    }
}

#[cfg(not(any(unix, windows)))]
fn fill(bytes: &mut [u8; 32]) {
    mixed(bytes);
}

/// The standard library's own random keys, which it takes from the system, when the system's source
/// cannot be read.
#[allow(dead_code)]
fn mixed(bytes: &mut [u8; 32]) {
    use std::collections::hash_map::RandomState;
    use std::hash::{BuildHasher, Hasher};
    for (i, chunk) in bytes.chunks_mut(8).enumerate() {
        let mut h = RandomState::new().build_hasher();
        h.write_usize(i);
        h.write_u128(std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_nanos()).unwrap_or(0));
        chunk.copy_from_slice(&h.finish().to_le_bytes()[..chunk.len()]);
    }
}
