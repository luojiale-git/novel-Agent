use std::sync::Mutex;

static BACKEND_PORT: Mutex<u16> = Mutex::new(8100);

#[tauri::command]
fn get_backend_port() -> u16 {
    *BACKEND_PORT.lock().unwrap()
}

#[tauri::command]
fn get_backend_status() -> String {
    match std::net::TcpStream::connect(format!("127.0.0.1:{}", *BACKEND_PORT.lock().unwrap())) {
        Ok(_) => "running".to_string(),
        Err(_) => "stopped".to_string(),
    }
}
