"""
CineMate Care - Mock Services for Demo Mode

These mock implementations allow the project to run WITHOUT Azure credentials,
making it easy for anyone to try the project instantly.

Usage:
    python main.py --demo
"""

import time
import random
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# MOCK SCENE DESCRIPTIONS
# Realistic responses that simulate Azure AI Vision output
# =============================================================================
MOCK_SCENES = [
    {
        "caption": "Scene: 2 persons detected, living room, television, couch",
        "people_count": 2,
        "tags": ["person", "living room", "television", "couch", "indoor"],
        "mood": "Calm"
    },
    {
        "caption": "Scene: 1 person detected, elderly person, sitting, window",
        "people_count": 1,
        "tags": ["person", "elderly", "sitting", "window", "indoor"],
        "mood": "Calm"
    },
    {
        "caption": "Scene: 3 persons detected, family gathering, dining table",
        "people_count": 3,
        "tags": ["person", "family", "dining", "table", "happy"],
        "mood": "Happy"
    },
    {
        "caption": "Scene: 1 person detected, person looking sad, alone",
        "people_count": 1,
        "tags": ["person", "sad", "alone", "emotional"],
        "mood": "Sad"
    },
    {
        "caption": "Scene: 2 persons detected, animated conversation, gestures",
        "people_count": 2,
        "tags": ["person", "conversation", "gestures", "talking"],
        "mood": "Engaged"
    },
]

MOCK_AI_RESPONSES = [
    {
        "should_speak": True,
        "emotion": "calm",
        "content": "It looks like a quiet moment in the scene. The characters seem to be having a thoughtful conversation.",
        "reasoning": "Scene shows calm interaction, good time to provide context"
    },
    {
        "should_speak": False,
        "emotion": "neutral",
        "content": "",
        "reasoning": "Scene is mundane, no need to interrupt"
    },
    {
        "should_speak": True,
        "emotion": "empathetic",
        "content": "This seems like an emotional moment. Take your time if you need a break.",
        "reasoning": "Detected emotional content in scene"
    },
    {
        "should_speak": True,
        "emotion": "cheerful",
        "content": "What a lovely scene! The family looks so happy together.",
        "reasoning": "Positive emotional content detected"
    },
    {
        "should_speak": False,
        "emotion": "neutral",
        "content": "",
        "reasoning": "Dialogue in progress, staying quiet"
    },
]


class MockVisionCapture:
    """
    Mock implementation of VisionCapture for demo mode.
    Simulates webcam capture and Azure AI Vision responses.
    """
    
    def __init__(self, camera_index: int = 0, **kwargs):
        logger.info("📷 [MOCK] Vision Capture initialized (Demo Mode - No Azure)")
        self.frame_count = 0
        self.analysis_count = 0
        self.latest_caption = None
        self.cap = None
        self._scene_index = 0
        
    def start_camera(self) -> bool:
        """Simulate camera start."""
        logger.info("📷 [MOCK] Camera started (simulated)")
        return True
    
    def stop_camera(self) -> None:
        """Simulate camera stop."""
        logger.info("📷 [MOCK] Camera stopped")
    
    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Return a simulated frame (colored noise for demo)."""
        self.frame_count += 1
        # Create a simple gradient frame for demo
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some color variation
        frame[:, :, 0] = 50  # Blue channel
        frame[:, :, 1] = 100  # Green channel  
        frame[:, :, 2] = 150  # Red channel
        # Add text overlay
        return True, frame
    
    def process_frame(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Return mock scene analysis."""
        # Only "analyze" every 30 frames to simulate real behavior
        if self.frame_count % 30 != 0:
            return None
        
        self.analysis_count += 1
        self._scene_index = (self._scene_index + 1) % len(MOCK_SCENES)
        scene = MOCK_SCENES[self._scene_index]
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "frame_number": self.frame_count,
            "analysis_number": self.analysis_count,
            "caption": {
                "text": scene["caption"],
                "confidence": 0.85
            },
            "people_count": scene["people_count"],
            "tags": scene["tags"],
            "dense_captions": [],
            "metadata": {
                "azure_service": "[MOCK] Demo Mode - No Azure",
                "demo_mode": True
            }
        }
        
        self.latest_caption = result
        logger.info(f"📷 [MOCK] Scene: {scene['caption']}")
        return result
    
    def get_latest_caption(self) -> Optional[Dict[str, Any]]:
        return self.latest_caption
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "frames_captured": self.frame_count,
            "frames_analyzed": self.analysis_count,
            "demo_mode": True
        }


class MockCognitiveEngine:
    """
    Mock implementation of CognitiveEngine for demo mode.
    Returns scripted responses without calling GPT-4o.
    """
    
    def __init__(self, **kwargs):
        logger.info("🧠 [MOCK] Cognitive Engine initialized (Demo Mode - No Azure OpenAI)")
        self._response_index = 0
        self.character_memory: Dict[str, str] = {}
    
    def analyze_context(
        self,
        scene_description: str,
        audio_transcript: str = "",
        user_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Return mock AI decision."""
        # Cycle through mock responses
        self._response_index = (self._response_index + 1) % len(MOCK_AI_RESPONSES)
        response = MOCK_AI_RESPONSES[self._response_index].copy()
        
        # Add metadata
        response["metadata"] = {
            "azure_service": "[MOCK] Demo Mode - No Azure OpenAI",
            "timestamp": datetime.now().isoformat(),
            "demo_mode": True
        }
        
        if response["should_speak"]:
            logger.info(f"🧠 [MOCK] AI will speak: {response['content'][:50]}...")
        else:
            logger.debug(f"🧠 [MOCK] AI staying quiet: {response['reasoning']}")
        
        return response
    
    def add_character(self, name: str, description: str) -> None:
        self.character_memory[name] = description
        logger.info(f"📝 [MOCK] Character added: {name}")
    
    def detect_distress(self, user_text: str) -> bool:
        distress_keywords = ["help", "stop", "scared", "afraid", "pause"]
        return any(kw in user_text.lower() for kw in distress_keywords)
    
    def get_comfort_message(self) -> str:
        return "I noticed you might be feeling overwhelmed. Would you like to take a break?"


class MockVoiceInterface:
    """
    Mock Voice Interface that prints to console.
    Extends the existing VoiceInterfaceSimulator concept.
    """
    
    def __init__(self, **kwargs):
        logger.info("🎤 [MOCK] Voice Interface initialized (Demo Mode - No Azure Speech)")
        self.is_speaking = False
        self.is_listening = False
        self.last_distress_time = None
    
    def speak_async(self, text: str, style: str = "neutral", block: bool = False) -> bool:
        print(f"\n🔊 [DEMO VOICE - {style.upper()}]: {text}\n")
        return True
    
    def speak_simple(self, text: str) -> bool:
        print(f"\n🔊 [DEMO]: {text}\n")
        return True
    
    def start_listening(self, **kwargs) -> bool:
        logger.info("🎤 [MOCK] Listener started (simulated - use keyboard for input)")
        self.is_listening = True
        return True
    
    def stop_listening(self) -> None:
        self.is_listening = False
    
    def distress_detected_recently(self, seconds: int = 10) -> bool:
        return False
    
    def cleanup(self) -> None:
        pass


def get_mock_services():
    """
    Factory function to get all mock service instances.
    
    Returns:
        Tuple of (MockVisionCapture, MockCognitiveEngine, MockVoiceInterface)
    """
    return (
        MockVisionCapture(),
        MockCognitiveEngine(), 
        MockVoiceInterface()
    )


# =============================================================================
# DEMO MODE BANNER
# =============================================================================
DEMO_BANNER = """
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
╚═══════════════════════════════════════════════════════════════════════════╝
"""

if __name__ == "__main__":
    print(DEMO_BANNER)
    print("Testing mock services...")
    
    # Test MockVisionCapture
    vision = MockVisionCapture()
    vision.start_camera()
    for i in range(35):
        ret, frame = vision.get_frame()
        result = vision.process_frame(frame)
        if result:
            print(f"Vision result: {result['caption']['text']}")
    vision.stop_camera()
    
    # Test MockCognitiveEngine
    engine = MockCognitiveEngine()
    for i in range(5):
        result = engine.analyze_context("Test scene description")
        print(f"AI decision: speak={result['should_speak']}, content={result.get('content', 'N/A')[:30]}")
    
    # Test MockVoiceInterface
    voice = MockVoiceInterface()
    voice.speak_async("Hello! This is a demo of CineMate Care.", style="cheerful")
    
    print("\n✅ All mock services working correctly!")
