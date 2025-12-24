"""
CineMate Care - Audio Monitor (Phase 6: Tuning)

Real-time audio level detection to mute AI during loud movie scenes.
Rule: If movie volume > threshold dB, suppress AI speech.

This module helps avoid the embarrassing scenario of the AI
speaking over an explosion or dramatic soundtrack.
"""

import os
import time
import logging
import threading
import numpy as np
from typing import Optional, Callable
from collections import deque
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import pyaudio, fall back to simulation if not available
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("⚠️ PyAudio not available. Using simulated audio levels.")


class AudioMonitor:
    """
    Real-time audio level monitor for intelligent AI speech timing.
    
    Features:
    - Monitors system audio input (movie audio)
    - Calculates decibel levels in real-time
    - Provides is_quiet() method for AI to check before speaking
    - "Cognitive Processing Pause" - signals when to pause video
    """
    
    def __init__(
        self,
        threshold_db: float = 70.0,
        quiet_duration_ms: int = 500,
        sample_rate: int = 44100,
        chunk_size: int = 1024
    ):
        """
        Initialize the audio monitor.
        
        Args:
            threshold_db: dB level above which is "loud" (0-100 scale)
            quiet_duration_ms: How long audio must be quiet before AI can speak
            sample_rate: Audio sample rate in Hz
            chunk_size: Number of samples per chunk
        """
        self.threshold_db = threshold_db
        self.quiet_duration_ms = quiet_duration_ms
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        
        # State tracking
        self.current_db: float = 0.0
        self.is_monitoring: bool = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # History for smoothing
        self.db_history: deque = deque(maxlen=50)  # ~1 second history
        self.last_loud_time: Optional[datetime] = None
        
        # Callbacks
        self.on_loud: Optional[Callable[[float], None]] = None
        self.on_quiet: Optional[Callable[[float], None]] = None
        
        # PyAudio setup
        self.pyaudio_instance: Optional['pyaudio.PyAudio'] = None
        self.stream = None
        
        logger.info(f"🔊 Audio Monitor initialized (threshold: {threshold_db}dB)")
    
    def _calculate_db(self, audio_data: np.ndarray) -> float:
        """
        Calculate decibel level from audio samples.
        
        Uses RMS (Root Mean Square) for accurate volume measurement.
        Returns value on 0-100 scale for easy thresholding.
        """
        if len(audio_data) == 0:
            return 0.0
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
        
        if rms == 0:
            return 0.0
        
        # Convert to dB (normalized to 0-100 scale)
        # Reference: 32768 is max value for 16-bit audio
        db = 20 * np.log10(rms / 32768.0)
        
        # Normalize to 0-100 scale (typical range is -60 to 0 dB)
        normalized_db = max(0, min(100, (db + 60) * (100 / 60)))
        
        return normalized_db
    
    def _monitor_loop(self) -> None:
        """Background thread for continuous audio monitoring."""
        logger.info("🎤 Audio monitoring started")
        
        if PYAUDIO_AVAILABLE:
            self._monitor_with_pyaudio()
        else:
            self._monitor_simulated()
        
        logger.info("🎤 Audio monitoring stopped")
    
    def _monitor_with_pyaudio(self) -> None:
        """Monitor audio using PyAudio (real implementation)."""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            while self.is_monitoring:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    
                    db = self._calculate_db(audio_array)
                    self._process_db_level(db)
                    
                except Exception as e:
                    logger.warning(f"Audio read error: {e}")
                    time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"PyAudio initialization error: {e}")
        
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
    
    def _monitor_simulated(self) -> None:
        """Simulated audio monitoring for testing without PyAudio."""
        while self.is_monitoring:
            # Simulate realistic audio levels
            # Mostly quiet (30-50 dB) with occasional loud bursts (70-90 dB)
            if np.random.random() > 0.9:  # 10% chance of loud
                db = np.random.uniform(70, 90)
            else:
                db = np.random.uniform(30, 55)
            
            self._process_db_level(db)
            time.sleep(0.02)  # ~50 updates per second
    
    def _process_db_level(self, db: float) -> None:
        """Process a new dB reading."""
        self.current_db = db
        self.db_history.append(db)
        
        # Check if loud
        if db > self.threshold_db:
            self.last_loud_time = datetime.now()
            if self.on_loud:
                self.on_loud(db)
        else:
            # Check if quiet long enough
            if self.is_quiet() and self.on_quiet:
                self.on_quiet(db)
    
    def start(self) -> bool:
        """Start audio monitoring in background thread."""
        if self.is_monitoring:
            logger.warning("Already monitoring")
            return False
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        return True
    
    def stop(self) -> None:
        """Stop audio monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def is_quiet(self) -> bool:
        """
        Check if audio has been quiet long enough for AI to speak.
        
        Returns True if:
        1. Current level is below threshold, AND
        2. It's been quiet for at least quiet_duration_ms
        """
        if self.current_db > self.threshold_db:
            return False
        
        if self.last_loud_time is None:
            return True
        
        elapsed_ms = (datetime.now() - self.last_loud_time).total_seconds() * 1000
        return elapsed_ms >= self.quiet_duration_ms
    
    def get_average_db(self) -> float:
        """Get smoothed average dB over recent history."""
        if not self.db_history:
            return 0.0
        return np.mean(list(self.db_history))
    
    def should_ai_speak(self) -> dict:
        """
        Determine if AI should speak now.
        
        Returns dict with:
        - can_speak: bool - True if safe to speak
        - current_db: float - Current audio level
        - reason: str - Why or why not
        """
        current = self.current_db
        avg = self.get_average_db()
        quiet = self.is_quiet()
        
        if not quiet:
            if current > self.threshold_db:
                reason = f"Loud audio detected ({current:.1f}dB > {self.threshold_db}dB)"
            else:
                reason = f"Audio was recently loud, waiting for {self.quiet_duration_ms}ms silence"
            return {
                "can_speak": False,
                "current_db": current,
                "average_db": avg,
                "reason": reason
            }
        
        return {
            "can_speak": True,
            "current_db": current,
            "average_db": avg,
            "reason": "Audio is quiet, safe to speak"
        }


class CognitiveProcessingPause:
    """
    Implements the "Cognitive Processing Pause" feature.
    
    When the AI needs to think, this can signal to pause the video,
    think, respond, then unpause. This is a FEATURE, not a bug!
    
    "While I consider this scene, let me pause for just a moment..."
    """
    
    def __init__(self, pause_callback: Optional[Callable] = None, 
                 unpause_callback: Optional[Callable] = None):
        """
        Initialize cognitive pause controller.
        
        Args:
            pause_callback: Function to call to pause video
            unpause_callback: Function to call to unpause video
        """
        self.pause_callback = pause_callback
        self.unpause_callback = unpause_callback
        self.is_paused = False
    
    def thinking_start(self) -> None:
        """Call when AI starts processing (may pause video)."""
        if self.pause_callback and not self.is_paused:
            logger.info("⏸️ Cognitive Processing Pause - Video paused")
            self.is_paused = True
            self.pause_callback()
    
    def thinking_end(self) -> None:
        """Call when AI finishes processing (may unpause video)."""
        if self.unpause_callback and self.is_paused:
            logger.info("▶️ Cognitive Processing Resume - Video resumed")
            self.is_paused = False
            self.unpause_callback()


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("CineMate Care - Audio Monitor Test")
    print("=" * 60)
    
    monitor = AudioMonitor(threshold_db=65)
    
    def on_loud(db):
        print(f"🔊 LOUD: {db:.1f} dB")
    
    def on_quiet(db):
        print(f"🔇 quiet: {db:.1f} dB")
    
    monitor.on_loud = on_loud
    monitor.on_quiet = on_quiet
    
    monitor.start()
    
    print("\nMonitoring audio levels... Press Ctrl+C to stop.\n")
    
    try:
        while True:
            result = monitor.should_ai_speak()
            status = "✅ CAN SPEAK" if result["can_speak"] else "🔇 WAIT"
            print(f"\r{status} | dB: {result['current_db']:.1f} | Avg: {result['average_db']:.1f}", end="")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n⚡ Stopped")
    finally:
        monitor.stop()
