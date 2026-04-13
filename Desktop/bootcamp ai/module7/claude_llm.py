import os
import logging
from typing import Optional, Dict, Any


try:
    import anthropic
    from dotenv import load_dotenv
except ImportError:
    anthropic = None
    load_dotenv = None

class ClaudeResponse:
    """Wrapper to match the expected interface: .content"""
    def __init__(self, content: str):
        self.content = content

class ClaudeLLM:
    """
    Real Anthropic Claude LLM wrapper for INDUSTRIE IA.
    Compatible with business_plan_agent.py interface (.invoke(prompt))
    """
    
    def __init__(self, model: str = "claude-haiku-4-5-20251001", api_key: Optional[str] = None):
        # 0. Load .env file automatically
        if load_dotenv:
            load_dotenv()
        
        # 1. Verification of library
        if anthropic is None:
            raise ImportError("The 'anthropic' library is required. Run: pip install anthropic")
        
        # 2. Get API Key from environment variable as requested
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
        
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.logger = logging.getLogger("ClaudeLLM")

    def invoke(self, prompt: str) -> ClaudeResponse:
        """
        Executes a prompt via Claude API.
        Returns an object with a .content attribute.
        """
        try:
            self.logger.info(f"Calling Anthropic API (Model: {self.model})...")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # The official SDK returns a list of content blocks.
            # We extract the text from the first block.
            content_text = ""
            if message.content and len(message.content) > 0:
                content_text = message.content[0].text
            
            return ClaudeResponse(content_text)

        except Exception as e:
            self.logger.error(f"Claude API Error: {str(e)}")
            # Return a graceful error message inside the object to prevent agent crash
            return ClaudeResponse(f"Error during Claude invocation: {str(e)}")

# Agent 7 (Business Plan) - Claude AI Interface
# Final Production Version
