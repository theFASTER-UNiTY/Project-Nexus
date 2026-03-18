from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class IconWidget(QLabel):
    """
    Custom class for displaying simple, static icon
    """
    def __init__(self, imagePath, sizeW: int = 32, sizeH: int = 32, parent = None):
        super().__init__(parent)
        
        pixmap = QPixmap(imagePath)
        
        resizedPixmap = pixmap.scaled(
            sizeW, sizeH, 
            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(resizedPixmap)
        self.setFixedSize(sizeW, sizeH)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
