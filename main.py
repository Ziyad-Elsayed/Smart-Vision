#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vision Assistant - Main Application

A Python application to help visually impaired individuals navigate
their environment and interact with the world around them using
AI-powered computer vision.
"""

import sys
import os
import time
import argparse
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QSplashScreen, QAction, QMenu,
    QStatusBar
)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal

# Make sure we can import modules from current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import application modules (using direct imports instead of 'from x import y')
import ui_components
import camera_manager
import speech_manager
import ai_processor
import utilities

# Application constants
APP_NAME = "Vision Assistant"
APP_VERSION = "1.0.0"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".vision_assistant", "config.ini")


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(800, 600)

        # Initialize configuration
        self.config_manager = utilities.ConfigManager(CONFIG_FILE)
        self.settings = self.config_manager.get_settings()

        # Check API key
        self.api_key = self.settings.get('api_key', '')
        if not self.api_key or self.api_key == "AIzaSyCRe8NU0N09-CddeW0C6BQayPlu2WwJ4CQ":
            self._show_api_key_dialog()

        # Initialize components
        self.init_components()
        self.setup_ui()
        self.connect_signals()

        # Start components
        self.start_components()

        # Show help on first run
        if self.settings.get('first_run', True):
            QTimer.singleShot(1000, self.show_help)
            self.settings['first_run'] = False
            self.config_manager.update_settings(self.settings)

    def init_components(self):
        """Initialize application components."""
        # Initialize speech manager
        self.speech_manager = speech_manager.SpeechManager(self._handle_speech_input)

        # Initialize camera manager
        self.camera_manager = camera_manager.CameraManager(self._handle_new_frame)

        # Initialize AI processor
        self.ai_processor = ai_processor.AIProcessor(self.api_key)

        # Application state
        self.current_mode = "navigation"
        self.last_process_time = 0
        self.process_interval = self.settings.get('process_interval', 5.0)

    def setup_ui(self):
        """Set up the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)

        # Camera view
        self.camera_view = ui_components.CameraView()
        self.camera_view.clicked.connect(self._handle_click)
        self.camera_view.double_clicked.connect(self._handle_double_click)
        self.camera_view.long_pressed.connect(self._handle_long_press)
        main_layout.addWidget(self.camera_view, 3)

        # Mode indicator
        self.mode_indicator = ui_components.ModeIndicator()
        main_layout.addWidget(self.mode_indicator)

        # Response display
        self.response_display = ui_components.ResponseDisplay()
        main_layout.addWidget(self.response_display, 1)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Create menu bar
        self.setup_menu()

    def setup_menu(self):
        """Set up the application menu."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Mode menu
        mode_menu = menu_bar.addMenu("&Mode")

        nav_action = QAction("&Navigation Mode", self)
        nav_action.triggered.connect(lambda: self.set_mode("navigation"))
        mode_menu.addAction(nav_action)

        assist_action = QAction("&Assistant Mode", self)
        assist_action.triggered.connect(lambda: self.set_mode("assistant"))
        mode_menu.addAction(assist_action)

        read_action = QAction("&Reading Mode", self)
        read_action.triggered.connect(lambda: self.set_mode("reading"))
        mode_menu.addAction(read_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        instructions_action = QAction("&Instructions", self)
        instructions_action.triggered.connect(self.show_help)
        help_menu.addAction(instructions_action)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def connect_signals(self):
        """Connect signals to slots."""
        # No additional signals to connect here
        pass

    def start_components(self):
        """Start all application components."""
        # Start speech manager
        self.speech_manager.start()

        # Start camera
        if not self.camera_manager.start():
            QMessageBox.warning(
                self, "Camera Error",
                "Failed to start camera. Please check your camera connection."
            )

        # Set initial mode
        self.set_mode("navigation")

        # Welcome message
        welcome_msg = f"Welcome to {APP_NAME}. You are in navigation mode."
        self.speech_manager.speak(welcome_msg)
        self.response_display.set_text(welcome_msg)

    def set_mode(self, mode):
        """
        Set the current application mode.

        Args:
            mode: New mode ("navigation", "assistant", or "reading")
        """
        if mode not in ["navigation", "assistant", "reading"]:
            return

        self.current_mode = mode
        self.ai_processor.set_mode(mode)
        self.mode_indicator.set_mode(mode)

        # Update status
        self.status_bar.showMessage(f"Mode: {mode.capitalize()}")

        # Handle mode-specific actions
        if mode == "navigation":
            self.speech_manager.recognizer.toggle_pause()  # Pause speech recognition
            self.speech_manager.speak("Navigation mode activated")
            self.response_display.set_text("Navigation mode activated. I'll describe your surroundings.")
        elif mode == "assistant":
            self.speech_manager.recognizer.toggle_pause()  # Enable speech recognition
            self.speech_manager.speak("Assistant mode activated. What would you like to know?")
            self.response_display.set_text("Assistant mode activated. Ask me anything about your surroundings.")
        elif mode == "reading":
            self.speech_manager.recognizer.toggle_pause()  # Pause speech recognition
            self.speech_manager.speak("Reading mode activated. Point camera at text.")
            self.response_display.set_text("Reading mode activated. Point camera at text to read.")
            # Process current frame immediately
            self._process_current_frame()

    def _handle_new_frame(self, frame):
        """
        Handle new camera frames.

        Args:
            frame: New camera frame
        """
        # Display the frame
        self.camera_view.display_frame(frame)

        # Process frame at intervals in navigation mode
        if self.current_mode == "navigation":
            current_time = time.time()
            if current_time - self.last_process_time >= self.process_interval:
                self._process_frame(frame)
                self.last_process_time = current_time

    def _process_frame(self, frame):
        """
        Process a camera frame with AI.

        Args:
            frame: Camera frame to process
        """
        self.status_bar.showMessage("Processing...")

        # Process the frame with AI
        self.ai_processor.process_frame(
            frame,
            None,  # No query in navigation mode
            self._handle_ai_result
        )

    def _process_current_frame(self):
        """Process the current camera frame."""
        frame = self.camera_manager.get_current_frame()
        if frame is not None:
            self._process_frame(frame)

    def _handle_ai_result(self, result):
        """
        Handle AI processing results.

        Args:
            result: Text result from AI
        """
        self.response_display.set_text(result)
        self.speech_manager.speak(result)
        self.status_bar.showMessage(f"Mode: {self.current_mode.capitalize()}")

    def _handle_speech_input(self, text):
        """
        Handle speech recognition input.

        Args:
            text: Recognized speech text
        """
        if not text:
            return

        if self.current_mode == "assistant":
            self.response_display.set_text(f"Query: {text}")
            frame = self.camera_manager.get_current_frame()
            if frame is not None:
                self.status_bar.showMessage("Processing...")
                self.ai_processor.process_frame(
                    frame,
                    text,  # Use the recognized speech as query
                    self._handle_ai_result
                )

    def _handle_click(self):
        """Handle single click event."""
        # Repeat last message
        current_text = self.response_display.text_label.text()
        if current_text and current_text != "Waiting for input...":
            self.speech_manager.speak(current_text)

    def _handle_double_click(self):
        """Handle double click event."""
        # Toggle between navigation and assistant modes
        if self.current_mode == "navigation":
            self.set_mode("assistant")
        else:
            self.set_mode("navigation")

    def _handle_long_press(self):
        """Handle long press event."""
        # Toggle between navigation and reading modes
        if self.current_mode == "navigation":
            self.set_mode("reading")
        else:
            self.set_mode("navigation")

    def _show_api_key_dialog(self):
        """Show dialog to get API key."""
        api_key = QMessageBox.question(
            self, "API Key Required",
            "This application requires a Gemini API key from Google AI Studio.\n\n"
            "Do you have an API key?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if api_key == QMessageBox.Yes:
            from PyQt5.QtWidgets import QInputDialog, QLineEdit
            key, ok = QInputDialog.getText(
                self, "Enter API Key",
                "Please enter your Gemini API key:",
                QLineEdit.Normal, ""
            )

            if ok and key:
                self.api_key = key
                self.settings['api_key'] = key
                self.config_manager.update_settings(self.settings)
                # Update AI processor with new key
                self.ai_processor = ai_processor.AIProcessor(self.api_key)
            else:
                QMessageBox.warning(
                    self, "API Key Required",
                    "A valid API key is required to use this application.\n"
                    "Please restart the application and enter your API key."
                )
                sys.exit(1)
        else:
            # Show instructions on getting an API key
            QMessageBox.information(
                self, "Get API Key",
                "To get a Gemini API key:\n\n"
                "1. Visit https://ai.google.dev/\n"
                "2. Sign in with your Google account\n"
                "3. Get an API key from the API Keys section\n\n"
                "The application will now exit. Please restart after obtaining an API key."
            )
            sys.exit(1)

    def show_settings(self):
        """Show settings dialog."""
        dialog = ui_components.SettingsDialog(self, self.settings)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.show()

    def _apply_settings(self, new_settings):
        """
        Apply new settings.

        Args:
            new_settings: Dictionary of new settings
        """
        # Update settings
        self.settings.update(new_settings)
        self.config_manager.update_settings(self.settings)

        # Apply speech settings
        self.speech_manager.configure(new_settings)

        # Apply process interval
        if 'process_interval' in new_settings:
            self.process_interval = new_settings['process_interval']

    def show_help(self):
        """Show help dialog."""
        dialog = ui_components.HelpDialog(self)
        dialog.show()

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h1>{APP_NAME} v{APP_VERSION}</h1>"
            "<p>An assistive application for visually impaired users.</p>"
            "<p>Uses computer vision and AI to help navigate and understand the world.</p>"
            "<p>Created with Python, PyQt, OpenCV, and Gemini AI.</p>"
            "<p>&copy; 2025 Your Name</p>"
            "<p>Licensed under MIT License</p>"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop all components
        self.speech_manager.stop()
        self.camera_manager.stop()

        # Save settings
        self.config_manager.update_settings(self.settings)

        # Accept the event
        event.accept()


def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        import PyQt5
        import cv2
        import numpy
        import speech_recognition
        import pyttsx3
        import google.generativeai

        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False


def main():
    """Application entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION}")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Check dependencies
    if not check_dependencies():
        print("Required dependencies are missing. Please install all required packages.")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

    # Check network connection
    if not utilities.NetworkChecker.is_connected():
        print("Warning: No network connection detected. The application requires internet access.")

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Show splash screen
    splash_screen = None
    try:
        splash_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "splash.png")
        if os.path.exists(splash_path):
            splash_pixmap = QPixmap(splash_path)
            if not splash_pixmap.isNull():
                splash_screen = QSplashScreen(splash_pixmap)
                splash_screen.show()
    except Exception as e:
        print(f"Could not load splash screen: {e}")
        # No splash screen available

    # Create and show main window
    main_window = MainWindow()

    # Hide splash screen and show main window
    if splash_screen:
        splash_screen.finish(main_window)

    main_window.show()

    # Start application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()