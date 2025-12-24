"""
CineMate Care - Vision Capture Module (Phase 1: "The Eyes")

This module handles webcam capture and scene analysis using Azure AI Vision.
It implements keyframe extraction to optimize API calls and reduce costs.

AZURE SERVICE USED: Azure AI Vision (Computer Vision 4.0)
- Endpoint: AZURE_VISION_ENDPOINT
- Features: VisualFeatures.CAPTION, VisualFeatures.DENSE_CAPTIONS
"""

import os
import cv2
import time
import json
import logging
import numpy as np
from io import BytesIO
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# ============================================================================
# AZURE AI VISION SDK
# This SDK connects to Azure's Computer Vision 4.0 service for image analysis.
# It provides advanced scene understanding, captioning, and object detection.
# ============================================================================
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

# For keyframe detection using Structural Similarity Index (SSIM)
from skimage.metrics import structural_similarity as ssim

# Retry logic for network resilience
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VisionCapture:
    """
    Webcam capture and Azure AI Vision integration for scene understanding.
    
    This class implements intelligent keyframe extraction to minimize API costs
    while ensuring important scene changes are captured and analyzed.
    
    AZURE SERVICE: Azure AI Vision (Computer Vision 4.0)
    - Used for: Scene captioning, dense captions (detailed region descriptions)
    - Cost optimization: Only analyzes frames that differ significantly from previous
    """
    
    def __init__(
        self,
        camera_index: int = 0,
        ssim_threshold: float = 0.95,  # High threshold = fewer API calls (was 0.85)
        max_interval_seconds: float = 15.0  # Analyze max every 15 seconds (was 5.0)
    ):
        """
        Initialize the Vision Capture module.
        
        Args:
            camera_index: Webcam index (0 = default camera)
            ssim_threshold: Similarity threshold for keyframe detection (0.0-1.0)
                           Lower = more sensitive to changes, Higher = fewer API calls
            max_interval_seconds: Maximum time between analyses (ensures periodic updates)
        """
        # ====================================================================
        # AZURE AI VISION CLIENT INITIALIZATION
        # This client connects to Azure's Computer Vision service.
        # Requires: AZURE_VISION_ENDPOINT and AZURE_VISION_KEY in environment
        # ====================================================================
        self.endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        self.key = os.getenv("AZURE_VISION_KEY")
        
        if not self.endpoint or not self.key:
            raise ValueError(
                "Azure Vision credentials not found. "
                "Please set AZURE_VISION_ENDPOINT and AZURE_VISION_KEY in .env file"
            )
        
        # Create the Azure AI Vision client
        self.vision_client = ImageAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
        logger.info("✅ Azure AI Vision client initialized successfully")
        
        # Webcam configuration
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        
        # Keyframe detection parameters
        self.ssim_threshold = ssim_threshold
        self.max_interval_seconds = max_interval_seconds
        
        # State tracking
        self.previous_frame_gray: Optional[np.ndarray] = None
        self.last_analysis_time: float = 0
        self.latest_caption: Optional[Dict[str, Any]] = None
        self.frame_count: int = 0
        self.analysis_count: int = 0
        
        # Camera stability - retry logic
        self.max_camera_retries: int = 3
        self.camera_retry_delay: float = 2.0  # seconds
        self.consecutive_failures: int = 0
        self.max_consecutive_failures: int = 10
    
    def start_camera(self) -> bool:
        """
        Initialize and start the webcam capture.
        
        Returns:
            bool: True if camera started successfully, False otherwise
        """
        for attempt in range(self.max_camera_retries):
            try:
                # Release any existing capture first
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except:
                        pass
                    self.cap = None
                    time.sleep(0.5)  # Give the camera time to release
                
                # Try DirectShow backend on Windows for better stability
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
                
                if not self.cap.isOpened():
                    # Fallback to default backend
                    self.cap = cv2.VideoCapture(self.camera_index)
                
                if not self.cap.isOpened():
                    logger.warning(f"⚠️ Failed to open camera (attempt {attempt + 1}/{self.max_camera_retries})")
                    if attempt < self.max_camera_retries - 1:
                        time.sleep(self.camera_retry_delay)
                        continue
                    return False
                
                # Set camera properties for optimal performance
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to prevent lag
                
                # Reset failure counter on successful start
                self.consecutive_failures = 0
                
                logger.info(f"📷 Camera started at index {self.camera_index}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Camera initialization error (attempt {attempt + 1}): {e}")
                if attempt < self.max_camera_retries - 1:
                    time.sleep(self.camera_retry_delay)
        
        return False
    
    def stop_camera(self) -> None:
        """Release the webcam resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info("📷 Camera stopped")
    
    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Capture a single frame from the webcam with auto-reconnection.
        
        Returns:
            Tuple of (success: bool, frame: numpy array or None)
        """
        if self.cap is None or not self.cap.isOpened():
            logger.warning("📷 Camera not available, attempting to reconnect...")
            if self.start_camera():
                logger.info("✅ Camera reconnected successfully")
            else:
                return False, None
        
        ret, frame = self.cap.read()
        
        if not ret:
            self.consecutive_failures += 1
            logger.warning(f"⚠️ Frame capture failed ({self.consecutive_failures}/{self.max_consecutive_failures})")
            
            if self.consecutive_failures >= self.max_consecutive_failures:
                logger.warning("📷 Too many failures, attempting camera reconnection...")
                if self.start_camera():
                    self.consecutive_failures = 0
                    # Try to get frame again after reconnection
                    ret, frame = self.cap.read()
                    if ret:
                        self.frame_count += 1
                        return True, frame
                return False, None
            
            # Small delay before next attempt
            time.sleep(0.1)
            return False, None
        
        # Reset failure counter on successful frame
        self.consecutive_failures = 0
        self.frame_count += 1
        return ret, frame
    
    def is_keyframe(self, current_frame: np.ndarray) -> bool:
        """
        Determine if the current frame is a 'keyframe' worth analyzing.
        
        A frame is considered a keyframe if:
        1. It's the first frame (no previous frame to compare)
        2. It's significantly different from the previous frame (SSIM < threshold)
        3. More than max_interval_seconds have passed since last analysis
        
        This logic saves Azure API costs by only analyzing meaningful changes.
        
        Args:
            current_frame: Current BGR frame from webcam
            
        Returns:
            bool: True if this frame should be sent to Azure AI Vision
        """
        current_time = time.time()
        
        # Convert to grayscale for SSIM comparison
        current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        
        # Case 1: First frame - always analyze
        if self.previous_frame_gray is None:
            self.previous_frame_gray = current_gray
            self.last_analysis_time = current_time
            logger.debug("🎬 First frame - marking as keyframe")
            return True
        
        # Case 2: Time-based trigger (ensures periodic updates)
        time_since_last = current_time - self.last_analysis_time
        if time_since_last >= self.max_interval_seconds:
            self.previous_frame_gray = current_gray
            self.last_analysis_time = current_time
            logger.debug(f"⏰ Time threshold reached ({time_since_last:.1f}s) - marking as keyframe")
            return True
        
        # Case 3: Content-based trigger using SSIM
        # SSIM (Structural Similarity Index) measures image similarity (0-1)
        # Lower SSIM = more different, Higher SSIM = more similar
        try:
            similarity = ssim(self.previous_frame_gray, current_gray)
            
            if similarity < self.ssim_threshold:
                self.previous_frame_gray = current_gray
                self.last_analysis_time = current_time
                logger.debug(f"🔄 Scene change detected (SSIM: {similarity:.3f}) - marking as keyframe")
                return True
        except Exception as e:
            logger.warning(f"SSIM calculation error: {e}")
            return False
        
        return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"🔄 Retrying Azure Vision API call (attempt {retry_state.attempt_number})..."
        )
    )
    def analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Send a frame to Azure AI Vision for analysis.
        
        AZURE SERVICE: Azure AI Vision - Image Analysis API
        - VisualFeatures.CAPTION: Single sentence describing the entire image
        - VisualFeatures.DENSE_CAPTIONS: Multiple captions for different regions
        
        This method includes retry logic for network resilience.
        
        Args:
            frame: BGR frame from webcam (numpy array)
            
        Returns:
            Dict with timestamp, caption, dense_captions, and confidence scores
        """
        # ====================================================================
        # AZURE AI VISION API CALL
        # We encode the frame as JPEG and send it to Azure for analysis.
        # The service returns natural language descriptions of the scene.
        # ====================================================================
        
        # Encode frame as JPEG for API transmission
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_data = BytesIO(buffer.tobytes())
        
        try:
            # Call Azure AI Vision API
            # Using TAGS, OBJECTS, and PEOPLE features for comprehensive detection
            result = self.vision_client.analyze(
                image_data=image_data,
                visual_features=[
                    VisualFeatures.TAGS,    # Scene elements and objects
                    VisualFeatures.OBJECTS, # Detected objects with locations
                    VisualFeatures.PEOPLE   # People detection with bounding boxes
                ]
            )
            
            self.analysis_count += 1
            
            # Build response structure
            # Convert tags to a natural language caption
            tags_list = []
            if result.tags is not None:
                tags_list = [tag.name for tag in result.tags.list if tag.confidence > 0.5]
            
            objects_list = []
            object_counts = {}  # Track count of each object type
            if result.objects is not None:
                for obj in result.objects.list:
                    if obj.tags:
                        obj_name = obj.tags[0].name
                        objects_list.append(obj_name)
                        object_counts[obj_name] = object_counts.get(obj_name, 0) + 1
            
            # Count people detected
            people_count = 0
            people_details = []
            if result.people is not None and result.people.list:
                people_count = len(result.people.list)
                for person in result.people.list:
                    people_details.append({
                        "confidence": person.confidence,
                        "bounding_box": {
                            "x": person.bounding_box.x,
                            "y": person.bounding_box.y,
                            "width": person.bounding_box.width,
                            "height": person.bounding_box.height
                        }
                    })
            
            # Build descriptive caption with person count
            caption_parts = []
            if people_count > 0:
                caption_parts.append(f"{people_count} person{'s' if people_count > 1 else ''} detected")
            
            # Add other object counts
            for obj_name, count in object_counts.items():
                if obj_name.lower() != 'person':
                    if count > 1:
                        caption_parts.append(f"{count} {obj_name}s")
                    else:
                        caption_parts.append(obj_name)
            
            # Add remaining unique elements from tags
            all_elements = list(set(tags_list) - set(objects_list))[:5]
            caption_parts.extend(all_elements)
            
            caption_text = f"Scene: {', '.join(caption_parts[:8])}" if caption_parts else "Scene analysis in progress"
            
            response = {
                "timestamp": datetime.now().isoformat(),
                "frame_number": self.frame_count,
                "analysis_number": self.analysis_count,
                "caption": {
                    "text": caption_text,
                    "confidence": 0.85
                },
                "people_count": people_count,
                "people_details": people_details,
                "tags": tags_list,
                "objects": objects_list,
                "object_counts": object_counts,
                "dense_captions": [],
                "metadata": {
                    "azure_service": "Azure AI Vision (Computer Vision 4.0)",
                    "features_used": ["TAGS", "OBJECTS", "PEOPLE"],
                    "region_fallback": False
                }
            }
            
            logger.info(f"👥 People: {people_count} | 📝 Tags: {', '.join(tags_list[:5])}...")
            
            self.latest_caption = response
            return response
            
        except Exception as e:
            logger.error(f"❌ Azure Vision API error: {e}")
            raise
    
    def get_latest_caption(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent caption from Azure AI Vision.
        
        Returns:
            Dict with caption data or None if no analysis has been performed
        """
        return self.latest_caption
    
    def process_frame(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Process a frame: check if it's a keyframe and analyze if needed.
        
        This is the main entry point for the vision pipeline. It combines
        keyframe detection and Azure AI Vision analysis.
        
        Args:
            frame: BGR frame from webcam
            
        Returns:
            Dict with caption if frame was analyzed, None otherwise
        """
        if self.is_keyframe(frame):
            try:
                return self.analyze_frame(frame)
            except Exception as e:
                logger.error(f"Frame analysis failed: {e}")
                return None
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get capture and analysis statistics."""
        return {
            "frames_captured": self.frame_count,
            "frames_analyzed": self.analysis_count,
            "analysis_ratio": f"{(self.analysis_count / max(1, self.frame_count)) * 100:.1f}%",
            "latest_caption": self.latest_caption
        }


# =============================================================================
# STANDALONE TEST MODE
# Run this file directly to test webcam capture and Azure Vision integration
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("CineMate Care - Vision Capture Test")
    print("AZURE SERVICE: Azure AI Vision (Computer Vision 4.0)")
    print("=" * 60)
    
    # Initialize vision capture
    vision = VisionCapture()
    
    if not vision.start_camera():
        print("Failed to start camera. Exiting.")
        exit(1)
    
    print("\n📷 Camera started. Press 'q' to quit.\n")
    
    try:
        while True:
            ret, frame = vision.get_frame()
            if not ret:
                print("Failed to capture frame")
                break
            
            # Process frame (keyframe detection + Azure analysis)
            result = vision.process_frame(frame)
            
            if result:
                print(f"\n📊 Analysis Result:")
                print(json.dumps(result, indent=2))
            
            # Display frame with overlay
            display_frame = frame.copy()
            caption_text = "Waiting for scene change..."
            if vision.latest_caption and vision.latest_caption.get("caption"):
                caption_text = vision.latest_caption["caption"]["text"]
            
            # Add caption overlay
            cv2.putText(
                display_frame, 
                caption_text[:80],  # Truncate long captions
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 255, 0), 
                2
            )
            
            # Add stats overlay
            stats = vision.get_stats()
            cv2.putText(
                display_frame,
                f"Frames: {stats['frames_captured']} | Analyzed: {stats['frames_analyzed']}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                1
            )
            
            cv2.imshow('CineMate Care - Vision Test', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n\n⚡ Interrupted by user")
    
    finally:
        vision.stop_camera()
        cv2.destroyAllWindows()
        
        print("\n" + "=" * 60)
        print("📊 Final Statistics:")
        print(json.dumps(vision.get_stats(), indent=2, default=str))
        print("=" * 60)
