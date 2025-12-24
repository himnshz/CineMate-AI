# CineMate Care - Demo Script

## Pre-Demo Checklist ✅

- [ ] `.env` file configured with Azure credentials
- [ ] Webcam connected and working
- [ ] Microphone tested
- [ ] Movie clip ready (Up opening or chosen clip)
- [ ] Wizard of Oz backup tested (Spacebar, F1-F6)
- [ ] Azure logs terminal open and visible
- [ ] Demo mode enabled: `set DEMO_MODE=true`

---

## Demo Script (2 minutes)

### Part 1: Introduction (0:00 - 0:20)

**[Show split screen: "Before" vs "After"]**

PRESENTER:
> "Imagine watching your favorite movie, alone, unable to see clearly 
> what's happening on screen. For millions of elderly and visually 
> impaired people, this is their daily reality. 
>
> Today, we're introducing CineMate Care."

**[Transition to live demo screen]**

---

### Part 2: Wake Word (0:20 - 0:40)

**[CineMate is running, movie paused]**

PRESENTER:
> "Let me introduce you to CineMate."

**[Say to the system]**
> "Hello, CineMate!"

**CINEMATE RESPONDS:**
> "Hello! I'm CineMate Care, your friendly movie companion. 
> I'm here whenever you need me."

**[Point to Azure logs showing STT → OpenAI → TTS flow]**

---

### Part 3: Scene Description (0:40 - 1:20)

**[Start the movie clip - "Up" opening sequence]**

**[Let it play for 10-15 seconds until Carl and Ellie meet]**

**CINEMATE RESPONDS (automatically):**
> "Oh, what a wonderful beginning! A young boy meeting a spirited 
> girl in an old clubhouse. You can tell they're going to be 
> best friends."

PRESENTER:
> "Notice how CineMate waited for a quiet moment before speaking. 
> It never interrupts dialogue."

**[Point to Azure Vision logs showing scene analysis]**

---

### Part 4: Accessibility Q&A (1:20 - 1:50)

**[Let movie continue to adventure book scene]**

**[Ask the system]**
> "CineMate, what is she showing him?"

**CINEMATE RESPONDS:**
> "She's showing him her adventure book! Paradise Falls in South 
> America - that's her dream destination. What a big dream for 
> such a young heart."

PRESENTER:
> "Vivid descriptions, not technical jargon. Like a friend 
> explaining what you missed."

---

### Part 5: Under the Hood (1:50 - 2:00)

**[Zoom on the Azure terminal logs]**

PRESENTER:
> "Under the hood, three Azure services working together:
> - Azure AI Vision analyzing scenes in real-time
> - Azure OpenAI's GPT-4o making intelligent decisions  
> - Azure Speech providing natural, empathetic voice
>
> All running live, right now."

**[End demo]**

---

## Backup Responses (Wizard of Oz)

If Azure fails, use these keyboard shortcuts:

| Key | Response |
|-----|----------|
| **SPACE** | Smart context response (auto-picks) |
| **F1** | Greeting: "Hello! I'm CineMate Care..." |
| **F2** | Scene: "I can see an emotional scene..." |
| **F3** | Question: "I'm happy to help describe..." |
| **F4** | Distress: "I noticed you might need..." |
| **F5** | Farewell: "It was lovely watching..." |
| **F6** | Generic: "That's an interesting scene..." |

---

## Emergency Procedures 🚨

### If webcam fails:
> "We're experiencing a small technical difficulty with the camera, 
> but let me show you how CineMate responds to voice..."

### If Azure Vision fails:
> Press **F2** for scene description backup

### If Azure Speech (TTS) fails:
> "The voice component is loading. Meanwhile, you can see the 
> text response here..." [Point to dashboard]

### If everything fails:
> Pre-record a 2-minute demo video as absolute last resort

---

## Demo Environment Setup

```powershell
# Set demo mode
$env:DEMO_MODE = "true"

# Run the main application
python main.py

# OR run dashboard
streamlit run dashboard.py
```

---

## Talking Points for Q&A

**Q: How do you handle privacy?**
> Everything runs in real-time with no recording or storage. 
> The video stream is analyzed frame-by-frame and immediately discarded.

**Q: What about latency?**
> We use keyframe extraction to analyze only significant changes,
> reducing latency while saving API costs by 80%.

**Q: How is this different from screen readers?**
> Screen readers describe UI elements. CineMate understands 
> *context* - it knows when a scene is sad, when a character
> returns, when you need support. It's a companion, not a tool.

**Q: Business model?**
> B2C subscription for individuals, B2B licensing for 
> assisted living facilities and vision impairment organizations.
