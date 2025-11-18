import os
import sys
import ctypes
import pyautogui
from io import BytesIO
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
from PyQt6.QtCore import Qt, QPoint

from google import genai
from google.genai import types
from google.genai.errors import APIError

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

class GhostOverlay(QWidget):
    def __init__(self):
        super().__init__()

        try:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            print(f"Gemini Client Initialization Error: {e}")
            self.client = None

        self.oldPos = self.pos()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 350, 500)

        layout = QVBoxLayout()
        self.setStyleSheet("""
            QWidget#Main {
                background-color: rgba(30, 30, 30, 0.90);
                border: 1px solid rgba(255, 185, 0, 0.5);
                border-radius: 12px;
            }
            QLabel { color: #ffffff; font-weight: bold; font-family: sans-serif; }
            QTextEdit { background-color: rgba(0, 0, 0, 0.3); color: #e0e0e0; border: none; padding: 5px; font-size: 13px; }
            QPushButton { background-color: #3C4043; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #5F6368; }
            QPushButton#AnalyzeBtn { background-color: #1A73E8; }
            QPushButton#AnalyzeBtn:hover { background-color: #185ABC; }
            QPushButton#CloseBtn { background-color: #EA4335; width: 30px; }
        """)

        main_container = QWidget()
        main_container.setObjectName("Main")
        inner_layout = QVBoxLayout(main_container)

        header_layout = QHBoxLayout()
        title = QLabel("Gemini Vision Layer")
        close_btn = QPushButton("×")
        close_btn.setObjectName("CloseBtn")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        inner_layout.addLayout(header_layout)

        self.output_area = QTextEdit()
        self.output_area.setPlaceholderText("Connected to Gemini API.\nReady to analyze...")
        self.output_area.setReadOnly(True)
        inner_layout.addWidget(self.output_area)

        self.analyze_btn = QPushButton("📸 Analyze Screen")
        self.analyze_btn.setObjectName("AnalyzeBtn")
        self.analyze_btn.clicked.connect(self.run_analysis)
        inner_layout.addWidget(self.analyze_btn)

        layout.addWidget(main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def run_analysis(self):
        if not self.client:
            self.output_area.setText("Error: Gemini Client not initialized. Check your API key.")
            return

        self.output_area.setText("Sending to Gemini...")
        self.analyze_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            self.hide()
            screenshot = pyautogui.screenshot()
            self.show()

            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")

            image_part = types.Part.from_bytes(
                data=buffered.getvalue(),
                mime_type='image/png'
            )

            contents = [
                "Analyze this screen content concisely. If it's code, debug it. If it's text, summarize it.",
                image_part
            ]

            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=contents
            )

            self.output_area.setText(response.text)

        except APIError as e:
            self.show()
            self.output_area.setText(f"Gemini API Error: {str(e)}")
        except Exception as e:
            self.show()
            self.output_area.setText(f"General Error: {str(e)}")

        self.analyze_btn.setEnabled(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GhostOverlay()
    ex.show()

    try:
        hwnd = int(ex.winId())
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
        print( "Stealth Mode Active")
    except Exception as e:
        print(f"Stealth Mode Error (Expected on Mac/Linux): {e}")

    sys.exit(app.exec())
