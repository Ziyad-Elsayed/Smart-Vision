# Vision Assistant

![Vision Assistant Logo](assets/vision_assistant_logo.png)

## Overview

Vision Assistant is a Python-based application designed to help visually impaired individuals navigate their environment and interact with the world around them using AI-powered computer vision and natural language processing.

## Features

### 🧭 Navigation Mode
- Real-time analysis of surroundings
- Obstacle detection and avoidance guidance
- Environment description (indoor/outdoor detection)
- Path finding and orientation assistance
- Object identification with color and size description

### 💬 Assistant Mode
- Ask questions about your surroundings
- Get information about specific objects
- Understand spatial relationships between objects
- Query about text visible in the environment
- General knowledge assistance

### 📖 Reading Mode
- Text detection and recognition from images
- Document reading (books, papers, mail)
- Sign reading (street signs, store names, warnings)
- Package label and instruction reading
- Support for multiple languages

## Installation

### Prerequisites
- Python 3.8 or higher
- Camera (webcam for desktop/laptop)
- Microphone
- Speakers or headphones
- Internet connection for AI processing

### Install from PyPI
```bash
pip install vision-assistant
```

### Install from source
```bash
git clone https://github.com/yourusername/vision-assistant.git
cd vision-assistant
pip install -e .
```

### API Key Setup
1. Get a Gemini API key from [Google AI Studio](https://ai.google.dev)
2. Add your API key to the configuration file:
   - During first run, the application will create a configuration file at `~/.vision_assistant/config.ini`
   - Edit this file and replace `YOUR_GEMINI_API_KEY` with your actual API key

## Usage

### Starting the Application
```bash
vision-assistant
```

### Gesture Controls
- **Double Tap**: Switch between Navigation and Assistant modes
- **Long Press**: Switch between Navigation and Reading modes
- **Shake Device**: Return to Navigation mode from any other mode
- **Swipe Up with Two Fingers**: Repeat last announcement
- **Swipe Down with Two Fingers**: Pause/Resume announcements

### Voice Commands
While in Assistant mode, you can ask questions such as:
- "What objects are in front of me?"
- "Is there a chair nearby?"
- "What color is the car?"
- "Read the sign ahead"
- "Describe my surroundings"

## Development

### Project Structure
```
vision_assistant/
├── main.py                 # Main application entry point
├── camera_manager.py       # Camera input handling
├── speech_manager.py       # Speech recognition and TTS
├── ai_processor.py         # AI processing with Gemini
├── ui/
│   ├── main_window.py      # Main UI components
│   ├── help_screen.py      # Tutorial screens
│   └── indicators.py       # Visual status indicators
└── utils/
    ├── config.py           # Configuration handling
    ├── image_utils.py      # Image processing utilities
    └── gestures.py         # Gesture detection
```

### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini API for powerful AI capabilities
- The open-source community for providing excellent libraries
- Feedback from visually impaired users that helped shape this application
