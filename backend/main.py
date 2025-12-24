"""
CineMate Care - Main Orchestrator (Phase 5: "The Guardian")

This is the main entry point that ties together all modules:
- VisionCapture (Azure AI Vision)
- CognitiveEngine (Azure OpenAI GPT-4o)
- VoiceInterface (Azure Speech)

The orchestrator runs asynchronously to ensure the video feed never freezes
while the AI is "thinking" or speaking.

AZURE SERVICES ORCHESTRATED:
- Azure AI Vision: Scene understanding
- Azure OpenAI Service: Context analysis and decision making
- Azure Speech Service: Voice input/output
"""

import os
import cv2
import json
import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from queue import Queue, Empty
from threading import Thread, Event
from dotenv import load_dotenv

# Import CineMate Care modules
from vision_capture import VisionCapture
from cognitive_engine import CognitiveEngine
from voice_interface import VoiceInterface, VoiceInterfaceSimulator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cinemate_care.log', mode='a')
    ]
)
logger = logging.getLogger("CineMate")


# =============================================================================
# CINEMATE CARE ORCHESTRATOR
# =============================================================================
class CinemateCareOrchestrator:
    """
    Main orchestrator for CineMate Care - The Cognitive Companion.
    
    This class coordinates three Azure-powered modules:
    1. VisionCapture - Webcam + Azure AI Vision for scene understanding
    2. CognitiveEngine - Azure OpenAI GPT-4o for decision making
    3. VoiceInterface - Azure Speech for TTS/STT
    
    The orchestrator manages:
    - Async event loop for non-blocking operation
    - Thread management for parallel processing
    - Safety protocols for distress detection
    - Graceful shutdown handling
    """
    
    def __init__(self, use_simulator: bool = False):
        """
        Initialize the CineMate Care orchestrator.
        
        Args:
            use_simulator: If True, use simulated voice (no Azure Speech)
        """
        logger.info("=" * 60)
        logger.info("🎬 CineMate Care - Cognitive Companion Starting...")
        logger.info("=" * 60)
        
        # ====================================================================
        # MODULE INITIALIZATION
        # Each module connects to its respective Azure service
        # ====================================================================
        
        # Phase 1: Vision Pipeline (Azure AI Vision)
        logger.info("📷 Initializing Vision Capture (Azure AI Vision)...")
        try:
            self.vision = VisionCapture()
            logger.info("✅ Vision Capture ready")
        except Exception as e:
            logger.error(f"❌ Vision Capture failed: {e}")
            self.vision = None
        
        # Phase 2: Cognitive Engine (Azure OpenAI GPT-4o)
        logger.info("🧠 Initializing Cognitive Engine (Azure OpenAI GPT-4o)...")
        try:
            self.engine = CognitiveEngine()
            logger.info("✅ Cognitive Engine ready")
        except Exception as e:
            logger.error(f"❌ Cognitive Engine failed: {e}")
            self.engine = None
        
        # Phase 3: Voice Interface (Azure Speech)
        logger.info("🎤 Initializing Voice Interface (Azure Speech)...")
        try:
            if use_simulator:
                self.voice = VoiceInterfaceSimulator()
            else:
                self.voice = VoiceInterface()
            logger.info("✅ Voice Interface ready")
        except Exception as e:
            logger.warning(f"⚠️ Voice Interface failed, using simulator: {e}")
            self.voice = VoiceInterfaceSimulator()
        
        # ====================================================================
        # STATE MANAGEMENT
        # ====================================================================
        self.running = False
        self.shutdown_event = Event()
        
        # User interaction tracking
        self.user_history: List[str] = []
        self.max_history = 20
        
        # Caption and context tracking
        self.latest_caption: Optional[str] = None
        self.audio_transcript: str = ""  # Would come from audio processing
        
        # Safety tracking
        self.last_distress_check = datetime.now()
        self.distress_cooldown = timedelta(seconds=30)  # Don't spam distress messages
        
        # Thread management
        self.vision_thread: Optional[Thread] = None
        self.caption_queue: Queue = Queue()
        
        logger.info("=" * 60)
        logger.info("🎬 CineMate Care - Initialization Complete")
        logger.info("=" * 60)
    
    def _on_wake_word(self, text: str) -> None:
        """
        Callback when wake word is detected.
        
        AZURE SERVICE: Azure Speech Service (STT)
        - Triggered when "CineMate" is detected in user speech
        """
        logger.info(f"✨ Wake word detected: '{text}'")
        
        # Add to user history for context
        self.user_history.append(text)
        if len(self.user_history) > self.max_history:
            self.user_history.pop(0)
        
        # Acknowledge the user
        response = "Yes, I'm here! What can I help you with?"
        self.voice.speak_async(response, style="cheerful")
    
    def _on_distress(self, text: str) -> None:
        """
        Callback when distress is detected.
        
        AZURE SERVICE: Azure Speech Service (STT)
        - Triggered when distress keywords are detected
        
        SAFETY PROTOCOL:
        - Immediately offer comfort and option to pause
        - Log the incident
        """
        logger.warning(f"⚠️ DISTRESS DETECTED: '{text}'")
        
        # Check cooldown to avoid spamming
        now = datetime.now()
        if now - self.last_distress_check < self.distress_cooldown:
            logger.debug("Distress message on cooldown, skipping")
            return
        
        self.last_distress_check = now
        
        # Compassionate response
        comfort_message = (
            "I noticed you might be feeling overwhelmed. "
            "Would you like me to pause the movie? "
            "Take all the time you need."
        )
        self.voice.speak_async(comfort_message, style="empathetic")
    
    def _on_user_speech(self, text: str) -> None:
        """
        Callback for all recognized speech.
        
        AZURE SERVICE: Azure Speech Service (STT)
        - Logs all user utterances for context building
        """
        logger.info(f"👤 User said: '{text}'")
        
        # Add to history
        self.user_history.append(text)
        if len(self.user_history) > self.max_history:
            self.user_history.pop(0)
    
    def _vision_worker(self) -> None:
        """
        Background worker for webcam capture and frame analysis.
        
        AZURE SERVICE: Azure AI Vision (Computer Vision 4.0)
        - Runs in separate thread to not block main loop
        - Captures frames and detects keyframes
        - Sends keyframes to Azure for scene analysis
        - Saves frames for Streamlit dashboard consumption
        """
        logger.info("📷 Vision worker thread started")
        
        if self.vision is None:
            logger.error("Vision module not available")
            return
        
        if not self.vision.start_camera():
            logger.error("Failed to start camera")
            return
        
        last_analysis_time = 0  # Track last API call time
        MIN_ANALYSIS_INTERVAL = 15  # Send to Azure every 15 seconds
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        frame_path = os.path.join(backend_dir, 'latest_frame.jpg')
        
        try:
            while not self.shutdown_event.is_set():
                ret, frame = self.vision.get_frame()
                if not ret:
                    time.sleep(0.03)
                    continue
                
                # Save EVERY frame for Streamlit dashboard (smooth constant video)
                try:
                    cv2.imwrite(frame_path, frame)
                except Exception as e:
                    pass  # Silently ignore frame save errors
                
                # API calls at intervals - separate from video display
                current_time = time.time()
                if current_time - last_analysis_time >= MIN_ANALYSIS_INTERVAL:
                    # Process frame (send to Azure for analysis)
                    result = self.vision.process_frame(frame)
                    last_analysis_time = current_time
                    
                    if result:
                        if result.get("caption"):
                            caption_text = result["caption"]["text"]
                            people_count = result.get("people_count", 0)
                            self.caption_queue.put({
                                "caption": caption_text,
                                "timestamp": result["timestamp"],
                                "people_count": people_count,
                                "dense_captions": result.get("dense_captions", [])
                            })
                            logger.info(f"👥 {people_count} people | 📝 {caption_text}")
                            self._log_activity("VISION", f"{caption_text[:60]}")
                
                # Minimal sleep - video runs at ~30 FPS
                time.sleep(0.033)
        
        except Exception as e:
            logger.error(f"Vision worker error: {e}")
        
        finally:
            self.vision.stop_camera()
            logger.info("📷 Vision worker thread stopped")
    
    def _log_activity(self, log_type: str, message: str, mood: str = "Calm") -> None:
        """
        Log activity for Streamlit dashboard consumption.
        Writes to activity_log.json which the frontend reads.
        """
        # Use absolute path in backend directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(backend_dir, "activity_log.json")
        
        try:
            # Read existing log
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {"logs": [], "scene": "", "mood": "Calm", "thought": "", "interventions": 0}
            
            # Add new entry
            data["logs"].append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": log_type,
                "message": message
            })
            
            # Keep only last 50 entries
            data["logs"] = data["logs"][-50:]
            
            # Update mood if provided
            if mood:
                data["mood"] = mood
            
            # Update scene description
            if log_type == "VISION":
                data["scene"] = message
            
            # Update thought if it's an action
            if log_type == "ACTION":
                data["thought"] = message
                data["interventions"] = data.get("interventions", 0) + 1
            
            # Write back
            with open(log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.debug(f"Activity log error: {e}")
    
    async def _main_loop(self) -> None:
        """
        Main asynchronous orchestration loop.
        
        This loop:
        1. Gets latest visual caption from Azure AI Vision
        2. Checks for distress from Azure Speech STT
        3. Sends context to Azure OpenAI GPT-4o for analysis
        4. Speaks response via Azure Speech TTS if appropriate
        
        AZURE SERVICES COORDINATED:
        - Azure AI Vision (scene captions)
        - Azure Speech (distress detection)
        - Azure OpenAI (decision making)
        - Azure Speech (TTS response)
        """
        logger.info("🔄 Main orchestration loop started")
        
        loop_count = 0
        
        while self.running and not self.shutdown_event.is_set():
            loop_count += 1
            
            try:
                # ============================================================
                # STEP 1: Get latest visual caption from Azure AI Vision
                # ============================================================
                try:
                    caption_data = self.caption_queue.get_nowait()
                    self.latest_caption = caption_data["caption"]
                except Empty:
                    pass  # No new caption, use existing
                
                # ============================================================
                # STEP 2: Check for distress (Azure Speech STT)
                # ============================================================
                if hasattr(self.voice, 'distress_detected_recently'):
                    if self.voice.distress_detected_recently(10):
                        logger.warning("⚠️ Recent distress detected, triggering safety response")
                        # This is handled by the _on_distress callback
                        await asyncio.sleep(0.5)
                        continue
                
                # ============================================================
                # STEP 3: Send to Cognitive Engine (Azure OpenAI GPT-4o)
                # ============================================================
                if self.latest_caption and self.engine:
                    # Only analyze periodically to avoid API spam
                    if loop_count % 30 == 0:  # Every ~3 seconds at 100ms loop
                        logger.debug("🧠 Sending context to Cognitive Engine...")
                        
                        # Run cognitive analysis in executor to not block
                        decision = await asyncio.get_event_loop().run_in_executor(
                            None,
                            self.engine.analyze_context,
                            self.latest_caption,
                            self.audio_transcript,
                            self.user_history if self.user_history else None
                        )
                        
                        # ====================================================
                        # STEP 4: Speak if AI decides to (Azure Speech TTS)
                        # ====================================================
                        if decision.get("should_speak") and decision.get("content"):
                            emotion = decision.get("emotion", "neutral")
                            content = decision["content"]
                            
                            logger.info(f"🗣️ AI speaking ({emotion}): {content[:50]}...")
                            
                            # Speak asynchronously
                            await asyncio.get_event_loop().run_in_executor(
                                None,
                                self.voice.speak_async,
                                content,
                                emotion,
                                False  # non-blocking
                            )
                        else:
                            logger.debug(f"🤐 AI staying quiet: {decision.get('reasoning', 'No reason')[:50]}")
                
                # Small sleep to prevent CPU overuse
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(1)  # Longer sleep on error
        
        logger.info("🔄 Main orchestration loop stopped")
    
    def start(self) -> None:
        """
        Start the CineMate Care system.
        
        This starts:
        1. Vision capture thread (webcam + Azure AI Vision)
        2. Speech listener (Azure Speech STT)
        3. Main orchestration loop (async)
        """
        logger.info("🚀 Starting CineMate Care...")
        
        self.running = True
        self.shutdown_event.clear()
        
        # Start vision capture thread
        if self.vision:
            self.vision_thread = Thread(target=self._vision_worker, daemon=True)
            self.vision_thread.start()
            logger.info("📷 Vision thread started")
        
        # Start speech listener
        if hasattr(self.voice, 'start_listening'):
            self.voice.start_listening(
                on_wake_word=self._on_wake_word,
                on_distress=self._on_distress,
                on_user_speech=self._on_user_speech
            )
            logger.info("🎤 Speech listener started")
        
        # Initial greeting
        greeting = "Hello! I'm CineMate Care, your friendly movie companion. I'm here whenever you need me."
        self.voice.speak_async(greeting, style="cheerful", block=True)
        
        # Run main loop
        try:
            asyncio.run(self._main_loop())
        except KeyboardInterrupt:
            logger.info("⚡ Interrupted by user")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """
        Gracefully stop the CineMate Care system.
        """
        logger.info("🛑 Stopping CineMate Care...")
        
        self.running = False
        self.shutdown_event.set()
        
        # Stop speech listener
        if hasattr(self.voice, 'stop_listening'):
            self.voice.stop_listening()
        
        # Wait for vision thread
        if self.vision_thread and self.vision_thread.is_alive():
            self.vision_thread.join(timeout=2)
        
        # Cleanup voice interface
        if hasattr(self.voice, 'cleanup'):
            self.voice.cleanup()
        
        # Farewell message
        farewell = "Goodbye! It was lovely watching with you. Take care!"
        self.voice.speak_async(farewell, style="empathetic", block=True)
        
        logger.info("✅ CineMate Care stopped gracefully")


# =============================================================================
# SIGNAL HANDLERS FOR GRACEFUL SHUTDOWN
# =============================================================================
orchestrator: Optional[CinemateCareOrchestrator] = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    if orchestrator:
        orchestrator.stop()
    sys.exit(0)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    """Main entry point for CineMate Care."""
    global orchestrator
    
    # Check for --demo flag (runs without Azure credentials)
    demo_mode = '--demo' in sys.argv or '--mock' in sys.argv
    
    if demo_mode:
        print("""
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║   🎬 CineMate Care - DEMO MODE                                           ║
    ║                                                                           ║
    ║   Running WITHOUT Azure credentials!                                      ║
    ║   All AI services are simulated for demonstration purposes.              ║
    ║                                                                           ║
    ║   To use real Azure services, configure your .env file.                  ║
    ║   See README.md for setup instructions.                                   ║
    ║                                                                           ║
    ║   Press Ctrl+C to stop                                                    ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
        """)
        
        # Import and run demo mode
        from mock_services import MockVisionCapture, MockCognitiveEngine, MockVoiceInterface
        
        logger.info("🎬 Starting CineMate Care in DEMO MODE")
        
        # Create mock services
        vision = MockVisionCapture()
        engine = MockCognitiveEngine()
        voice = MockVoiceInterface()
        
        # Simple demo loop
        voice.speak_async("Hello! I'm CineMate Care running in demo mode. All AI services are simulated.", style="cheerful")
        
        vision.start_camera()
        try:
            import time
            loop_count = 0
            while True:
                loop_count += 1
                ret, frame = vision.get_frame()
                result = vision.process_frame(frame)
                
                if result:
                    caption = result["caption"]["text"]
                    decision = engine.analyze_context(caption)
                    
                    if decision.get("should_speak") and decision.get("content"):
                        voice.speak_async(decision["content"], style=decision.get("emotion", "neutral"))
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n⚡ Demo stopped by user")
        finally:
            vision.stop_camera()
            voice.speak_async("Goodbye! Thanks for trying CineMate Care demo.", style="cheerful")
        
        return
    
    # Normal mode with Azure services
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🎬 CineMate Care - Cognitive Companion for Elderly Users   ║
    ║                                                               ║
    ║   Azure Services:                                             ║
    ║   • Azure AI Vision (Computer Vision 4.0) - Scene Analysis   ║
    ║   • Azure OpenAI Service (GPT-4o) - Decision Making          ║
    ║   • Azure Speech Service - Voice Interaction                 ║
    ║                                                               ║
    ║   Press Ctrl+C to stop                                        ║
    ║                                                               ║
    ║   💡 Tip: Run with --demo flag to try without Azure          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check for --simulator flag
    use_simulator = '--simulator' in sys.argv or '--sim' in sys.argv
    
    if use_simulator:
        print("🔧 Running in SIMULATOR mode (no Azure Speech)")
    
    # Create and start orchestrator
    try:
        orchestrator = CinemateCareOrchestrator(use_simulator=use_simulator)
        orchestrator.start()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease ensure your .env file is configured correctly.")
        print("Or run with --demo flag to try without Azure credentials:")
        print("    python main.py --demo")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal Error: {e}")
        print("\nTip: Run with --demo flag to try without Azure credentials:")
        print("    python main.py --demo")
        sys.exit(1)


if __name__ == "__main__":
    main()
