# 🌐 No-Guardrail AI Chromium Browser

## Overzicht

Custom Chromium-fork met ingebouwde AI-sidebar die rechtstreeks communiceert met je lokale Ollama/Dolphin no-guardrail stack.

## Features

✅ **Ingebouwde AI Sidebar** - Altijd toegankelijk via Cmd+Shift+A
✅ **Direct Ollama Connect** - Geen externe API's, 100% lokaal
✅ **Context-aware** - Huidige pagina automatisch in context
✅ **No Telemetry** - Alle Google tracking verwijderd
✅ **Privacy First** - Geen data naar externe servers
✅ **Coding Assistant** - Kilocode-integratie voor development

## Architectuur

```
Chromium Browser
├── AI Sidebar (React)
│   ├── Chat Interface
│   ├── Code Editor
│   └── Context Manager
├── Native Messaging Host
│   └── Ollama Connector (Python)
└── Modified Chromium Core
    ├── Removed Google Services
    ├── Added AI Keybindings
    └── Custom New Tab Page
```

## Build Instructies

### Prerequisites

```bash
# macOS
brew install python@3.11 nodejs ninja depot_tools

# Linux
sudo apt-get install python3 nodejs ninja-build
```

### 1. Clone Chromium Source

```bash
# Maak workspace
mkdir ~/chromium && cd ~/chromium

# Fetch Chromium (dit duurt lang, ~30GB)
fetch --nohooks chromium
cd src

# Checkout stable branch
git checkout -b no-guardrail-ai origin/main
```

### 2. Patch Chromium

```bash
# Kopieer patches
cp -r ~/no-guardrail-ai/chromium/patches .

# Apply patches
git am patches/*.patch
```

### 3. Build Configuration

Maak `out/Default/args.gn`:

```gn
# Build type
is_debug = false
is_official_build = true

# Target
target_cpu = "arm64"  # of "x64" voor Intel Mac
target_os = "mac"     # of "linux"

# Features
enable_nacl = false
enable_google_services = false
use_official_google_api_keys = false

# Privacy
safe_browsing_mode = 0
enable_reporting = false
enable_supervised_users = false

# Custom branding
chrome_pgo_phase = 0
is_component_build = false
```

### 4. Build

```bash
# Generate build files
gn gen out/Default

# Build (dit duurt uren)
autoninja -C out/Default chrome
```

### 5. AI Sidebar Integration

```bash
# Installeer sidebar dependencies
cd chrome/browser/resources/ai_sidebar
npm install
npm run build

# Build native messaging host
cd ../../../../chromium/native_host
pip install -r requirements.txt
pyinstaller --onefile ollama_host.py
```

## Installation

### macOS

```bash
# Kopieer binary
cp out/Default/Chromium.app /Applications/NoGuardrailAI.app

# Installeer native messaging host
cp chromium/native_host/dist/ollama_host \
   ~/Library/Application\ Support/NoGuardrailAI/

# Registreer manifest
mkdir -p ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts
cp chromium/native_host/com.noguardrail.ollama.json \
   ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/
```

### Linux

```bash
# Installeer binary
sudo cp out/Default/chrome /opt/no-guardrail-ai/
sudo ln -s /opt/no-guardrail-ai/chrome /usr/bin/no-guardrail-ai

# Native messaging
cp chromium/native_host/dist/ollama_host ~/.config/no-guardrail-ai/
cp chromium/native_host/com.noguardrail.ollama.json \
   ~/.config/chromium/NativeMessagingHosts/
```

## Gebruik

### AI Sidebar Activeren

```
Cmd+Shift+A (macOS)
Ctrl+Shift+A (Linux/Windows)
```

### Context Menu

Rechtsklik op geselecteerde tekst:
- "Ask AI about this" - Vraag uitleg
- "Generate code" - Genereer code
- "Improve this" - Verbeter tekst
- "Translate" - Vertaal

### Dev Tools Integration

In DevTools Console:

```javascript
// Direct AI access
await ai.ask('Explain this function');

// Code generation
await ai.generate('Create a React component for...');

// Current page context
await ai.analyze(document.body.innerText);
```

## Native Messaging Host

De bridge tussen Chromium en Ollama:

```python
# chromium/native_host/ollama_host.py
import json
import sys
import requests

OLLAMA_URL = 'http://localhost:11434'

def send_message(message):
    sys.stdout.buffer.write(struct.pack('I', len(message)))
    sys.stdout.buffer.write(message.encode('utf-8'))
    sys.stdout.buffer.flush()

def read_message():
    text_length_bytes = sys.stdin.buffer.read(4)
    text_length = struct.unpack('I', text_length_bytes)[0]
    text = sys.stdin.buffer.read(text_length).decode('utf-8')
    return json.loads(text)

while True:
    message = read_message()
    
    # Forward naar Ollama
    response = requests.post(
        f'{OLLAMA_URL}/api/generate',
        json={
            'model': 'dolphin-uncensored',
            'prompt': message['prompt'],
            'stream': False
        }
    )
    
    send_message(json.dumps(response.json()))
```

## AI Sidebar Component

```typescript
// chrome/browser/resources/ai_sidebar/app.tsx
import React, { useState } from 'react';
import { sendNativeMessage } from './native_bridge';

export const AISidebar: React.FC = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    const response = await sendNativeMessage({
      type: 'chat',
      prompt: input,
      context: await getPageContext()
    });
    
    setMessages([...messages, 
      { role: 'user', content: input },
      { role: 'assistant', content: response.text }
    ]);
  };

  return (
    <div className="ai-sidebar">
      <div className="messages">
        {messages.map((msg, i) => (
          <Message key={i} {...msg} />
        ))}
      </div>
      <input 
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyPress={e => e.key === 'Enter' && sendMessage()}
      />
    </div>
  );
};
```

## Custom Patches

### 1. Remove Google Services

```patch
--- a/chrome/browser/chrome_browser_main.cc
+++ b/chrome/browser/chrome_browser_main.cc
@@ -1234,7 +1234,7 @@
   // Initialize Google Update services
-  google_update::InitializeGoogleUpdate();
+  // google_update::InitializeGoogleUpdate();  // REMOVED
```

### 2. Add AI Keybinding

```patch
--- a/chrome/browser/ui/views/frame/browser_view.cc
+++ b/chrome/browser/ui/views/frame/browser_view.cc
@@ +445,6 +445,11 @@
+  // AI Sidebar toggle
+  focus_manager->RegisterAccelerator(
+      ui::Accelerator(ui::VKEY_A, ui::EF_COMMAND_DOWN | ui::EF_SHIFT_DOWN),
+      ui::AcceleratorManager::kNormalPriority,
+      this);
```

### 3. Custom New Tab Page

```patch
--- a/chrome/browser/ui/webui/ntp/new_tab_ui.cc
+++ b/chrome/browser/ui/webui/ntp/new_tab_ui.cc
@@ -89,7 +89,7 @@
-  source->AddResourcePath("new_tab.html", IDR_NEW_TAB_HTML);
+  source->AddResourcePath("new_tab.html", IDR_AI_NEW_TAB_HTML);
```

## Pre-built Binaries

Voor wie niet wil compileren:

### macOS (Apple Silicon)
```bash
curl -O https://github.com/vandurmedries/no-guardrail-ai/releases/download/v1.0/NoGuardrailAI-mac-arm64.dmg
open NoGuardrailAI-mac-arm64.dmg
```

### Linux (x64)
```bash
wget https://github.com/vandurmedries/no-guardrail-ai/releases/download/v1.0/no-guardrail-ai-linux-x64.tar.gz
tar xzf no-guardrail-ai-linux-x64.tar.gz
sudo ./install.sh
```

## Development

```bash
# Hot reload sidebar
cd chrome/browser/resources/ai_sidebar
npm run dev

# Rebuild alleen sidebar
autoninja -C out/Default chrome/browser/resources/ai_sidebar

# Test native messaging
python chromium/native_host/test_host.py
```

## Configuration

Settings → AI Assistant:

```json
{
  "ollama_endpoint": "http://localhost:11434",
  "model": "dolphin-uncensored",
  "temperature": 0.7,
  "context_mode": "auto",
  "sidebar_position": "right",
  "keybinding": "Cmd+Shift+A"
}
```

## Privacy & Security

✅ Alle telemetry verwijderd
✅ Geen Google API calls
✅ Geen crash reporting naar Google
✅ Geen Safe Browsing (optional)
✅ Geen account sync met Google
✅ 100% lokale AI - geen data leaves machine

## Performance

- **Build tijd**: 2-4 uur (afhankelijk van CPU)
- **Disk space**: ~40GB voor source + build
- **Runtime**: Iets zwaarder dan stock Chromium door AI sidebar (~100MB extra RAM)
- **AI latency**: Afhankelijk van je Ollama setup

## Troubleshooting

### Native messaging werkt niet

```bash
# Check manifest location
ls ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/

# Test host direct
echo '{"prompt":"test"}' | python chromium/native_host/ollama_host.py
```

### Sidebar laadt niet

```bash
# Rebuild sidebar
cd chrome/browser/resources/ai_sidebar
npm run build

# Check browser console (Cmd+Option+I)
```

### Build fails

```bash
# Clean build
rm -rf out/Default
gn gen out/Default

# Sync deps
gclient sync -D
```

## Roadmap

- [ ] Extension API voor custom AI tools
- [ ] Multi-model support (switch tussen modellen)
- [ ] Voice input via Whisper
- [ ] Screenshot → code generator
- [ ] Browser automation via AI (like Anthropic Computer Use)
- [ ] Sync via eigen server (geen Google)

## Contributing

Pull requests welcome! Focus areas:

- Performance optimizations
- More AI integrations
- Better context extraction
- UI/UX improvements

## License

Chromium source: BSD 3-Clause (upstream)
Custom patches & sidebar: MIT

## Links

- [Chromium Build Docs](https://chromium.googlesource.com/chromium/src/+/main/docs/mac_build_instructions.md)
- [Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)

---

**Build status**: ![Build](https://img.shields.io/github/workflow/status/vandurmedries/no-guardrail-ai/build)

**Gebouwd met**: Chromium 131 + React 18 + Python 3.11
