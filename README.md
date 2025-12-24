# 🎬 CineMate Care

**AI-Powered Cognitive Companion for Elderly Users**

CineMate Care is an intelligent movie-watching companion that helps elderly users and those with visual impairments enjoy media content. It provides real-time scene descriptions, emotional support, and voice interaction - like having a caring friend explain what's happening on screen.

![Azure](https://img.shields.io/badge/Azure-AI%20Foundry-0078D4?style=flat&logo=microsoft-azure)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat&logo=streamlit)

---

## ✨ Features

- **🎥 Real-Time Scene Analysis** - Azure AI Vision describes what's happening on screen
- **🧠 Intelligent Commentary** - GPT-4o decides when and what to say (never interrupts dialogue!)
- **🗣️ Natural Voice** - Azure Speech provides warm, emotional voice output
- **🛡️ Safety Monitoring** - Detects user distress and offers comfort
- **📊 Caregiver Dashboard** - Real-time monitoring via Streamlit

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

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Webcam
- Microphone & Speakers
- Azure subscription with:
  - **Azure AI Vision** (Computer Vision)
  - **Azure AI Foundry** (with GPT-4o deployed)
  - **Azure Speech Service**

### 1. Clone the Repository

```bash
git clone https://github.com/himnshz/CineMate-AI.git
cd CineMate-AI
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 4. Configure Azure Credentials

Create a `.env` file in the `backend/` folder:

```env
# Azure AI Vision
AZURE_VISION_ENDPOINT=https://your-vision-resource.cognitiveservices.azure.com/
AZURE_VISION_KEY=your-vision-api-key

# Azure AI Foundry (OpenAI)
AZURE_OPENAI_ENDPOINT=https://your-foundry-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Azure Speech
AZURE_SPEECH_KEY=your-speech-api-key
AZURE_SPEECH_REGION=eastus

# App Settings
TTS_VOICE=en-US-DavisNeural
WAKE_WORD=CineMate
```

### 5. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Dashboard:**
```bash
cd frontend
streamlit run app.py
```

---

## ☁️ Azure Setup Guide

### Azure AI Vision (Computer Vision)

1. Go to [Azure Portal](https://portal.azure.com/)
2. Create resource → **Computer Vision**
3. Copy **Endpoint** and **Key** to `.env`

### Azure AI Foundry (GPT-4o)

1. Go to [Azure AI Foundry](https://ai.azure.com/)
2. Create or select a **Project**
3. Go to **Model catalog** → Find **gpt-4o**
4. Click **Deploy** → Name it `gpt-4o`
5. After deployment, copy the **Endpoint URL** to `.env`

> **Important:** The deployment name in Azure AI Foundry must match `AZURE_OPENAI_DEPLOYMENT` in your `.env` file.

### Azure Speech Service

1. Go to [Azure Portal](https://portal.azure.com/)
2. Create resource → **Speech**
3. Copy **Key** and note the **Region**

---

## 📁 Project Structure

```
CineMate-AI/
├── backend/
│   ├── main.py              # Main orchestrator
│   ├── vision_capture.py    # Azure AI Vision integration
│   ├── cognitive_engine.py  # Azure OpenAI (GPT-4o) integration
│   ├── voice_interface.py   # Azure Speech TTS/STT
│   ├── demo_mode.py         # Demo/backup mode
│   └── requirements.txt
├── frontend/
│   ├── app.py               # Streamlit dashboard
│   └── requirements.txt
├── docs/
│   └── demo_script.md       # Demo presentation script
└── README.md
```

---

## 🎮 Usage

### Voice Commands

| Command | Action |
|---------|--------|
| "CineMate" | Wake word - activates the AI |
| "What's happening?" | Describes the current scene |
| "Who is that?" | Character identification |
| "Help" / "Stop" | Triggers safety response |

### Keyboard Shortcuts (Demo Mode)

| Key | Response |
|-----|----------|
| SPACE | Smart context response |
| F1 | Greeting |
| F2 | Scene description |
| F3 | Answer question |
| F4 | Distress response |

---

## 🛡️ Safety Features

- **Distress Detection** - Monitors for keywords like "help", "scared", "stop"
- **Comfort Mode** - Offers to pause content during overwhelming scenes
- **Guardian Dashboard** - Caregivers can monitor remotely

---

## 🏆 Built For

**Microsoft Imagine Cup 2026** - Accessibility & Healthcare Track

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Microsoft Azure AI Services
- OpenAI GPT-4o
- Streamlit Community
