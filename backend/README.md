# 🎬 CineMate Care - Cognitive Companion for Elderly Users

A compassionate AI companion designed to reduce isolation and assist with understanding visual media for elderly users and those with visual impairments.

## 🌟 Features

- **Scene Understanding**: Real-time scene descriptions using Azure AI Vision
- **Intelligent Responses**: Context-aware AI that knows when to speak (Azure OpenAI GPT-4o)
- **Natural Voice**: Emotional TTS with neural voices (Azure Speech)
- **Wake Word Detection**: Say "CineMate" to get the AI's attention
- **Safety Protocols**: Distress detection with comfort responses
- **Real-time Dashboard**: Monitor the system with Streamlit UI

## 🛠️ Azure Services Used

| Service | Purpose |
|---------|---------|
| Azure AI Vision (Computer Vision 4.0) | Scene analysis, captions, object detection |
| Azure OpenAI Service (GPT-4o) | Context analysis, decision making |
| Azure Speech Service | Text-to-Speech (Neural), Speech-to-Text |

## 📁 Project Structure

```
cinemate-ai/
├── main.py              # Phase 5: Orchestrator
├── vision_capture.py    # Phase 1: Webcam + Azure Vision
├── cognitive_engine.py  # Phase 2: Azure OpenAI GPT-4o
├── voice_interface.py   # Phase 3: Azure Speech TTS/STT
├── dashboard.py         # Phase 4: Streamlit Dashboard
├── requirements.txt     # Python dependencies
├── .env.example         # Azure credentials template
└── README.md            # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- Webcam
- Microphone
- Azure subscription with:
  - Azure AI Vision resource
  - Azure OpenAI resource (with GPT-4o deployed)
  - Azure Speech resource

### 2. Installation

```bash
# Clone or navigate to the project
cd "d:\microsoft hackathon\Cinemate AI"

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Azure Credentials

```bash
# Copy the example file
copy .env.example .env

# Edit .env with your Azure credentials
notepad .env
```

Required credentials in `.env`:
```ini
AZURE_VISION_ENDPOINT=https://your-vision.cognitiveservices.azure.com/
AZURE_VISION_KEY=your-key-here

AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o

AZURE_SPEECH_KEY=your-key-here
AZURE_SPEECH_REGION=eastus
```

### 4. Run the Application

**Full System:**
```bash
python main.py
```

**With Voice Simulator (no Azure Speech):**
```bash
python main.py --simulator
```

**Dashboard Only:**
```bash
streamlit run dashboard.py
```

**Test Individual Modules:**
```bash
# Test Vision
python vision_capture.py

# Test Cognitive Engine
python cognitive_engine.py

# Test Voice Interface
python voice_interface.py
```

## 🎯 How It Works

1. **Webcam Capture**: Frames are captured from your webcam
2. **Keyframe Detection**: Only significantly different frames are analyzed (saves API costs)
3. **Scene Analysis**: Azure AI Vision generates captions for keyframes
4. **Context Decision**: GPT-4o decides if the AI should speak based on:
   - Is there dialogue? (Don't interrupt)
   - Is the scene emotional? (Offer support)
   - Did the user ask something? (Respond)
5. **Voice Response**: Neural TTS speaks with appropriate emotion
6. **Safety Monitoring**: Distress keywords trigger comfort responses

## 🎨 Dashboard Features

- **Live Video Feed**: See what the AI sees
- **AI Thought Overlay**: Current analysis status
- **Engagement Charts**: Track user engagement over time
- **Scene Logs**: Real-time analysis history
- **Azure Status**: Service health indicators

## ⚙️ Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `CARE_MODE` | active | `active` or `passive` |
| `TTS_VOICE` | en-US-DavisNeural | Azure neural voice name |
| `WAKE_WORD` | CineMate | Activation phrase |

## 🔒 Safety Features

- **Distress Detection**: Monitors for words like "help", "stop", "scared"
- **Comfort Protocol**: Offers to pause and provides supportive messages
- **Non-Blocking**: Video never freezes while AI is processing
- **Graceful Shutdown**: Clean exit on Ctrl+C

## 📝 API Cost Optimization

- SSIM-based keyframe detection reduces Vision API calls by ~80%
- 5-second maximum interval ensures periodic updates
- Cognitive Engine only queries GPT-4o every 3 seconds during active viewing

## 🤝 Contributing

This project was created for the Microsoft Imagine Cup 2026.

## 📄 License

MIT License
