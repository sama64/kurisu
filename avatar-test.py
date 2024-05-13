import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import Qt, QSize, QPoint

class AvatarWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.offset = None  # Initialize offset to None

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        # Create the avatar label
        avatar_label = QLabel(self)
        avatar_pixmap = QPixmap(os.path.join(os.getcwd(), "avatar.png"))
        avatar_label.setPixmap(avatar_pixmap)

        # Create the drag handle label
        self.drag_handle = QLabel(self)
        self.drag_handle.setStyleSheet("background-color: rgba(255, 255, 255, 100); border-radius: 5px;")
        self.drag_handle.setFixedSize(20, 20)
        self.drag_handle.setCursor(QCursor(Qt.OpenHandCursor))

        # Create a layout and add the avatar label and drag handle
        layout = QVBoxLayout(self)
        layout.addWidget(avatar_label)
        layout.addWidget(self.drag_handle, alignment=Qt.AlignBottom | Qt.AlignRight)

        self.show()

    def sizeHint(self):
        return QSize(400, 400)  # Set the preferred window size

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.mapToParent(event.pos() - self.offset))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        # Update the position of the drag handle
        self.drag_handle.move(self.rect().bottomRight() - QPoint(25, 25))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    avatar_window = AvatarWindow()
    avatar_window.move(100, 100)  # Set the window position
    sys.exit(app.exec_())