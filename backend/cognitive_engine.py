"""
CineMate Care - Cognitive Engine Module (Phase 2: "The Brain")

This module makes intelligent decisions about when and what the AI companion
should say, using Azure OpenAI GPT-4o for context-aware reasoning.

AZURE SERVICE USED: Azure OpenAI Service (GPT-4o)
- Endpoint: AZURE_OPENAI_ENDPOINT
- Model: GPT-4o (deployed as AZURE_OPENAI_DEPLOYMENT)
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# ============================================================================
# AZURE OPENAI SDK
# This SDK connects to Azure's hosted OpenAI models (GPT-4o, GPT-4, etc.)
# It provides the same capabilities as OpenAI but with Azure's enterprise features.
# ============================================================================
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM PROMPT - THE AI's PERSONALITY AND RULES
# This prompt defines how CineMate Care behaves as a companion.
# =============================================================================
CINEMATE_SYSTEM_PROMPT = """You are CineMate Care, a compassionate and observant cognitive companion for elderly users and those with visual impairments. You are watching a video/movie together with the user.

## YOUR CORE PURPOSE:
- Provide a sense of presence and reduce feelings of isolation
- Help the user understand and enjoy visual media
- Offer emotional support during difficult scenes
- Serve as a helpful memory aid for characters and plot points

## BEHAVIOR RULES (CRITICAL - FOLLOW EXACTLY):

1. **DO NOT INTERRUPT DIALOGUE**: 
   - If the audio_transcript contains ongoing speech, set should_speak to FALSE
   - Only speak during pauses, silence, or visual-only moments
   - Exception: The user explicitly asks you a question

2. **MATCH THE EMOTIONAL TONE**:
   - If the scene is sad: Be supportive ("This is a tough moment...")
   - If it's funny: Be light-hearted ("That was hilarious!")
   - If it's tense: Acknowledge it ("Things are getting intense...")
   - If it's heartwarming: Share the joy

3. **ACCESSIBILITY DESCRIPTIONS**:
   - Describe visual actions vividly but concisely
   - Focus on what matters: who did what, important objects, facial expressions
   - Example: "The villain just slipped a letter into his pocket while she wasn't looking"

4. **MEMORY AIDS**:
   - If a character reappears after a while, remind the user who they are
   - Reference earlier scenes when relevant
   - Example: "That's John, the baker from the first scene"

5. **SAFETY AWARENESS**:
   - If you detect distress words from the user (e.g., "help", "stop", "scared"), suggest taking a break
   - Always be gentle and never dismissive of emotions

## RESPONSE FORMAT:
You MUST respond with valid JSON only. No other text.
{
    "should_speak": true/false,
    "emotion": "empathetic|cheerful|calm|concerned|neutral",
    "content": "What you want to say to the user (if should_speak is true)",
    "reasoning": "Brief internal reasoning for your decision"
}

## TONE EXAMPLES:
- Warm: "Oh, that's such a lovely moment between them."
- Supportive: "I know this is hard to watch. Take your time."
- Helpful: "Just to catch you up - that's Maria, the one who helped the hero earlier."
- Cheerful: "Ha! I didn't see that coming. Classic comedy moment!"
"""


class CognitiveEngine:
    """
    Decision-making brain for CineMate Care using Azure OpenAI GPT-4o.
    
    This class analyzes the visual scene, audio transcript, and user context
    to determine:
    1. Whether the AI should speak (avoid interrupting dialogue)
    2. What emotion to convey
    3. What content to say
    
    AZURE SERVICE: Azure OpenAI Service
    - Model: GPT-4o (multi-modal large language model)
    - Purpose: Context-aware decision making and natural language generation
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None,
        deployment: Optional[str] = None
    ):
        """
        Initialize the Cognitive Engine with Azure OpenAI credentials.
        
        Args:
            endpoint: Azure OpenAI endpoint URL (or from env: AZURE_OPENAI_ENDPOINT)
            key: Azure OpenAI API key (or from env: AZURE_OPENAI_KEY)
            deployment: Deployed model name (or from env: AZURE_OPENAI_DEPLOYMENT)
        """
        # ====================================================================
        # AZURE OPENAI CLIENT INITIALIZATION
        # This client connects to Azure's hosted OpenAI service.
        # Requires: Endpoint, API Key, and Deployment name
        # ====================================================================
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.key = key or os.getenv("AZURE_OPENAI_KEY")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        
        if not self.endpoint or not self.key:
            raise ValueError(
                "Azure OpenAI credentials not found. "
                "Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY in .env file"
            )
        
        # Create the Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.key,
            api_version="2024-02-15-preview"  # Latest stable API version
        )
        
        logger.info(f"✅ Azure OpenAI client initialized (deployment: {self.deployment})")
        
        # Conversation history for context
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_length = 10  # Keep last 10 exchanges
        
        # Character memory for the movie being watched
        self.character_memory: Dict[str, str] = {}
    
    def analyze_context(
        self,
        scene_description: str,
        audio_transcript: str = "",
        user_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze the context and decide if/what the AI should say.
        
        AZURE SERVICE: Azure OpenAI - Chat Completions API
        - Model: GPT-4o
        - Purpose: Analyze scene, audio, and user context to generate appropriate response
        
        Args:
            scene_description: Visual description from Azure AI Vision
            audio_transcript: Recent dialogue/audio from the video
            user_history: Recent things the user has said
            
        Returns:
            Dict with keys:
            - should_speak: bool - Whether the AI should speak now
            - emotion: str - Emotional tone (empathetic, cheerful, calm, concerned, neutral)
            - content: str - What to say (if should_speak is True)
            - reasoning: str - Internal reasoning (for debugging)
        """
        # Build the context message for GPT-4o
        context_parts = []
        
        context_parts.append(f"## CURRENT SCENE DESCRIPTION (from Azure AI Vision):\n{scene_description}")
        
        if audio_transcript:
            context_parts.append(f"## RECENT AUDIO/DIALOGUE:\n{audio_transcript}")
        else:
            context_parts.append("## RECENT AUDIO/DIALOGUE:\n[Silent - no dialogue detected]")
        
        if user_history:
            context_parts.append(f"## USER'S RECENT COMMENTS:\n" + "\n".join(f"- {comment}" for comment in user_history[-5:]))
        else:
            context_parts.append("## USER'S RECENT COMMENTS:\n[No recent comments from user]")
        
        if self.character_memory:
            memory_text = "\n".join(f"- {name}: {desc}" for name, desc in self.character_memory.items())
            context_parts.append(f"## KNOWN CHARACTERS:\n{memory_text}")
        
        context_message = "\n\n".join(context_parts)
        context_message += "\n\n---\nBased on the above context, decide if you should speak now and what to say. Remember: DO NOT interrupt dialogue!"
        
        # ====================================================================
        # AZURE OPENAI API CALL - CHAT COMPLETIONS
        # This is the main API call that uses Azure OpenAI GPT-4o
        # The model analyzes the context and returns a structured decision
        # ====================================================================
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,  # This is the deployment name in Azure
                messages=[
                    {"role": "system", "content": CINEMATE_SYSTEM_PROMPT},
                    {"role": "user", "content": context_message}
                ],
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=300,   # Enough for a thoughtful response
                response_format={"type": "json_object"}  # Ensure JSON output
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            logger.debug(f"GPT-4o response: {response_text}")
            
            try:
                result = json.loads(response_text)
                
                # Validate required fields
                result.setdefault("should_speak", False)
                result.setdefault("emotion", "neutral")
                result.setdefault("content", "")
                result.setdefault("reasoning", "No reasoning provided")
                
                # Add metadata
                result["metadata"] = {
                    "azure_service": "Azure OpenAI Service (GPT-4o)",
                    "timestamp": datetime.now().isoformat(),
                    "model": self.deployment
                }
                
                if result["should_speak"]:
                    logger.info(f"🗣️ AI will speak: {result['content'][:50]}... (emotion: {result['emotion']})")
                else:
                    logger.debug(f"🤐 AI staying quiet. Reason: {result['reasoning'][:50]}...")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT-4o response as JSON: {e}")
                return self._fallback_response("JSON parsing error")
                
        except Exception as e:
            logger.error(f"❌ Azure OpenAI API error: {e}")
            return self._fallback_response(str(e))
    
    def _fallback_response(self, error_reason: str) -> Dict[str, Any]:
        """Generate a safe fallback response when API fails."""
        return {
            "should_speak": False,
            "emotion": "neutral",
            "content": "",
            "reasoning": f"Fallback due to error: {error_reason}",
            "metadata": {
                "azure_service": "Azure OpenAI Service (GPT-4o)",
                "timestamp": datetime.now().isoformat(),
                "error": True
            }
        }
    
    def add_character(self, name: str, description: str) -> None:
        """
        Add a character to the memory for context.
        
        Args:
            name: Character's name
            description: Brief description (role, appearance, etc.)
        """
        self.character_memory[name] = description
        logger.info(f"📝 Character added to memory: {name} - {description}")
    
    def detect_distress(self, user_text: str) -> bool:
        """
        Check if user's speech indicates distress.
        
        Args:
            user_text: What the user said
            
        Returns:
            bool: True if distress keywords detected
        """
        distress_keywords = [
            "help", "stop", "pause", "scared", "afraid", 
            "don't like", "too much", "overwhelming", "can't watch",
            "turn off", "feeling bad", "upset", "crying"
        ]
        
        user_lower = user_text.lower()
        for keyword in distress_keywords:
            if keyword in user_lower:
                logger.warning(f"⚠️ Distress keyword detected: '{keyword}'")
                return True
        return False
    
    def get_comfort_message(self) -> str:
        """Get a comforting message for when distress is detected."""
        return "I noticed you might be feeling overwhelmed. Would you like to take a break? We can pause the movie anytime you want."


# =============================================================================
# STANDALONE TEST MODE
# Run this file directly to test the Cognitive Engine
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("CineMate Care - Cognitive Engine Test")
    print("AZURE SERVICE: Azure OpenAI Service (GPT-4o)")
    print("=" * 60)
    
    # Initialize cognitive engine
    engine = CognitiveEngine()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Silent emotional scene",
            "scene": "A person sitting alone on a park bench, looking at an old photograph with tears in their eyes. The lighting is dim and melancholic.",
            "audio": "",
            "user": []
        },
        {
            "name": "Active dialogue",
            "scene": "Two people having an animated conversation at a coffee shop.",
            "audio": "Character A: 'I can't believe you did that!' Character B: 'What choice did I have?'",
            "user": []
        },
        {
            "name": "User asks question",
            "scene": "A man in a suit entering a large building.",
            "audio": "",
            "user": ["Who is that guy again?"]
        },
        {
            "name": "Funny moment",
            "scene": "A cat accidentally knocks over a vase while trying to catch a fly, looking surprised.",
            "audio": "[Slapstick comedy music plays]",
            "user": []
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'='*60}")
        print(f"Scene: {test['scene'][:80]}...")
        print(f"Audio: {test['audio'] or '[Silent]'}")
        print(f"User said: {test['user'] or '[Nothing]'}")
        
        result = engine.analyze_context(
            scene_description=test['scene'],
            audio_transcript=test['audio'],
            user_history=test['user'] if test['user'] else None
        )
        
        print(f"\n📊 Result:")
        print(f"  Should speak: {result['should_speak']}")
        print(f"  Emotion: {result['emotion']}")
        print(f"  Content: {result['content']}")
        print(f"  Reasoning: {result['reasoning']}")
    
    # Test distress detection
    print(f"\n{'='*60}")
    print("Distress Detection Test")
    print(f"{'='*60}")
    
    distress_tests = [
        "I'm feeling scared",
        "This is a great movie!",
        "Please help, I don't like this",
        "Can we stop for a moment?"
    ]
    
    for text in distress_tests:
        is_distress = engine.detect_distress(text)
        print(f"  '{text}' -> Distress: {is_distress}")
