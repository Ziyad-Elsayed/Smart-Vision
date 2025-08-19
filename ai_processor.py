import os
import time
import threading
import queue
from typing import Optional, Tuple, List, Dict, Any
import io
from PIL import Image
import numpy as np
import cv2

# Try to import Google Generative AI, but handle import errors gracefully
try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel

    GENAI_AVAILABLE = True
except ImportError:
    print("Warning: google.generativeai module not available. AI features will be limited.")
    GENAI_AVAILABLE = False


class AIProcessor:
    """Handles all AI processing tasks for the Vision Assistant application."""

    def __init__(self, api_key: str):
        """Initialize the AI processor with API key and configuration."""
        self.api_key = api_key
        self.setup_model()
        self.task_queue = queue.Queue()
        self.result_callbacks = {}
        self.current_mode = "navigation"
        self.last_processed_time = time.time()
        self.process_interval = 5.0  # seconds between processing in navigation mode
        self.processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.running = True
        self.processing_thread.start()

        # Prompt templates for different modes
        self.prompts = {
            "navigation": """
            You are a navigation assistant for visually impaired users. Analyze this image and provide:

            1. A brief description of the environment (indoor/outdoor, type of space)
            2. Identification of obstacles or hazards in the path
            3. Clear, simple navigation guidance
            4. Important objects, their colors, and relative positions

            Keep your response to 3-4 short sentences, prioritizing safety information.
            Use directional terms like "in front", "to your left", "ahead", etc.
            """,

            "reading": """
            Your task is to accurately read and transcribe ALL text visible in this image.
            Present the text in a logical reading order.
            If there are multiple text elements (signs, headers, paragraphs), organize them clearly.
            If text is partially visible or unclear, indicate this with [unclear] or make your best guess.
            If no text is visible, state "No text detected in the image."
            """,

            "assistant": """
            You are an AI assistant for a visually impaired person who is showing you what they can see through their camera.
            The user has asked: "{query}"

            Analyze the image and provide a helpful, detailed response to their question.
            Focus on visual elements relevant to their query.
            Describe colors, positions, and other visual details accurately.
            If you cannot answer their question based on the visible information, explain why.
            """
        }

    def setup_model(self):
        """Configure and initialize the Gemini model."""
        if not GENAI_AVAILABLE:
            print("Warning: Cannot initialize Gemini model (module not available)")
            self.model = None
            return

        try:
            # استخدام مفتاح API مباشرة هنا
            api_key = "AIzaSyCRe8NU0N09-CddeW0C6BQayPlu2WwJ4CQ"
            genai.configure(api_key=api_key)
            self.model = GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 1024,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            self.model = None

    def set_mode(self, mode: str):
        """Change the current operating mode."""
        self.current_mode = mode

    def process_frame(self, frame: np.ndarray, query: Optional[str] = None, callback=None):
        """
        Add a frame to the processing queue.

        Args:
            frame: The camera frame to process
            query: Optional text query (for assistant mode)
            callback: Function to call with results
        """
        # Skip if we're in navigation mode and not enough time has elapsed
        current_time = time.time()
        if (self.current_mode == "navigation" and
                (current_time - self.last_processed_time) < self.process_interval):
            return False

        task_id = str(current_time)
        if callback:
            self.result_callbacks[task_id] = callback

        self.task_queue.put((task_id, frame, query))

        if self.current_mode == "navigation":
            self.last_processed_time = current_time

        return True

    def _process_queue(self):
        """Worker thread that processes the queue of frames."""
        while self.running:
            try:
                if self.task_queue.empty():
                    time.sleep(0.1)
                    continue

                task_id, frame, query = self.task_queue.get()

                # If Gemini is not available, provide a fallback response
                if not GENAI_AVAILABLE or self.model is None:
                    fallback_msg = self._generate_fallback_response(self.current_mode, query)
                    if task_id in self.result_callbacks:
                        self.result_callbacks[task_id](fallback_msg)
                        del self.result_callbacks[task_id]
                    self.task_queue.task_done()
                    continue

                # Convert OpenCV frame to PIL Image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)

                # Create in-memory JPEG to send to API
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='JPEG', quality=85)
                img_byte_arr.seek(0)

                # Format prompt based on mode
                if self.current_mode == "assistant" and query:
                    prompt = self.prompts["assistant"].format(query=query)
                else:
                    prompt = self.prompts[self.current_mode]

                # Send to Gemini API
                try:
                    response = self.model.generate_content([prompt, pil_image])
                    result = response.text
                except Exception as e:
                    print(f"Error generating content: {e}")
                    result = f"Sorry, I encountered an error processing the image: {str(e)}"

                # Call callback if registered
                if task_id in self.result_callbacks:
                    self.result_callbacks[task_id](result)
                    del self.result_callbacks[task_id]

                self.task_queue.task_done()

            except Exception as e:
                print(f"Error in AI processing: {e}")

                if task_id in self.result_callbacks:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    self.result_callbacks[task_id](error_msg)
                    del self.result_callbacks[task_id]

                self.task_queue.task_done()

    def _generate_fallback_response(self, mode: str, query: Optional[str] = None) -> str:
        """Generate a fallback response when Gemini is not available."""
        if mode == "navigation":
            return "Unable to analyze the environment. Gemini API is not available. Please check your internet connection and API key."
        elif mode == "reading":
            return "Unable to read text from the image. Gemini API is not available. Please check your internet connection and API key."
        elif mode == "assistant":
            if query:
                return f"I cannot answer your question '{query}' because the Gemini API is not available. Please check your internet connection and API key."
            else:
                return "Unable to process your request. Gemini API is not available and no question was provided."
        else:
            return "Unsupported mode. Please try again with a valid mode."

    def shutdown(self):
        """Clean shutdown of the processing thread."""
        self.running = False
        if self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)