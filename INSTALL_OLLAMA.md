# Installing Ollama on Windows

## Option 1: Direct Download (Recommended)

1. **Download Ollama**:
   - Go to: https://ollama.com/download
   - Download the Windows installer
   - Run the installer as administrator

2. **Verify Installation**:
   ```bash
   ollama --version
   ```

3. **Start Ollama Service**:
   ```bash
   ollama serve
   ```

4. **Install Qwen2.5-VL Model**:
   ```bash
   ollama pull qwen2.5-vl
   ```

5. **Verify Model Installation**:
   ```bash
   ollama list
   ```

## Option 2: Using PowerShell

If the direct download doesn't work, you can try:

```powershell
# Download and install Ollama
Invoke-WebRequest -Uri "https://ollama.com/download/windows" -OutFile "ollama-windows-amd64.exe"
./ollama-windows-amd64.exe
```

## Troubleshooting

### If Ollama command is not recognized:
1. Restart your terminal/PowerShell
2. Check if Ollama was added to PATH
3. Try running from the installation directory

### If model download fails:
```bash
# Try alternative model names
ollama pull qwen2-vl
ollama pull qwen2.5:latest
```

### If port 11434 is busy:
```bash
# Check what's using the port
netstat -ano | findstr :11434

# Kill the process if needed
taskkill /PID <PID_NUMBER> /F
```

## Testing Your Installation

After installation, run our test script:
```bash
python test_ollama.py
```

This will verify that:
- Ollama is running
- The model is available
- API communication works
