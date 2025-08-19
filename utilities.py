import os
import json
import configparser
import time
from typing import Dict, Any, Optional
import cv2
import numpy as np


class ConfigManager:
    """Manages application configuration and settings."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_file: Path to configuration file, or None to use default
        """
        if config_file is None:
            # Default config location
            home_dir = os.path.expanduser("~")
            config_dir = os.path.join(home_dir, ".vision_assistant")

            # Create config directory if it doesn't exist
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            self.config_file = os.path.join(config_dir, "config.ini")
        else:
            self.config_file = config_file

        self.config = configparser.ConfigParser()

        # Create default config if it doesn't exist
        if not os.path.exists(self.config_file):
            self._create_default_config()
        else:
            self.config.read(self.config_file)

    def _create_default_config(self):
        """Create a default configuration file."""
        self.config["General"] = {
            "first_run": "true",
            "last_run": str(int(time.time()))
        }

        self.config["API"] = {
            "api_key": "YOUR_GEMINI_API_KEY",
            "model": "gemini-1.5-flash"
        }

        self.config["Speech"] = {
            "voice_rate": "150",
            "volume": "80",
            "voice": "0"
        }

        self.config["Navigation"] = {
            "process_interval": "5.0",
            "auto_start": "true"
        }

        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a value from the configuration.

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found

        Returns:
            The configuration value or default
        """
        try:
            return self.config[section][key]
        except (KeyError, configparser.NoSectionError):
            return default

    def set_value(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        # Create section if it doesn't exist
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = str(value)

    def save(self) -> None:
        """Save the configuration to file."""
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_settings(self) -> Dict[str, Any]:
        """
        Get all settings as a dictionary.

        Returns:
            Dictionary of settings
        """
        settings = {}

        # API settings
        settings['api_key'] = self.get_value('API', 'api_key', '')
        settings['model'] = self.get_value('API', 'model', 'gemini-1.5-flash')

        # Speech settings
        settings['voice_rate'] = int(self.get_value('Speech', 'voice_rate', 150))
        settings['volume'] = int(self.get_value('Speech', 'volume', 80))
        settings['voice'] = int(self.get_value('Speech', 'voice', 0))

        # Navigation settings
        settings['process_interval'] = float(self.get_value('Navigation', 'process_interval', 5.0))
        settings['auto_start'] = self.get_value('Navigation', 'auto_start', 'true').lower() == 'true'

        # General settings
        settings['first_run'] = self.get_value('General', 'first_run', 'true').lower() == 'true'

        return settings

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update settings from a dictionary.

        Args:
            settings: Dictionary of settings to update
        """
        # API settings
        if 'api_key' in settings:
            self.set_value('API', 'api_key', settings['api_key'])
        if 'model' in settings:
            self.set_value('API', 'model', settings['model'])

        # Speech settings
        if 'voice_rate' in settings:
            self.set_value('Speech', 'voice_rate', settings['voice_rate'])
        if 'volume' in settings:
            self.set_value('Speech', 'volume', settings['volume'])
        if 'voice' in settings:
            self.set_value('Speech', 'voice', settings['voice'])

        # Navigation settings
        if 'process_interval' in settings:
            self.set_value('Navigation', 'process_interval', settings['process_interval'])
        if 'auto_start' in settings:
            self.set_value('Navigation', 'auto_start', 'true' if settings['auto_start'] else 'false')

        # General settings
        if 'first_run' in settings:
            self.set_value('General', 'first_run', 'true' if settings['first_run'] else 'false')

        # Always update last run time
        self.set_value('General', 'last_run', str(int(time.time())))

        # Save changes
        self.save()


class ImageProcessor:
    """Helper class for image processing tasks."""

    @staticmethod
    def resize_image(image: np.ndarray, max_width: int = 1024) -> np.ndarray:
        """
        Resize image while preserving aspect ratio.

        Args:
            image: OpenCV image
            max_width: Maximum width

        Returns:
            Resized image
        """
        height, width = image.shape[:2]

        if width <= max_width:
            return image

        scale = max_width / width
        new_height = int(height * scale)

        return cv2.resize(image, (max_width, new_height), interpolation=cv2.INTER_AREA)

    @staticmethod
    def enhance_for_text_recognition(image: np.ndarray) -> np.ndarray:
        """
        Enhance image for better text recognition.

        Args:
            image: OpenCV image

        Returns:
            Enhanced image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Apply morphological operations to clean the image
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        return opening

    @staticmethod
    def detect_edges(image: np.ndarray) -> np.ndarray:
        """
        Detect edges in an image for obstacle detection.

        Args:
            image: OpenCV image

        Returns:
            Edge map
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)

        return edges

    @staticmethod
    def extract_text_regions(image: np.ndarray) -> list:
        """
        Extract potential text regions from an image.

        Args:
            image: OpenCV image

        Returns:
            List of (x, y, w, h) coordinates for potential text regions
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter contours based on size and aspect ratio
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            area = w * h

            # Filter based on size and aspect ratio
            if area > 200 and 0.1 < aspect_ratio < 10:
                text_regions.append((x, y, w, h))

        return text_regions


class NetworkChecker:
    """Utility to check network connectivity."""

    @staticmethod
    def is_connected() -> bool:
        """
        Check if network is available.

        Returns:
            True if connected, False otherwise
        """
        try:
            # Try to connect to Google DNS
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    @staticmethod
    def check_api_key(api_key: str) -> bool:
        """
        Check if API key is valid.

        Args:
            api_key: API key to check

        Returns:
            True if valid, False otherwise
        """
        if not api_key or api_key == "YOUR_GEMINI_API_KEY":
            return False

        # Import here to avoid circular import
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            # Try a simple API call
            models = genai.list_models()
            return len(models) > 0
        except Exception:
            return False