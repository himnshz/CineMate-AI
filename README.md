# 🎬 CineMate Care

**AI-Powered Cognitive Companion for Elderly Users**

CineMate Care is an intelligent movie-watching companion designed to help elderly users and those with visual impairments enjoy media content. It provides real-time scene descriptions, emotional support, and voice interaction — like having a caring friend explain what's happening on screen.

![Azure](https://img.shields.io/badge/Azure-AI%20Foundry-0078D4?style=flat&logo=microsoft-azure)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat&logo=streamlit)
![CI](https://github.com/himnshz/CineMate-AI/actions/workflows/ci.yml/badge.svg)

---

## 🚀 Try It Now (No Azure Required!)

**Run in demo mode** — no cloud credentials needed:

```bash
git clone https://github.com/himnshz/CineMate-AI.git
cd CineMate-AI
pip install -r backend/requirements.txt
cd backend
python main.py --demo
```

This uses simulated AI services so you can instantly experience the concept!

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎥 **Scene Analysis** | Real-time description of what's happening on screen |
| 🧠 **Smart Commentary** | AI decides when and what to say (never interrupts dialogue!) |
| 🗣️ **Natural Voice** | Warm, emotional voice output for a companion-like experience |
| 🛡️ **Safety Monitoring** | Detects user distress and offers comfort |
| 📊 **Caregiver Dashboard** | Remote monitoring via Streamlit interface |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Azure AI       │     │  Azure AI       │     │  Azure Speech   │
│  Vision         │     │  Foundry        │     │  Service        │
│  (Scene Analysis)│     │  (GPT-4o)       │     │  (TTS/STT)      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   CineMate Orchestrator │
                    │      (main.py)          │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
     ┌────────┴────────┐ ┌───────┴───────┐ ┌───────┴───────┐
     │ vision_capture  │ │cognitive_engine│ │voice_interface│
     │    (Eyes)       │ │    (Brain)     │ │   (Mouth)     │
     └─────────────────┘ └───────────────┘ └───────────────┘
```

---

## 📦 Installation

### Prerequisites

- Python 3.9+
- Webcam (optional for demo mode)
- Microphone & Speakers (optional)

### Quick Setup

```bash
# Clone repository
git clone https://github.com/himnshz/CineMate-AI.git
cd CineMate-AI

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### Running Modes

| Mode | Command | Requirements |
|------|---------|--------------|
| **Demo** | `python main.py --demo` | None! |
| **Simulator** | `python main.py --sim` | Azure Vision + OpenAI |
| **Full** | `python main.py` | All Azure services |

---

## ☁️ Azure Setup (Optional)

For full functionality with real AI services:

### 1. Azure AI Vision
1. Go to [Azure Portal](https://portal.azure.com/) → Create **Computer Vision** resource
2. Copy Endpoint and Key

### 2. Azure AI Foundry (GPT-4o)
1. Go to [Azure AI Foundry](https://ai.azure.com/)
2. Create/select a Project → Go to **Model catalog** → Deploy **gpt-4o**
3. Name deployment `gpt-4o` → Copy Endpoint URL

### 3. Azure Speech
1. Azure Portal → Create **Speech** resource
2. Copy Key and note Region

### 4. Configure .env
Create `backend/.env`:
```env
AZURE_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_VISION_KEY=your-key

AZURE_OPENAI_ENDPOINT=https://your-foundry.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o

AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=eastus

TTS_VOICE=en-US-DavisNeural
WAKE_WORD=CineMate
```

---

## 📁 Project Structure

```
CineMate-AI/
├── backend/
│   ├── main.py              # Main orchestrator
│   ├── vision_capture.py    # Azure AI Vision
│   ├── cognitive_engine.py  # Azure OpenAI (GPT-4o)
│   ├── voice_interface.py   # Azure Speech
│   ├── mock_services.py     # Demo mode (no Azure)
│   └── tests/               # Unit tests
├── frontend/
│   └── app.py               # Streamlit dashboard
├── .github/
│   ├── workflows/ci.yml     # CI pipeline
│   └── ISSUE_TEMPLATE/      # Bug/feature templates
├── CONTRIBUTING.md
└── README.md
```

---

## 🗺️ Roadmap

### ✅ Phase 1: Core MVP (Current)
- [x] Azure AI Vision integration
- [x] Azure OpenAI (GPT-4o) integration
- [x] Azure Speech TTS/STT
- [x] Demo mode (no Azure required)
- [x] Caregiver dashboard

### 🚧 Phase 2: Enhanced Experience
- [ ] Character memory across sessions
- [ ] Personalized user profiles
- [ ] Multi-language support
- [ ] Mobile app for caregivers

### 🔮 Phase 3: Healthcare Integration
- [ ] Integration with health monitoring
- [ ] Emotional wellness tracking
- [ ] Professional caregiver portal
- [ ] HIPAA-compliant deployment

---

## 🎮 Usage

### Voice Commands
| Command | Action |
|---------|--------|
| "CineMate" | Wake word - activates AI |
| "What's happening?" | Scene description |
| "Who is that?" | Character info |
| "Help" / "Stop" | Safety response |

### Dashboard
```bash
cd frontend
streamlit run app.py
```

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## ❓ Troubleshooting

Having issues? See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common problems and solutions.

## 🏆 Built For

**Microsoft Imagine Cup 2026** — Accessibility & Healthcare Track

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.
