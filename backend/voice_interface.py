"""
CineMate Care - Voice Interface Module (Phase 3: "The Mouth")

This module handles all speech input/output using Azure Speech Service,
including Text-to-Speech with emotional styles and Speech-to-Text with
wake word and distress detection.

AZURE SERVICE USED: Azure Speech Service
- TTS: Neural voices with SSML for emotional expression
- STT: Continuous speech recognition for user interaction
"""

import os
import time
import logging
import threading
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime, timedelta
from queue import Queue
from dotenv import load_dotenv

# ============================================================================
# AZURE SPEECH SDK
# This SDK provides Text-to-Speech (TTS) and Speech-to-Text (STT) capabilities.
# Neural voices sound natural and can express emotions via SSML.
# ============================================================================
import azure.cognitiveservices.speech as speechsdk

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# SSML TEMPLATES FOR EMOTIONAL SPEECH
# SSML (Speech Synthesis Markup Language) controls how the AI speaks.
# Different styles make the voice sound empathetic, cheerful, etc.
# =============================================================================
SSML_TEMPLATE = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
       xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
    <voice name="{voice_name}">
        <mstts:express-as style="{style}" styledegree="{degree}">
            <prosody rate="{rate}" pitch="{pitch}">
                {text}
            </prosody>
        </mstts:express-as>
    </voice>
</speak>
"""

# Voice style configurations for different emotions
EMOTION_STYLES = {
    "empathetic": {
        "style": "empathetic",
        "degree": "1.5",
        "rate": "-5%",
        "pitch": "-2%"
    },
    "cheerful": {
        "style": "cheerful",
        "degree": "1.2",
        "rate": "+5%",
        "pitch": "+3%"
    },
    "calm": {
        "style": "calm",
        "degree": "1.0",
        "rate": "-10%",
        "pitch": "-5%"
    },
    "concerned": {
        "style": "sad",  # Azure uses 'sad' for concerned tone
        "degree": "1.0",
        "rate": "-5%",
        "pitch": "-3%"
    },
    "neutral": {
        "style": "general",
        "degree": "1.0",
        "rate": "0%",
        "pitch": "0%"
    }
}


class VoiceInterface:
    """
    Speech input/output interface using Azure Speech Service.
    
    Provides:
    - Text-to-Speech with emotional styles (neural voices + SSML)
    - Speech-to-Text with continuous listening
    - Wake word detection ("CineMate")
    - Distress keyword monitoring
    
    AZURE SERVICE: Azure Speech Service
    - TTS Engine: Neural voices (en-US-DavisNeural, en-US-JennyNeural)
    - STT Engine: Continuous speech recognition
    """
    
    def __init__(
        self,
        speech_key: Optional[str] = None,
        speech_region: Optional[str] = None,
        voice_name: Optional[str] = None
    ):
        """
        Initialize the Voice Interface with Azure Speech credentials.
        
        Args:
            speech_key: Azure Speech API key (or from env: AZURE_SPEECH_KEY)
            speech_region: Azure region (or from env: AZURE_SPEECH_REGION)
            voice_name: Neural voice to use (or from env: TTS_VOICE)
        """
        # ====================================================================
        # AZURE SPEECH SERVICE CONFIGURATION
        # This configures both TTS and STT capabilities.
        # Requires: Speech Key and Region from Azure portal
        # ====================================================================
        self.speech_key = speech_key or os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = speech_region or os.getenv("AZURE_SPEECH_REGION", "eastus")
        self.voice_name = voice_name or os.getenv("TTS_VOICE", "en-US-DavisNeural")
        
        if not self.speech_key:
            raise ValueError(
                "Azure Speech credentials not found. "
                "Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in .env file"
            )
        
        # Create speech configuration
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        
        # Set default voice for TTS
        self.speech_config.speech_synthesis_voice_name = self.voice_name
        
        logger.info(f"✅ Azure Speech Service initialized (region: {self.speech_region}, voice: {self.voice_name})")
        
        # ====================================================================
        # TEXT-TO-SPEECH (TTS) SYNTHESIZER
        # Uses Azure's Neural TTS with SSML for emotional expression
        # ====================================================================
        self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
        
        # ====================================================================
        # SPEECH-TO-TEXT (STT) CONFIGURATION
        # For continuous listening and wake word detection
        # ====================================================================
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer: Optional[speechsdk.SpeechRecognizer] = None
        
        # Wake word and distress detection
        self.wake_word = os.getenv("WAKE_WORD", "CineMate").lower()
        self.distress_keywords = [
            "help", "stop", "pause", "scared", "afraid",
            "don't like", "too much", "overwhelming", "can't watch"
        ]
        
        # State tracking
        self.is_listening = False
        self.is_speaking = False
        self.listener_thread: Optional[threading.Thread] = None
        self.recognized_text_queue: Queue = Queue()
        
        # Callback storage
        self.on_wake_word: Optional[Callable[[str], None]] = None
        self.on_distress: Optional[Callable[[str], None]] = None
        self.on_user_speech: Optional[Callable[[str], None]] = None
        
        # Distress tracking
        self.last_distress_time: Optional[datetime] = None
    
    def speak_async(
        self,
        text: str,
        style: str = "neutral",
        block: bool = False
    ) -> bool:
        """
        Speak the given text using Azure Neural TTS with emotional style.
        
        AZURE SERVICE: Azure Speech Service - Text-to-Speech API
        - Engine: Neural TTS
        - Features: SSML for prosody and emotional expression
        
        Args:
            text: What to say
            style: Emotional style (empathetic, cheerful, calm, concerned, neutral)
            block: If True, wait for speech to complete before returning
            
        Returns:
            bool: True if speech started successfully
        """
        if not text:
            return False
        
        self.is_speaking = True
        logger.info(f"🗣️ Speaking ({style}): {text[:50]}...")
        
        # Get style configuration
        style_config = EMOTION_STYLES.get(style, EMOTION_STYLES["neutral"])
        
        # Build SSML for expressive speech
        ssml = SSML_TEMPLATE.format(
            voice_name=self.voice_name,
            style=style_config["style"],
            degree=style_config["degree"],
            rate=style_config["rate"],
            pitch=style_config["pitch"],
            text=text
        )
        
        try:
            # ================================================================
            # AZURE SPEECH TTS API CALL
            # This sends the SSML to Azure for neural speech synthesis
            # ================================================================
            if block:
                # Synchronous speech (blocks until complete)
                result = self.synthesizer.speak_ssml(ssml)
            else:
                # Asynchronous speech (returns immediately)
                result = self.synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("✅ Speech completed successfully")
                self.is_speaking = False
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"❌ Speech cancelled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation.error_details}")
                self.is_speaking = False
                return False
                
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            self.is_speaking = False
            return False
        
        self.is_speaking = False
        return True
    
    def speak_simple(self, text: str) -> bool:
        """
        Simple speech without emotional styling.
        
        Args:
            text: What to say
            
        Returns:
            bool: True if successful
        """
        try:
            result = self.synthesizer.speak_text(text)
            return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted
        except Exception as e:
            logger.error(f"❌ Simple TTS error: {e}")
            return False
    
    def start_listening(
        self,
        on_wake_word: Optional[Callable[[str], None]] = None,
        on_distress: Optional[Callable[[str], None]] = None,
        on_user_speech: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Start continuous speech recognition in a background thread.
        
        AZURE SERVICE: Azure Speech Service - Speech-to-Text API
        - Mode: Continuous recognition
        - Features: Real-time transcription with phrase detection
        
        Args:
            on_wake_word: Callback when wake word is detected (receives full phrase)
            on_distress: Callback when distress is detected (receives phrase)
            on_user_speech: Callback for all recognized speech
            
        Returns:
            bool: True if listener started successfully
        """
        if self.is_listening:
            logger.warning("⚠️ Already listening")
            return False
        
        self.on_wake_word = on_wake_word
        self.on_distress = on_distress
        self.on_user_speech = on_user_speech
        
        # ====================================================================
        # AZURE SPEECH STT RECOGNIZER
        # Creates a continuous speech recognizer using the default microphone
        # ====================================================================
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=self.audio_config
        )
        
        # Set up event handlers
        self.speech_recognizer.recognized.connect(self._on_recognized)
        self.speech_recognizer.session_started.connect(
            lambda evt: logger.info("🎤 Listening session started")
        )
        self.speech_recognizer.session_stopped.connect(
            lambda evt: logger.info("🎤 Listening session stopped")
        )
        
        try:
            # Start continuous recognition
            self.speech_recognizer.start_continuous_recognition()
            self.is_listening = True
            logger.info(f"🎤 Started listening for wake word: '{self.wake_word}'")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start listener: {e}")
            return False
    
    def _on_recognized(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        """
        Handle recognized speech events.
        
        This is called by Azure Speech SDK when speech is recognized.
        It checks for wake words, distress keywords, and notifies callbacks.
        """
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text.strip()
            if not text:
                return
            
            logger.info(f"🎤 Heard: '{text}'")
            text_lower = text.lower()
            
            # Add to queue for other modules
            self.recognized_text_queue.put({
                "text": text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Check for wake word
            if self.wake_word in text_lower:
                logger.info(f"✨ Wake word detected!")
                if self.on_wake_word:
                    self.on_wake_word(text)
            
            # Check for distress keywords
            for keyword in self.distress_keywords:
                if keyword in text_lower:
                    logger.warning(f"⚠️ Distress keyword detected: '{keyword}'")
                    self.last_distress_time = datetime.now()
                    if self.on_distress:
                        self.on_distress(text)
                    break
            
            # General speech callback
            if self.on_user_speech:
                self.on_user_speech(text)
    
    def stop_listening(self) -> None:
        """Stop the continuous speech recognition."""
        if self.speech_recognizer and self.is_listening:
            try:
                self.speech_recognizer.stop_continuous_recognition()
                self.is_listening = False
                logger.info("🎤 Stopped listening")
            except Exception as e:
                logger.error(f"❌ Error stopping listener: {e}")
    
    def distress_detected_recently(self, seconds: int = 10) -> bool:
        """
        Check if distress was detected within the last N seconds.
        
        Args:
            seconds: Time window to check
            
        Returns:
            bool: True if distress was detected recently
        """
        if self.last_distress_time is None:
            return False
        
        time_since = datetime.now() - self.last_distress_time
        return time_since < timedelta(seconds=seconds)
    
    def get_recent_speech(self) -> List[Dict[str, Any]]:
        """
        Get all recently recognized speech from the queue.
        
        Returns:
            List of speech dictionaries with text and timestamp
        """
        results = []
        while not self.recognized_text_queue.empty():
            results.append(self.recognized_text_queue.get())
        return results
    
    def set_audio_ducking(self, duck: bool) -> None:
        """
        Placeholder for audio ducking (lowering video volume when AI speaks).
        
        Note: Full implementation would require platform-specific audio control.
        This is a placeholder that logs the intent.
        
        Args:
            duck: True to lower volume, False to restore
        """
        if duck:
            logger.info("🔉 [AUDIO DUCKING] Lowering background audio...")
            # Platform-specific implementation would go here
            # Examples:
            # - Windows: Use pycaw library
            # - macOS: Use osascript
            # - Linux: Use pactl
        else:
            logger.info("🔊 [AUDIO DUCKING] Restoring background audio...")
    
    def cleanup(self) -> None:
        """Release all resources."""
        self.stop_listening()
        logger.info("🧹 Voice interface cleaned up")


class VoiceInterfaceSimulator:
    """
    Simulator for testing without Azure credentials.
    Prints speech to console instead of using TTS.
    """
    
    def __init__(self):
        logger.info("📢 Using Voice Interface Simulator (no Azure credentials)")
        self.is_speaking = False
        self.is_listening = False
        self.last_distress_time = None
    
    def speak_async(self, text: str, style: str = "neutral", block: bool = False) -> bool:
        print(f"\n🔊 [SIMULATED SPEECH - {style.upper()}]: {text}\n")
        return True
    
    def speak_simple(self, text: str) -> bool:
        print(f"\n🔊 [SIMULATED]: {text}\n")
        return True
    
    def start_listening(self, **kwargs) -> bool:
        logger.info("🎤 [SIMULATED] Listener started (use keyboard input instead)")
        self.is_listening = True
        return True
    
    def stop_listening(self) -> None:
        self.is_listening = False
    
    def distress_detected_recently(self, seconds: int = 10) -> bool:
        return False
    
    def cleanup(self) -> None:
        pass


# =============================================================================
# STANDALONE TEST MODE
# Run this file directly to test the Voice Interface
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("CineMate Care - Voice Interface Test")
    print("AZURE SERVICE: Azure Speech Service")
    print("=" * 60)
    
    try:
        voice = VoiceInterface()
    except ValueError as e:
        print(f"\n⚠️ {e}")
        print("Using simulator mode for testing...\n")
        voice = VoiceInterfaceSimulator()
    
    # Test TTS with different emotions
    test_phrases = [
        ("Hello! I'm CineMate Care, your friendly movie companion.", "cheerful"),
        ("This is a touching moment in the film.", "empathetic"),
        ("Let me describe what's happening on screen.", "calm"),
        ("I noticed you might be feeling overwhelmed. Would you like to take a break?", "concerned"),
        ("That character is John, the baker from the first scene.", "neutral"),
    ]
    
    print("\n🎤 Testing Text-to-Speech with different emotions:\n")
    
    for text, emotion in test_phrases:
        print(f"Emotion: {emotion}")
        print(f"Text: {text}")
        voice.speak_async(text, style=emotion, block=True)
        print("-" * 40)
        time.sleep(0.5)
    
    # Test listening (if real voice interface)
    if isinstance(voice, VoiceInterface):
        print("\n🎤 Testing Speech-to-Text...")
        print(f"Say something with the wake word '{voice.wake_word}'")
        print("Press Ctrl+C to stop.\n")
        
        def on_wake(text):
            print(f"✨ Wake word callback: {text}")
        
        def on_distress(text):
            print(f"⚠️ Distress callback: {text}")
        
        voice.start_listening(
            on_wake_word=on_wake,
            on_distress=on_distress
        )
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⚡ Interrupted by user")
        finally:
            voice.stop_listening()
    
    voice.cleanup()
    print("\n✅ Voice interface test complete!")
