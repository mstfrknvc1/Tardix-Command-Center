from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)
from core.news import FeedItem


class NewsItemWidget(QFrame):
    """Basit haber widget'ı resim desteği ile."""
    
    clicked = Signal(str)  # URL yayınlar
    
    def __init__(self, feed_item: FeedItem, parent: QWidget | None = None):
        super().__init__(parent)
        self.feed_item = feed_item
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Resim label'ı
        self.image_label = QLabel()
        self.image_label.setFixedSize(60, 50)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #2a2a3a;
                border-radius: 4px;
                background-color: #2a2a3a;
            }
        """)
        
        # Metin layout'ı
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        
        # Site adı
        site_label = QLabel(self.feed_item.source)
        site_label.setStyleSheet("color: #8ab4f8; font-weight: bold; font-size: 9pt;")
        
        # Başlık
        title_label = QLabel(self.feed_item.title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #e0e0e0; font-size: 10pt; font-weight: bold;")
        
        # Açıklama
        desc_label = QLabel(self.feed_item.description if self.feed_item.description else "")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #b0b0b0; font-size: 8pt;")
        desc_label.setMaximumHeight(40)  # Limit description height
        
        text_layout.addWidget(site_label)
        text_layout.addWidget(title_label)
        if self.feed_item.description:
            text_layout.addWidget(desc_label)
        text_layout.addStretch()
        
        # Layout'a ekle
        layout.addWidget(self.image_label)
        layout.addLayout(text_layout, 1)
        
        # Resim varsa yükle
        if self.feed_item.image_url:
            self.load_image(self.feed_item.image_url)
        else:
            self.show_placeholder()
        
        # Stil
        self.setStyleSheet("""
            NewsItemWidget {
                border: 1px solid #2a2a3a;
                border-radius: 5px;
                background-color: #1a1a1a;
                margin: 1px;
                padding: 2px;
            }
            NewsItemWidget:hover {
                border: 1px solid #1C3F95;
                background-color: #1e1e2e;
            }
        """)
        
    def load_image(self, image_url: str):
        """URL'den resim yükler."""
        try:
            from PySide6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
            
            # URL'i temizle ve doğrula
            if not image_url or not image_url.startswith(('http://', 'https://')):
                self.show_placeholder()
                return
            
            self.nam = QNetworkAccessManager(self)
            request = QNetworkRequest(QUrl(image_url))
            request.setRawHeader(b"User-Agent", b"Tardix-Command-Center/0.5 RSS-reader")
            request.setRawHeader(b"Accept", b"image/*")
            
            self.reply = self.nam.get(request)
            self.reply.finished.connect(self.on_image_loaded)
            self.reply.errorOccurred.connect(self.on_image_error)
        except Exception as e:
            print(f"Image load error: {e}")
            self.show_placeholder()
    
    def on_image_loaded(self):
        """Resim yüklendiğinde."""
        try:
            from PySide6.QtNetwork import QNetworkReply
            if self.reply.error() == QNetworkReply.NetworkError.NoError:
                data = self.reply.readAll()
                if data:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(data):
                        # Resim boyutunu ayarla
                        scaled_pixmap = pixmap.scaled(
                            self.image_label.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.image_label.setPixmap(scaled_pixmap)
                        return
            self.show_placeholder()
        except Exception as e:
            print(f"Image processing error: {e}")
            self.show_placeholder()
        finally:
            self.reply.deleteLater()
    
    def on_image_error(self, error):
        """Resim yükleme hatası."""
        print(f"Network error loading image: {error}")
        self.show_placeholder()
    
    def show_placeholder(self):
        """Resim yoksa placeholder."""
        self.image_label.setText("📰")
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #2a2a3a;
                border-radius: 3px;
                background-color: #2a2a3a;
                color: #666;
                font-size: 12pt;
            }
        """)
    
    def mousePressEvent(self, event):
        """Tıklandığında linki aç."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.feed_item.link)
        super().mousePressEvent(event)
