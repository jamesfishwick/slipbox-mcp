# Tauri Menu Bar App Implementation Plan

## Overview
Build a native macOS menu bar application using Tauri to provide GUI access to the Zettelkasten MCP server. The app will execute terminal commands from the existing `zk` CLI and display status in the menu bar.

## Goals
- Replace SwiftBar with a native, distributable solution
- Maintain current menu functionality
- Keep it simple: mostly command execution, minimal UI
- Ship-ready for paid distribution
- Cross-platform foundation (Mac first, Windows/Linux later)

---

## Phase 1: Setup & Scaffolding (Day 1 Morning)

### Prerequisites
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Tauri CLI
cargo install tauri-cli

# Install Node.js dependencies manager (if needed)
# You likely already have npm/pnpm/yarn
```

### Project Structure
```
zettelkasten-mcp/
├── menubar/                    # New Tauri app directory
│   ├── src-tauri/             # Rust backend
│   │   ├── src/
│   │   │   └── main.rs        # Menu logic, command execution
│   │   ├── icons/             # App icons
│   │   ├── Cargo.toml
│   │   └── tauri.conf.json    # Tauri configuration
│   ├── src/                   # Frontend (minimal HTML)
│   │   └── index.html         # Hidden window (required by Tauri)
│   ├── package.json
│   └── README.md
```

### Scaffold the Project
```bash
cd /Users/jamesfishwick/Workspace/zettelkasten-mcp
npm create tauri-app@latest menubar

# Choose:
# - Package manager: npm (or your preference)
# - UI template: Vanilla (we won't use it much)
# - TypeScript: No (keep it simple)
```

### Configure for Menu Bar App
Edit `menubar/src-tauri/tauri.conf.json`:
```json
{
  "build": {
    "beforeDevCommand": "",
    "beforeBuildCommand": "",
    "devPath": "../src",
    "distDir": "../src"
  },
  "tauri": {
    "systemTray": {
      "iconPath": "icons/tray-icon.png",
      "iconAsTemplate": true
    },
    "windows": []  // No main window - menu bar only
  }
}
```

**Deliverable:** Working Tauri scaffold that runs `cargo tauri dev` without errors

---

## Phase 2: Core Menu Implementation (Day 1 Afternoon)

### Menu Structure
Implement the menu from your screenshot:

```
⚠️ Server Crashed         (status indicator - dynamic)
⚡ Start Server
● View Status
📋 View Logs
🔄 Rebuild Index
---
📂 Open in Obsidian
📁 Open Notes Folder
---
⚙️ Settings >
    ✅ Enable Auto-Start
    🔴 Disable Auto-Start
🔧 SwiftBar >            (keep for migration, remove later)
---
Updated 1 Second Ago
🖥️ Run in Terminal...
🔌 Disable Plugin
ℹ️ About
```

### Implementation in `src-tauri/src/main.rs`

```rust
use tauri::{
    CustomMenuItem, SystemTray, SystemTrayMenu, SystemTrayEvent,
    Manager, SystemTrayMenuItem, SystemTraySubmenu, AppHandle, Icon
};
use std::process::Command;

fn main() {
    let tray_menu = create_menu();
    let tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .system_tray(tray)
        .on_system_tray_event(handle_tray_event)
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn create_menu() -> SystemTrayMenu {
    let status = CustomMenuItem::new("status_indicator", "⚙️ Server Status");
    let start = CustomMenuItem::new("start", "⚡ Start Server");
    let view_status = CustomMenuItem::new("view_status", "● View Status");
    let view_logs = CustomMenuItem::new("view_logs", "📋 View Logs");
    let rebuild = CustomMenuItem::new("rebuild", "🔄 Rebuild Index");
    let open_obsidian = CustomMenuItem::new("open_obsidian", "📂 Open in Obsidian");
    let open_folder = CustomMenuItem::new("open_folder", "📁 Open Notes Folder");
    
    let enable_auto = CustomMenuItem::new("enable_auto", "✅ Enable Auto-Start");
    let disable_auto = CustomMenuItem::new("disable_auto", "🔴 Disable Auto-Start");
    let settings_submenu = SystemTraySubmenu::new(
        "⚙️ Settings",
        SystemTrayMenu::new()
            .add_item(enable_auto)
            .add_item(disable_auto)
    );

    let about = CustomMenuItem::new("about", "ℹ️ About");
    let quit = CustomMenuItem::new("quit", "Quit Zettelkasten");

    SystemTrayMenu::new()
        .add_item(status.disabled()) // Status indicator only
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(start)
        .add_item(view_status)
        .add_item(view_logs)
        .add_item(rebuild)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(open_obsidian)
        .add_item(open_folder)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_submenu(settings_submenu)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(about)
        .add_item(quit)
}

fn handle_tray_event(app: &AppHandle, event: SystemTrayEvent) {
    match event {
        SystemTrayEvent::MenuItemClick { id, .. } => {
            match id.as_str() {
                "start" => run_command("zk", &["start"]),
                "view_status" => run_command("zk", &["status"]),
                "view_logs" => run_command("zk", &["logs"]),
                "rebuild" => run_command("zk", &["rebuild"]),
                "enable_auto" => run_command("zk", &["enable"]),
                "disable_auto" => run_command("zk", &["disable"]),
                "open_obsidian" => open_obsidian(),
                "open_folder" => open_notes_folder(),
                "about" => show_about(app),
                "quit" => std::process::exit(0),
                _ => {}
            }
        }
        _ => {}
    }
}

fn run_command(cmd: &str, args: &[&str]) {
    let output = Command::new(cmd)
        .args(args)
        .output();
    
    match output {
        Ok(output) => {
            if output.status.success() {
                show_notification("Success", &String::from_utf8_lossy(&output.stdout));
            } else {
                show_notification("Error", &String::from_utf8_lossy(&output.stderr));
            }
        }
        Err(e) => show_notification("Error", &format!("Failed to run command: {}", e))
    }
}

fn open_obsidian() {
    Command::new("open")
        .arg("-a")
        .arg("Obsidian")
        .arg("/path/to/notes") // Update with actual path
        .spawn()
        .ok();
}

fn open_notes_folder() {
    Command::new("open")
        .arg("/path/to/notes") // Update with actual path
        .spawn()
        .ok();
}

fn show_notification(title: &str, body: &str) {
    // macOS notification center
    Command::new("osascript")
        .arg("-e")
        .arg(format!(
            r#"display notification "{}" with title "Zettelkasten" subtitle "{}""#,
            body, title
        ))
        .spawn()
        .ok();
}

fn show_about(app: &AppHandle) {
    // Show simple about dialog
    // For now, just notification - can enhance later
    show_notification("About", "Zettelkasten MCP Server v1.0");
}
```

**Deliverable:** Working menu bar with all items that execute commands

---

## Phase 3: Dynamic Status Updates (Day 2 Morning)

### Server Status Monitoring
The menu needs to show real-time server status.

#### Option A: Polling (Simple)
```rust
use std::time::Duration;
use std::thread;

fn start_status_monitor(app_handle: AppHandle) {
    thread::spawn(move || {
        loop {
            thread::sleep(Duration::from_secs(5));
            let status = get_server_status();
            update_menu_status(&app_handle, &status);
        }
    });
}

fn get_server_status() -> String {
    let output = Command::new("zk")
        .arg("status")
        .output()
        .ok()?;
    
    if output.status.success() {
        "✅ Server Running"
    } else {
        "⚠️ Server Stopped"
    }
}

fn update_menu_status(app: &AppHandle, status: &str) {
    app.tray_handle()
        .get_item("status_indicator")
        .set_title(status)
        .ok();
}
```

#### Option B: File Watching (Better)
Monitor the server's PID file or status file for changes.

```rust
use notify::{Watcher, RecursiveMode, Event};
use std::path::Path;

fn watch_status_file(app_handle: AppHandle) {
    let mut watcher = notify::recommended_watcher(move |res: Result<Event, _>| {
        if let Ok(event) = res {
            let status = get_server_status();
            update_menu_status(&app_handle, &status);
        }
    }).unwrap();

    watcher.watch(
        Path::new("/Users/jamesfishwick/.local/share/mcp/zettelkasten/status"),
        RecursiveMode::NonRecursive
    ).ok();
    
    // Keep watcher alive
    std::mem::forget(watcher);
}
```

**Start with Option A** (polling), upgrade to Option B if needed.

**Deliverable:** Menu status updates automatically

---

## Phase 4: Enhanced UX (Day 2 Afternoon)

### Icon States
Create different tray icons for different states:
- `tray-icon-running.png` - Green/normal
- `tray-icon-stopped.png` - Gray/dimmed  
- `tray-icon-error.png` - Red/warning

Update icon based on status:
```rust
fn update_tray_icon(app: &AppHandle, state: &str) {
    let icon_path = match state {
        "running" => "icons/tray-icon-running.png",
        "stopped" => "icons/tray-icon-stopped.png",
        _ => "icons/tray-icon-error.png",
    };
    
    let icon = Icon::File(icon_path.into());
    app.tray_handle().set_icon(icon).ok();
}
```

### Command Output Handling
For commands that produce output (view status, view logs), open Terminal:

```rust
fn view_status() {
    Command::new("osascript")
        .arg("-e")
        .arg(r#"tell application "Terminal"
            activate
            do script "zk status; read -p 'Press enter to close...'"
        end tell"#)
        .spawn()
        .ok();
}

fn view_logs() {
    Command::new("osascript")
        .arg("-e")
        .arg(r#"tell application "Terminal"
            activate
            do script "zk logs"
        end tell"#)
        .spawn()
        .ok();
}
```

### Configuration
Read paths from environment or config file instead of hardcoding:

```rust
use std::env;

fn get_notes_path() -> String {
    env::var("ZETTELKASTEN_NOTES_PATH")
        .unwrap_or_else(|_| "/Users/jamesfishwick/notes".to_string())
}
```

**Deliverable:** Polished UX with proper feedback

---

## Phase 5: Testing & Debugging (Day 3 Morning)

### Test Checklist
- [ ] All menu items respond correctly
- [ ] Commands execute with proper error handling
- [ ] Status updates work (both success and error states)
- [ ] Notifications appear and are informative
- [ ] Terminal opens for output-heavy commands
- [ ] Auto-start enable/disable works
- [ ] App survives server crashes gracefully
- [ ] App starts on login (if configured)
- [ ] Icon changes reflect status accurately

### Debug Mode
Add logging:
```rust
use log::{info, error};
use env_logger;

fn main() {
    env_logger::init();
    info!("Zettelkasten menu bar app starting");
    // ... rest of code
}

fn run_command(cmd: &str, args: &[&str]) {
    info!("Running command: {} {:?}", cmd, args);
    // ... rest of command execution
}
```

Run with: `RUST_LOG=info cargo tauri dev`

**Deliverable:** Stable, tested app ready for distribution

---

## Phase 6: Packaging & Distribution (Day 3 Afternoon)

### Build for Release
```bash
cd menubar
cargo tauri build
```

This produces:
- `src-tauri/target/release/bundle/macos/Zettelkasten.app`
- `src-tauri/target/release/bundle/dmg/Zettelkasten_1.0.0_x64.dmg`

### Code Signing (Required for Distribution)

1. **Get Apple Developer Account** ($99/year)

2. **Create certificates:**
```bash
# In Xcode > Preferences > Accounts > Manage Certificates
# Create "Developer ID Application" certificate
```

3. **Configure signing in `tauri.conf.json`:**
```json
{
  "tauri": {
    "bundle": {
      "identifier": "com.yourcompany.zettelkasten",
      "macOS": {
        "signingIdentity": "Developer ID Application: Your Name (TEAMID)",
        "entitlements": null,
        "exceptionDomain": null
      }
    }
  }
}
```

4. **Notarize the app:**
```bash
# After building
xcrun notarytool submit target/release/bundle/dmg/Zettelkasten_1.0.0_x64.dmg \
    --apple-id "your@email.com" \
    --team-id "TEAMID" \
    --password "app-specific-password"
```

### Auto-Updates (Optional - v2.0)
Tauri supports auto-updates via GitHub releases:
```json
{
  "tauri": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://github.com/yourusername/zettelkasten-mcp/releases/latest/download/latest.json"
      ]
    }
  }
}
```

**Deliverable:** Signed, notarized .dmg ready to distribute

---

## Phase 7: Integration & Migration (Day 4)

### Bundle with MCP Server
Options:

**Option A: Separate installs**
- User installs Python server separately
- Menu bar app assumes server is installed

**Option B: Bundle everything**
- Include Python runtime + MCP server in .app
- Self-contained distribution

For Option B:
```
Zettelkasten.app/
└── Contents/
    ├── MacOS/
    │   └── zettelkasten-menubar    # Tauri binary
    └── Resources/
        ├── server/                  # Python server
        │   ├── .venv/
        │   └── src/
        └── zk                       # CLI script
```

### Migration Path from SwiftBar
1. Keep SwiftBar plugin functional during transition
2. Add detection: "Native app available - switch?"
3. Instructions in README for migration
4. Deprecate SwiftBar plugin in v2.0

**Deliverable:** Complete distribution package

---

## Timeline Summary

| Day | Phase | Hours | Deliverable |
|-----|-------|-------|-------------|
| 1 AM | Setup & Scaffolding | 2-3 | Working Tauri project |
| 1 PM | Core Menu | 3-4 | All menu items functional |
| 2 AM | Status Updates | 2-3 | Dynamic status indicator |
| 2 PM | Enhanced UX | 2-3 | Polished interactions |
| 3 AM | Testing | 2-3 | Production-ready code |
| 3 PM | Packaging | 2-3 | Signed .dmg |
| 4 | Integration | 3-4 | Complete distribution |

**Total: ~3-4 days of focused work**

---

## Future Enhancements (v2.0+)

### Features to Consider
- **Settings window** (instead of just menu items)
  - Configure notes path
  - Set update frequency
  - Customize keyboard shortcuts
- **Dashboard window** 
  - Note count, recent notes
  - Graph visualization (if useful)
- **Auto-updates** via Tauri updater
- **Keyboard shortcuts** (global hotkeys)
- **Windows/Linux builds** (minimal additional work)

### Architecture Improvements
- Move from command execution to **direct Rust integration** with server
- Replace shell commands with **IPC** between menu and server
- **Shared state management** instead of file polling

---

## Resources

### Tauri Documentation
- [System Tray Guide](https://tauri.app/v1/guides/features/system-tray)
- [Command & Shell](https://tauri.app/v1/guides/features/command)
- [Bundle & Distribution](https://tauri.app/v1/guides/distribution/overview)

### Examples
- [Tauri System Tray Example](https://github.com/tauri-apps/tauri/tree/dev/examples/system-tray)
- [Menu Bar Apps in Tauri](https://github.com/search?q=tauri+menu+bar)

### Tools
- [create-tauri-app](https://github.com/tauri-apps/create-tauri-app)
- [tauri-plugin-notification](https://github.com/tauri-apps/tauri-plugin-notification)
- [cargo-bundle](https://github.com/burtonageo/cargo-bundle) (included in Tauri)

---

## Success Criteria

✅ **MVP Complete When:**
- Menu bar icon shows correct status
- All commands execute reliably
- Notifications provide clear feedback
- App survives server restarts/crashes
- Builds into distributable .dmg

✅ **Ship-Ready When:**
- Code signed and notarized
- Tested on fresh Mac (no dev environment)
- Documentation complete
- Migration path from SwiftBar clear
- Ready to charge money for it

---

## Next Steps

1. **Commit this plan:** `git add docs/TAURI_MENU_BAR_PLAN.md && git commit`
2. **Block calendar:** 4 focused days for implementation
3. **Start Phase 1:** Run through setup checklist
4. **Ship it:** Don't let perfect be enemy of good—iterate after v1.0

Let's build this.
