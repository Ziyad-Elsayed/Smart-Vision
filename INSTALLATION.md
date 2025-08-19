# Vision Assistant Installation Guide

## Prerequisites

* Python 3.8 or higher
* Web camera
* Microphone
* Speakers or headphones
* Internet connection
* Gemini API key from Google AI Studio

## Installation Options

### Option 1: Install from Source (Recommended)

1. Clone or download the repository:
```bash
git clone https://github.com/yourusername/vision-assistant.git
cd vision-assistant
```

2. Run the installation script:
```bash
# Linux/macOS
python3 run.py

# Windows
python run.py
```

The script will check for dependencies and install them if needed.

### Option 2: Manual Installation

1. Clone or download the repository:
```bash
git clone https://github.com/yourusername/vision-assistant.git
cd vision-assistant
```

2. Create a virtual environment (optional but recommended):
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python main.py
```

## API Key Setup

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Go to "API Keys" section
4. Create a new API key
5. When you run the application for the first time, you'll be prompted to enter your API key

## Configuration

The application stores its configuration in:
- Linux/macOS: `~/.vision_assistant/config.ini`
- Windows: `C:\Users\<username>\.vision_assistant\config.ini`

### Manual Configuration

You can edit the configuration file directly:

```ini
[General]
first_run = false
last_run = 1715123456

[API]
api_key = YOUR_GEMINI_API_KEY
model = gemini-1.5-flash

[Speech]
voice_rate = 150
volume = 80
voice = 0

[Navigation]
process_interval = 5.0
auto_start = true
```

## Troubleshooting

### Missing Dependencies

If you encounter errors related to missing dependencies:

```bash
pip install -r requirements.txt
```

### PyAudio Installation Issues

PyAudio can be challenging to install on some systems:

#### Windows
```bash
pip install pipwin
pipwin install pyaudio
```

#### macOS
```bash
brew install portaudio
pip install pyaudio
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install python3-pyaudio
```

### Camera Access Issues

Ensure your camera is connected and not being used by another application.

You may need to grant camera permissions to Python/terminal:
- Windows: Allow access in Privacy Settings
- macOS: Allow access in System Preferences > Security & Privacy > Camera
- Linux: Various depending on distribution

### API Key Issues

If you get errors related to the API key:
1. Check if your API key is correctly entered in the config file
2. Verify that the API key is active in Google AI Studio
3. Ensure you have internet connectivity

## Running the Application

After successful installation, run the application:

```bash
# From the project directory
python run.py
```

The application will start and guide you through initial setup if it's your first time.
