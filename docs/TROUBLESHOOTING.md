# Troubleshooting Guide

Common issues and solutions for CineMate Care.

---

## 🚀 Quick Fix: Use Demo Mode

Most issues are related to Azure credentials. **Skip them entirely**:

```bash
cd backend
python main.py --demo
```

This runs with simulated AI services — no Azure account needed!

---

## Common Errors

### ❌ "Azure Vision credentials not found"

**Cause**: Missing or invalid `.env` file.

**Fix**:
1. Copy the template: `cp .env.example .env`
2. Fill in your Azure credentials
3. OR just use `--demo` mode

---

### ❌ "The requested resource is not found" (404 from OpenAI)

**Cause**: GPT-4o model not deployed in Azure AI Foundry.

**Fix**:
1. Go to [Azure AI Foundry](https://ai.azure.com/)
2. Navigate to Deployments
3. Deploy `gpt-4o` model
4. Ensure deployment name matches `AZURE_OPENAI_DEPLOYMENT` in `.env`

---

### ❌ "ModuleNotFoundError: No module named..."

**Cause**: Dependencies not installed.

**Fix**:
```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

---

### ❌ Camera not working

**Cause**: Webcam in use by another app, or not connected.

**Fix**:
1. Close other apps using webcam (Zoom, Teams, etc.)
2. Check webcam is connected
3. Try demo mode: `python main.py --demo`

---

### ❌ "pyaudio" installation fails on Windows

**Cause**: Missing build tools for pyaudio.

**Fix**:
```bash
pip install pipwin
pipwin install pyaudio
```

Or skip audio features with demo mode.

---

## Still Stuck?

1. **Check logs**: Look at `cinemate_care.log` for detailed errors
2. **Open an issue**: [GitHub Issues](https://github.com/himnshz/CineMate-AI/issues)
3. **Test components individually**:
   ```bash
   python vision_capture.py      # Test Azure Vision
   python cognitive_engine.py    # Test Azure OpenAI
   python voice_interface.py     # Test Azure Speech
   python mock_services.py       # Test demo mode
   ```
