import cv2
import time
import threading
from typing import Callable, Optional, Tuple
import numpy as np


class CameraManager:
    """Manages camera operations for the Vision Assistant application."""

    def __init__(self, frame_callback: Optional[Callable[[np.ndarray], None]] = None):
        """
        Initialize the camera manager.

        Args:
            frame_callback: Function to call with each new frame
        """
        self.frame_callback = frame_callback
        self.camera = None
        self.running = False
        self.paused = False
        self.camera_thread = None
        self.current_frame = None
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        self.last_frame_time = 0

    def start(self, camera_index: int = 0, width: int = 640, height: int = 480, fps: int = 30) -> bool:
        """
        Start the camera.

        Args:
            camera_index: Camera device index
            width: Frame width
            height: Frame height
            fps: Target frames per second

        Returns:
            True if camera started successfully, False otherwise
        """
        if self.camera_thread is not None and self.camera_thread.is_alive():
            return True

        self.frame_width = width
        self.frame_height = height
        self.fps = fps

        try:
            self.camera = cv2.VideoCapture(camera_index)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera.set(cv2.CAP_PROP_FPS, fps)

            # Check if camera opened successfully
            if not self.camera.isOpened():
                print("Failed to open camera")
                return False

            # Start camera thread
            self.running = True
            self.camera_thread = threading.Thread(target=self._camera_loop)
            self.camera_thread.daemon = True
            self.camera_thread.start()
            return True

        except Exception as e:
            print(f"Camera initialization error: {e}")
            return False

    def stop(self) -> None:
        """Stop the camera."""
        self.running = False

        if self.camera_thread:
            self.camera_thread.join(timeout=2.0)

        if self.camera:
            self.camera.release()
            self.camera = None

    def toggle_pause(self) -> bool:
        """
        Toggle pause state.

        Returns:
            New pause state
        """
        self.paused = not self.paused
        return self.paused

    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame.

        Returns:
            Current frame or None if no frame is available
        """
        return self.current_frame

    def capture_still(self) -> Optional[np.ndarray]:
        """
        Capture a still image (higher resolution if possible).

        Returns:
            Captured image or None if capture failed
        """
        if not self.camera or not self.camera.isOpened():
            return None

        # Save current resolution
        current_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        current_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)

        try:
            # Set higher resolution for still capture
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            # Capture frame
            ret, frame = self.camera.read()

            # Restore original resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, current_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, current_height)

            if ret:
                return frame
            return None

        except Exception as e:
            print(f"Still capture error: {e}")
            # Restore original resolution in case of error
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, current_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, current_height)
            return None

    def _camera_loop(self) -> None:
        """Main camera capture loop."""
        frame_interval = 1.0 / self.fps

        while self.running:
            if not self.camera or not self.camera.isOpened():
                print("Camera not available")
                break

            if not self.paused:
                # Calculate elapsed time since last frame
                current_time = time.time()
                elapsed = current_time - self.last_frame_time

                # Ensure we maintain target FPS
                if elapsed >= frame_interval:
                    ret, frame = self.camera.read()

                    if ret:
                        self.current_frame = frame

                        # Call callback if provided
                        if self.frame_callback:
                            self.frame_callback(frame)

                        self.last_frame_time = current_time

            # Sleep to avoid consuming too much CPU
            sleep_time = max(0.001, frame_interval - (time.time() - self.last_frame_time))
            time.sleep(sleep_time)

        # Clean up
        if self.camera:
            self.camera.release()
            self.camera = None


class MotionDetector:
    """Detects motion in camera frames."""

    def __init__(self,
                 sensitivity: float = 0.5,
                 min_area: int = 500,
                 history: int = 3):
        """
        Initialize the motion detector.

        Args:
            sensitivity: Detection sensitivity (0-1)
            min_area: Minimum contour area to consider as motion
            history: Number of previous frames to consider
        """
        self.sensitivity = sensitivity
        self.min_area = min_area
        self.history = history
        self.frames = []
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=100, varThreshold=16, detectShadows=False
        )

    def detect(self, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Detect motion in a frame.

        Args:
            frame: Input frame

        Returns:
            Tuple of (motion_detected, visualization_frame)
        """
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)

        # Apply threshold to get binary image
        _, thresh = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Check for significant motion
        motion_detected = False
        visualization = frame.copy()

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                motion_detected = True
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(visualization, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return motion_detected, visualization

    def set_sensitivity(self, sensitivity: float) -> None:
        """
        Set detector sensitivity.

        Args:
            sensitivity: New sensitivity value (0-1)
        """
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        # Adjust parameters based on sensitivity
        self.min_area = int(1000 * (1 - self.sensitivity))


class QRCodeScanner:
    """Scans for QR codes in camera frames."""

    def __init__(self):
        """Initialize the QR code scanner."""
        self.detector = cv2.QRCodeDetector()

    def scan(self, frame: np.ndarray) -> Tuple[bool, str, Optional[np.ndarray]]:
        """
        Scan for QR codes in a frame.

        Args:
            frame: Input frame

        Returns:
            Tuple of (code_detected, code_data, visualization_frame)
        """
        # Detect and decode
        try:
            data, bbox, _ = self.detector.detectAndDecode(frame)

            # Check if a QR code was found
            if data and bbox is not None:
                # Convert bbox to integer points
                bbox = bbox.astype(int)

                # Create visualization
                visualization = frame.copy()

                # Draw bounding box
                cv2.polylines(
                    visualization, [bbox], True, (0, 255, 0), 2
                )

                # Add text with decoded data
                cv2.putText(
                    visualization, data, (bbox[0][0], bbox[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
                )

                return True, data, visualization

            return False, "", None

        except Exception as e:
            print(f"QR code scanning error: {e}")
            return False, "", None