import sys
import os
import time
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QSlider, QComboBox,
    QApplication, QMessageBox, QSplashScreen
)
from PyQt5.QtGui import QFont, QPixmap, QImage, QIcon, QPainter, QColor
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QThread, QEvent
import cv2
import numpy as np


class ModeIndicator(QWidget):
    """Custom widget that shows the current mode with colored indicators."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.current_mode = "navigation"

    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)

        # Create mode labels
        self.nav_label = QLabel("NAVIGATION")
        self.nav_label.setAlignment(Qt.AlignCenter)
        self.nav_label.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; "
            "padding: 8px; border-radius: 5px;"
        )

        self.assist_label = QLabel("ASSISTANT")
        self.assist_label.setAlignment(Qt.AlignCenter)
        self.assist_label.setStyleSheet(
            "background-color: #9E9E9E; color: white; font-weight: bold; "
            "padding: 8px; border-radius: 5px;"
        )

        self.read_label = QLabel("READING")
        self.read_label.setAlignment(Qt.AlignCenter)
        self.read_label.setStyleSheet(
            "background-color: #9E9E9E; color: white; font-weight: bold; "
            "padding: 8px; border-radius: 5px;"
        )

        layout.addWidget(self.nav_label)
        layout.addWidget(self.assist_label)
        layout.addWidget(self.read_label)

    def set_mode(self, mode):
        """Update the indicator to show the current mode."""
        self.current_mode = mode

        # Reset all to inactive
        self.nav_label.setStyleSheet(
            "background-color: #9E9E9E; color: white; font-weight: bold; "
            "padding: 8px; border-radius: 5px;"
        )
        self.assist_label.setStyleSheet(
            "background-color: #9E9E9E; color: white; font-weight: bold; "
            "padding: 8px; border-radius: 5px;"
        )
        self.read_label.setStyleSheet(
            "background-color: #9E9E9E; color: white; font-weight: bold; "
            "padding: 8px; border-radius: 5px;"
        )

        # Set active mode
        if mode == "navigation":
            self.nav_label.setStyleSheet(
                "background-color: #4CAF50; color: white; font-weight: bold; "
                "padding: 8px; border-radius: 5px;"
            )
        elif mode == "assistant":
            self.assist_label.setStyleSheet(
                "background-color: #2196F3; color: white; font-weight: bold; "
                "padding: 8px; border-radius: 5px;"
            )
        elif mode == "reading":
            self.read_label.setStyleSheet(
                "background-color: #FF9800; color: white; font-weight: bold; "
                "padding: 8px; border-radius: 5px;"
            )


class CameraView(QLabel):
    """Widget that displays the camera feed and handles gestures."""

    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    long_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 480)
        self.setStyleSheet("background-color: black;")

        # Gesture tracking
        self.press_start_time = 0
        self.last_click_time = 0
        self.long_press_threshold = 800  # ms
        self.double_click_threshold = 300  # ms
        self.touch_timer = QTimer(self)
        self.touch_timer.setSingleShot(True)
        self.touch_timer.timeout.connect(self._emit_long_press)

    def mousePressEvent(self, event):
        """Handle mouse press events for gesture detection."""
        if event.button() == Qt.LeftButton:
            self.press_start_time = time.time() * 1000
            self.touch_timer.start(self.long_press_threshold)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for gesture detection."""
        if event.button() == Qt.LeftButton:
            self.touch_timer.stop()

            # Calculate elapsed time
            elapsed = time.time() * 1000 - self.press_start_time

            # Skip if it was a long press (already handled by timer)
            if elapsed >= self.long_press_threshold:
                return

            # Check for double click
            if (time.time() * 1000 - self.last_click_time) < self.double_click_threshold:
                self.double_clicked.emit()
                self.last_click_time = 0  # Reset to prevent triple click
            else:
                self.clicked.emit()
                self.last_click_time = time.time() * 1000

    def _emit_long_press(self):
        """Emit long press signal when timer times out."""
        self.long_pressed.emit()

    def display_frame(self, frame):
        """Display a camera frame in the view."""
        if frame is None:
            return

        # Convert OpenCV frame to QPixmap
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        # Scale to fit widget while preserving aspect ratio
        self.setPixmap(pixmap.scaled(
            self.width(), self.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))


class ResponseDisplay(QFrame):
    """Widget that displays the AI responses with styling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.7); border-radius: 10px; "
            "color: white; padding: 15px;"
        )
        self.setMinimumHeight(120)

        self.layout = QVBoxLayout(self)

        self.text_label = QLabel("Waiting for input...")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("font-size: 16px; background-color: transparent;")

        self.layout.addWidget(self.text_label)

    def set_text(self, text):
        """Update the displayed text."""
        self.text_label.setText(text)

    def highlight_text(self, highlight=True):
        """Highlight the text to indicate it's being spoken."""
        if highlight:
            self.setStyleSheet(
                "background-color: rgba(33, 150, 243, 0.7); border-radius: 10px; "
                "color: white; padding: 15px;"
            )
        else:
            self.setStyleSheet(
                "background-color: rgba(0, 0, 0, 0.7); border-radius: 10px; "
                "color: white; padding: 15px;"
            )


class SettingsDialog(QWidget):
    """Dialog for adjusting application settings."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Settings")
        self.setMinimumSize(400, 300)

        if current_settings is None:
            current_settings = {
                'voice_rate': 150,
                'process_interval': 5.0,
                'volume': 80,
                'voice': 0
            }

        self.current_settings = current_settings
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Voice rate slider
        layout.addWidget(QLabel("Speech Rate:"))
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setMinimum(50)
        self.rate_slider.setMaximum(300)
        self.rate_slider.setValue(self.current_settings.get('voice_rate', 150))
        self.rate_slider.setTickPosition(QSlider.TicksBelow)
        self.rate_slider.setTickInterval(50)
        layout.addWidget(self.rate_slider)

        # Voice volume slider
        layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self.current_settings.get('volume', 80))
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.setTickInterval(10)
        layout.addWidget(self.volume_slider)

        # Processing interval slider (for navigation mode)
        layout.addWidget(QLabel("Navigation Update Interval (seconds):"))
        self.interval_slider = QSlider(Qt.Horizontal)
        self.interval_slider.setMinimum(1)
        self.interval_slider.setMaximum(10)
        self.interval_slider.setValue(int(self.current_settings.get('process_interval', 5.0)))
        self.interval_slider.setTickPosition(QSlider.TicksBelow)
        self.interval_slider.setTickInterval(1)
        layout.addWidget(self.interval_slider)

        # Voice selection
        layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["Default", "Male", "Female"])
        self.voice_combo.setCurrentIndex(self.current_settings.get('voice', 0))
        layout.addWidget(self.voice_combo)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

    def save_settings(self):
        """Save the current settings and emit signal."""
        settings = {
            'voice_rate': self.rate_slider.value(),
            'process_interval': float(self.interval_slider.value()),
            'volume': self.volume_slider.value(),
            'voice': self.voice_combo.currentIndex()
        }

        self.settings_changed.emit(settings)
        self.hide()


class HelpDialog(QWidget):
    """Help dialog with instructions on using the application."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("How to Use Vision Assistant")
        self.setMinimumSize(500, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Vision Assistant Help")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Tab widget for different help sections
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Gesture controls tab
        gesture_tab = QWidget()
        gesture_layout = QVBoxLayout(gesture_tab)
        gesture_text = QLabel(
            "<b>Double Tap:</b> Switch between Navigation and Assistant modes<br><br>"
            "<b>Long Press:</b> Switch between Navigation and Reading modes<br><br>"
            "<b>Single Tap:</b> Repeat last announcement<br><br>"
            "<b>Shake Device:</b> Return to Navigation mode"
        )
        gesture_text.setWordWrap(True)
        gesture_layout.addWidget(gesture_text)
        tabs.addTab(gesture_tab, "Gestures")

        # Modes tab
        modes_tab = QWidget()
        modes_layout = QVBoxLayout(modes_tab)
        modes_text = QLabel(
            "<b>Navigation Mode:</b><br>"
            "• Environment descriptions<br>"
            "• Obstacle warnings<br>"
            "• Direction guidance<br><br>"
            "<b>Assistant Mode:</b><br>"
            "• Ask questions about surroundings<br>"
            "• General information queries<br>"
            "• Object identification<br><br>"
            "<b>Reading Mode:</b><br>"
            "• Text recognition<br>"
            "• Document reading<br>"
            "• Sign interpretation"
        )
        modes_text.setWordWrap(True)
        modes_layout.addWidget(modes_text)
        tabs.addTab(modes_tab, "Modes")

        # Voice commands tab
        voice_tab = QWidget()
        voice_layout = QVBoxLayout(voice_tab)
        voice_text = QLabel(
            "<b>Example Questions in Assistant Mode:</b><br><br>"
            "\"What objects are around me?\"<br>"
            "\"Is there a chair nearby?\"<br>"
            "\"What color is the car?\"<br>"
            "\"Describe the room I'm in\"<br>"
            "\"Any obstacles ahead?\"<br>"
            "\"Read the sign in front of me\""
        )
        voice_text.setWordWrap(True)
        voice_layout.addWidget(voice_text)
        tabs.addTab(voice_tab, "Voice Commands")

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.hide)
        layout.addWidget(close_button)