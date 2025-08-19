#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Vision Assistant - تطبيق مساعد بصري مبسط وسريع الاستجابة
"""

import sys
import os
import time
import random
import pygame
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QStatusBar
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtMultimedia import QSound

# تهيئة مشغل الصوت
pygame.mixer.init()

# قائمة من الوصوفات للبيئة (بديل عن AI)
ENVIRONMENT_DESCRIPTIONS = [
    "أنت في ممر واضح. يمكنك المضي قدماً بأمان.",
    "هناك طاولة إلى يمينك وكرسي إلى يسارك.",
    "أنت في غرفة مفتوحة. يبدو أنها غرفة معيشة.",
    "هناك باب أمامك. يمكنك التقدم مباشرة للوصول إليه.",
    "انتبه، هناك درج أمامك. يبدو أنه يصعد إلى الطابق العلوي.",
    "أنت في ممر ضيق. يمكنك المشي ببطء إلى الأمام.",
    "هناك سجادة على الأرض ومصباح في الزاوية اليمنى.",
    "أنت في مطبخ. هناك طاولة في المنتصف.",
    "يبدو أنك في غرفة النوم. هناك سرير أمامك.",
    "هناك نافذة كبيرة إلى يسارك. يدخل منها ضوء النهار.",
]

# قائمة من الوصوفات للقراءة (بديل عن AI)
READING_DESCRIPTIONS = [
    "يوجد لافتة تقول: مرحباً بكم في المبنى",
    "يوجد ملصق يقول: يرجى الحفاظ على الهدوء",
    "يوجد لوحة تعليمات: في حالة الطوارئ، اتصل بالرقم 911",
    "يوجد كتاب مفتوح عند الصفحة 42، عنوان الفصل: المغامرة الكبرى",
    "يوجد ملصق على الحائط يقول: لا تنسى إغلاق الأنوار عند المغادرة",
    "يوجد جريدة على الطاولة، العنوان الرئيسي: اكتشافات علمية جديدة",
    "يوجد لوحة على الحائط تظهر خريطة المبنى، أنت في الطابق الأول",
    "يوجد كتيب تعليمات يشرح كيفية استخدام الجهاز",
    "يوجد رسالة مكتوبة: لقد ذهبت للتسوق، سأعود قريباً",
    "يوجد لافتة توجيهية: المخرج إلى اليمين، دورات المياه إلى اليسار",
]


class SimpleVisionAssistant(QMainWindow):
    """التطبيق الرئيسي"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("مساعد الرؤية المبسط")
        self.setMinimumSize(800, 600)

        # حالة التطبيق
        self.current_mode = "navigation"  # navigation, assistant, reading
        self.last_update_time = 0
        self.update_interval = 5.0  # seconds

        # إعداد واجهة المستخدم
        self.setup_ui()

        # بدء التحديثات الدورية
        self.start_updates()

        # ترحيب صوتي
        self.speak("مرحباً بك في مساعد الرؤية المبسط. أنت الآن في وضع التنقل.")

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # إنشاء العنصر المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)

        # منطقة الكاميرا (مستعاضة هنا بمنطقة رمادية)
        self.camera_area = QLabel()
        self.camera_area.setStyleSheet("background-color: #333333;")
        self.camera_area.setMinimumHeight(400)
        self.camera_area.setAlignment(Qt.AlignCenter)
        self.camera_area.setText("منطقة الكاميرا")
        self.camera_area.setFont(QFont("Arial", 20))
        main_layout.addWidget(self.camera_area)

        # أزرار الأوضاع
        mode_layout = QHBoxLayout()

        self.nav_button = QPushButton("وضع التنقل")
        self.nav_button.setStyleSheet("font-size: 16px; padding: 10px;")
        self.nav_button.clicked.connect(lambda: self.set_mode("navigation"))

        self.assist_button = QPushButton("وضع المساعد")
        self.assist_button.setStyleSheet("font-size: 16px; padding: 10px;")
        self.assist_button.clicked.connect(lambda: self.set_mode("assistant"))

        self.read_button = QPushButton("وضع القراءة")
        self.read_button.setStyleSheet("font-size: 16px; padding: 10px;")
        self.read_button.clicked.connect(lambda: self.set_mode("reading"))

        mode_layout.addWidget(self.nav_button)
        mode_layout.addWidget(self.assist_button)
        mode_layout.addWidget(self.read_button)

        main_layout.addLayout(mode_layout)

        # منطقة عرض الاستجابة
        self.response_label = QLabel("منطقة الاستجابة")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.7); color: white; "
            "font-size: 16px; padding: 20px; border-radius: 10px;"
        )
        self.response_label.setWordWrap(True)
        self.response_label.setMinimumHeight(100)
        main_layout.addWidget(self.response_label)

        # زر الاستماع (للوضع المساعد)
        self.listen_button = QPushButton("اضغط للتحدث")
        self.listen_button.setStyleSheet(
            "font-size: 18px; background-color: #4CAF50; color: white; "
            "padding: 15px; border-radius: 10px;"
        )
        self.listen_button.clicked.connect(self.listen_for_speech)
        main_layout.addWidget(self.listen_button)
        self.listen_button.hide()  # إخفاء الزر مبدئياً

        # شريط الحالة
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("جاهز")

    def set_mode(self, mode):
        """تغيير وضع التطبيق"""
        self.current_mode = mode

        # تحديث واجهة المستخدم
        self.nav_button.setStyleSheet(
            "font-size: 16px; padding: 10px; "
            f"background-color: {'#4CAF50' if mode == 'navigation' else '#f0f0f0'}"
        )
        self.assist_button.setStyleSheet(
            "font-size: 16px; padding: 10px; "
            f"background-color: {'#2196F3' if mode == 'assistant' else '#f0f0f0'}"
        )
        self.read_button.setStyleSheet(
            "font-size: 16px; padding: 10px; "
            f"background-color: {'#FF9800' if mode == 'reading' else '#f0f0f0'}"
        )

        # إظهار/إخفاء زر الاستماع
        self.listen_button.setVisible(mode == "assistant")

        # تحديث شريط الحالة
        self.status_bar.showMessage(f"الوضع الحالي: {self.get_mode_name(mode)}")

        # تحديث النص
        if mode == "navigation":
            self.speak("تم تنشيط وضع التنقل")
            self.update_navigation()
        elif mode == "assistant":
            self.speak("تم تنشيط وضع المساعد. اضغط على زر التحدث ثم اطرح سؤالك.")
            self.response_label.setText("اضغط على زر التحدث ثم اطرح سؤالك")
        elif mode == "reading":
            self.speak("تم تنشيط وضع القراءة")
            self.update_reading()

    def get_mode_name(self, mode):
        """الحصول على اسم الوضع بالعربية"""
        if mode == "navigation":
            return "وضع التنقل"
        elif mode == "assistant":
            return "وضع المساعد"
        elif mode == "reading":
            return "وضع القراءة"
        return ""

    def start_updates(self):
        """بدء التحديثات الدورية"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_content)
        self.timer.start(1000)  # تحديث كل ثانية

    def update_content(self):
        """تحديث المحتوى حسب الوضع الحالي"""
        current_time = time.time()

        if self.current_mode == "navigation" and (current_time - self.last_update_time) >= self.update_interval:
            self.update_navigation()
            self.last_update_time = current_time

    def update_navigation(self):
        """تحديث وضع التنقل"""
        description = random.choice(ENVIRONMENT_DESCRIPTIONS)
        self.response_label.setText(description)
        self.speak(description)

    def update_reading(self):
        """تحديث وضع القراءة"""
        reading_text = random.choice(READING_DESCRIPTIONS)
        self.response_label.setText(reading_text)
        self.speak(reading_text)

    def listen_for_speech(self):
        """الاستماع للكلام (محاكاة)"""
        self.status_bar.showMessage("جارٍ الاستماع...")
        self.listen_button.setEnabled(False)
        self.listen_button.setText("جارٍ الاستماع...")

        # محاكاة لوقت الاستماع
        QTimer.singleShot(2000, self.process_speech)

    def process_speech(self):
        """معالجة الكلام (محاكاة)"""
        self.listen_button.setEnabled(True)
        self.listen_button.setText("اضغط للتحدث")
        self.status_bar.showMessage(f"الوضع الحالي: {self.get_mode_name(self.current_mode)}")

        # استجابات افتراضية للأسئلة
        responses = [
            "أمامك طاولة كبيرة بنية اللون.",
            "يوجد شخصان في الغرفة، أحدهما يجلس على الكرسي.",
            "هناك كرسي أزرق على يمينك ونافذة كبيرة على يسارك.",
            "الطقس اليوم مشمس ودرجة الحرارة دافئة.",
            "توجد سيارة حمراء متوقفة أمام المنزل.",
            "هناك كتاب على الطاولة، يبدو أنه رواية.",
            "المكان هادئ نسبياً مع بعض الأصوات الخافتة في الخلفية.",
        ]

        response = random.choice(responses)
        self.response_label.setText(response)
        self.speak(response)

    def speak(self, text):
        """نطق النص صوتياً"""
        try:
            # حذف الملف القديم إذا وجد
            if os.path.exists("temp_speech.mp3"):
                try:
                    pygame.mixer.music.stop()
                    os.remove("temp_speech.mp3")
                except:
                    pass

            # استخدام gTTS فقط إذا كانت متاحة
            try:
                from gtts import gTTS
                tts = gTTS(text=text, lang='ar', slow=False)
                tts.save("temp_speech.mp3")

                pygame.mixer.music.load("temp_speech.mp3")
                pygame.mixer.music.play()
            except ImportError:
                # إذا كانت gTTS غير متاحة، استخدم صوت تنبيه بسيط
                print(f"النص للنطق: {text}")
                pygame.mixer.Sound("beep.wav").play()
        except Exception as e:
            print(f"خطأ في النطق: {e}")
            print(f"النص: {text}")

    def closeEvent(self, event):
        """عند إغلاق التطبيق"""
        self.timer.stop()
        event.accept()


def main():
    """نقطة الدخول للتطبيق"""
    app = QApplication(sys.argv)
    window = SimpleVisionAssistant()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()