from setuptools import setup, find_packages

setup(
    name="vision_assistant",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An assistive application for visually impaired users",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/vision-assistant",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "opencv-python>=4.7.0",
        "numpy>=1.23.0",
        "SpeechRecognition>=3.8.1",
        "pyttsx3>=2.90",
        "google-generativeai>=0.3.0",
        "Pillow>=9.0.0",
        "requests>=2.28.0",
        "PyAudio>=0.2.13",
    ],
    entry_points={
        "console_scripts": [
            "vision-assistant=vision_assistant.main:main",
        ],
    },
    include_package_data=True,
)
