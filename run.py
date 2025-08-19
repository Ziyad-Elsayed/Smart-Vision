#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vision Assistant Launcher

This script checks requirements and launches the Vision Assistant application.
"""

import os
import sys
import subprocess
import platform
import shutil
import tempfile
from PIL import Image, ImageDraw, ImageFont

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Application info
APP_NAME = "Vision Assistant"
APP_VERSION = "1.0.0"

# Requirements
REQUIRED_PACKAGES = [
    "PyQt5>=5.15.0",
    "opencv-python>=4.7.0",
    "numpy>=1.23.0",
    "SpeechRecognition>=3.8.1",
    "pyttsx3>=2.90",
    "google-generativeai>=0.3.0",
    "Pillow>=9.0.0",
    "requests>=2.28.0",
    "PyAudio>=0.2.13",
]


def check_python_version():
    """Check if Python version is compatible."""
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"Error: {APP_NAME} requires Python 3.8 or higher")
        print(f"Current Python version: {platform.python_version()}")
        return False
    return True


def check_packages():
    """Check if required packages are installed."""
    import importlib
    import pkg_resources

    missing_packages = []

    for package_req in REQUIRED_PACKAGES:
        package_name = package_req.split(">=")[0]
        try:
            pkg_resources.require(package_req)
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            missing_packages.append(package_req)

    return missing_packages


def install_packages(packages):
    """Install missing packages."""
    print(f"Installing required packages for {APP_NAME}...")

    # Create a temporary requirements file
    fd, temp_path = tempfile.mkstemp(suffix='.txt')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write("\n".join(packages))

        # Install packages using pip
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", temp_path
        ])
    finally:
        os.unlink(temp_path)

    print("All required packages have been installed.")


def check_api_key():
    """Check if API key is configured."""
    config_dir = os.path.join(os.path.expanduser("~"), ".vision_assistant")
    config_file = os.path.join(config_dir, "config.ini")

    if not os.path.exists(config_file):
        return False

    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file)

        api_key = config.get("API", "api_key", fallback="")
        return api_key and api_key != "YOUR_GEMINI_API_KEY"
    except Exception:
        return False


def create_assets_directory():
    """Create assets directory if it doesn't exist."""
    assets_dir = os.path.join(current_dir, "assets")

    # Create assets directory if it doesn't exist
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)

    # Create __init__.py in assets directory
    init_file = os.path.join(assets_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# Assets package\n")

    # Create splash screen image if it doesn't exist
    splash_path = os.path.join(assets_dir, "splash.png")
    if not os.path.exists(splash_path):
        try:
            # Create a blank image
            img = Image.new('RGB', (600, 400), color=(53, 59, 72))
            d = ImageDraw.Draw(img)

            # Add text
            try:
                # Try to load a font, fall back to default if not available
                font = None
                try:
                    # Try common system fonts
                    system_fonts = [
                        "arial.ttf",
                        "Arial.ttf",
                        "/usr/share/fonts/TTF/arial.ttf",
                        "/usr/share/fonts/truetype/msttcorefonts/arial.ttf",
                        "/System/Library/Fonts/Helvetica.ttc"
                    ]
                    for font_path in system_fonts:
                        if os.path.exists(font_path):
                            font = ImageFont.truetype(font_path, 40)
                            break
                except Exception:
                    pass

                if font is None:
                    # Use default font if no system font is available
                    font = ImageFont.load_default()
            except Exception:
                # Fallback if we can't load any font
                font = None

            # Draw text
            text_color = (236, 240, 241)
            if font:
                d.text((300, 180), APP_NAME, fill=text_color, font=font, anchor="mm")
                d.text((300, 230), f"Version {APP_VERSION}", fill=text_color, font=font, anchor="mm")
            else:
                # Very basic approach if no font is available
                d.text((250, 180), APP_NAME, fill=text_color)
                d.text((250, 230), f"Version {APP_VERSION}", fill=text_color)

            # Save the image
            img.save(splash_path)
            print(f"Created splash screen at {splash_path}")

        except Exception as e:
            print(f"Warning: Failed to create splash screen: {e}")
            print("The application will run without a splash screen.")


def main():
    """Main entry point."""
    print(f"Starting {APP_NAME} v{APP_VERSION}...")

    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        sys.exit(1)

    # Check and install required packages
    try:
        missing_packages = check_packages()
        if missing_packages:
            print(f"Missing required packages: {', '.join(missing_packages)}")
            response = input("Do you want to install the missing packages? [Y/n]: ")
            if response.lower() in ("", "y", "yes"):
                install_packages(missing_packages)
            else:
                print("Cannot continue without required packages.")
                input("Press Enter to exit...")
                sys.exit(1)
    except Exception as e:
        print(f"Error checking packages: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Create assets directory
    create_assets_directory()

    # Create and check __init__.py file in main directory
    init_file = os.path.join(current_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# Vision Assistant package\n")

    # Start the application
    try:
        import main
        main.main()
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()