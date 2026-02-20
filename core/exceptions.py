# Custom domain exceptions for the Honeypot API

class AIProcessingError(Exception):
    """Exception raised for errors during AI/Gemini interaction (Detection or Extraction)."""
    def __init__(self, message="An error occurred while communicating with the AI Engine"):
        self.message = message
        super().__init__(self.message)

class PersonaGenerationError(AIProcessingError):
    """Exception raised specifically when the Persona Engine fails to generate a reply."""
    def __init__(self, message="Failed to generate persona reply"):
        self.message = message
        super().__init__(self.message)
