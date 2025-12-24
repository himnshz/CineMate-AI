"""
Tests for CineMate Care Mock Services

These tests verify that the demo mode works correctly
without requiring any Azure credentials.
"""

import pytest
import numpy as np
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_services import (
    MockVisionCapture, 
    MockCognitiveEngine, 
    MockVoiceInterface,
    get_mock_services
)


class TestMockVisionCapture:
    """Tests for MockVisionCapture."""
    
    def test_initialization(self):
        """Test that MockVisionCapture initializes without errors."""
        vision = MockVisionCapture()
        assert vision is not None
        assert vision.frame_count == 0
    
    def test_start_camera(self):
        """Test camera start simulation."""
        vision = MockVisionCapture()
        result = vision.start_camera()
        assert result is True
        vision.stop_camera()
    
    def test_get_frame(self):
        """Test frame capture simulation."""
        vision = MockVisionCapture()
        vision.start_camera()
        ret, frame = vision.get_frame()
        
        assert ret is True
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)
        
        vision.stop_camera()
    
    def test_process_frame_returns_caption(self):
        """Test that process_frame returns scene analysis."""
        vision = MockVisionCapture()
        vision.start_camera()
        
        # Process enough frames to trigger analysis
        result = None
        for i in range(35):
            ret, frame = vision.get_frame()
            result = vision.process_frame(frame)
            if result:
                break
        
        assert result is not None
        assert "caption" in result
        assert "text" in result["caption"]
        assert "people_count" in result
        
        vision.stop_camera()


class TestMockCognitiveEngine:
    """Tests for MockCognitiveEngine."""
    
    def test_initialization(self):
        """Test that MockCognitiveEngine initializes without errors."""
        engine = MockCognitiveEngine()
        assert engine is not None
    
    def test_analyze_context(self):
        """Test context analysis returns valid response."""
        engine = MockCognitiveEngine()
        result = engine.analyze_context("A person watching TV")
        
        assert "should_speak" in result
        assert "emotion" in result
        assert "content" in result
        assert "reasoning" in result
        assert isinstance(result["should_speak"], bool)
    
    def test_distress_detection(self):
        """Test distress keyword detection."""
        engine = MockCognitiveEngine()
        
        assert engine.detect_distress("I'm scared") is True
        assert engine.detect_distress("Help me") is True
        assert engine.detect_distress("This is great") is False
        assert engine.detect_distress("I love this movie") is False


class TestMockVoiceInterface:
    """Tests for MockVoiceInterface."""
    
    def test_initialization(self):
        """Test that MockVoiceInterface initializes without errors."""
        voice = MockVoiceInterface()
        assert voice is not None
    
    def test_speak_async(self):
        """Test that speak_async doesn't error and returns True."""
        voice = MockVoiceInterface()
        result = voice.speak_async("Hello world", style="cheerful")
        assert result is True
    
    def test_start_listening(self):
        """Test listener simulation."""
        voice = MockVoiceInterface()
        result = voice.start_listening()
        assert result is True
        assert voice.is_listening is True
        voice.stop_listening()


class TestIntegration:
    """Integration tests for mock services."""
    
    def test_get_mock_services(self):
        """Test factory function returns all services."""
        vision, engine, voice = get_mock_services()
        
        assert isinstance(vision, MockVisionCapture)
        assert isinstance(engine, MockCognitiveEngine)
        assert isinstance(voice, MockVoiceInterface)
    
    def test_full_pipeline(self):
        """Test a full demo pipeline cycle."""
        vision, engine, voice = get_mock_services()
        
        # Start vision
        vision.start_camera()
        
        # Get frames and find one that triggers analysis
        for _ in range(35):
            ret, frame = vision.get_frame()
            result = vision.process_frame(frame)
            
            if result:
                # Analyze with cognitive engine
                caption = result["caption"]["text"]
                decision = engine.analyze_context(caption)
                
                # Speak if AI decides to
                if decision["should_speak"]:
                    voice.speak_async(
                        decision["content"], 
                        style=decision.get("emotion", "neutral")
                    )
                break
        
        vision.stop_camera()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
