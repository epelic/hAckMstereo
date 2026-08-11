try:
    from PySide6.QtCore import QTimer, Signal, QObject, Qt
    from PySide6.QtGui import QColor, QPainter, QPen, QIcon
    from PySide6.QtWidgets import *
except ImportError:
    from PySide2.QtCore import QTimer, Signal, QObject, Qt
    from PySide2.QtGui import QColor, QPainter, QPen, QIcon
    from PySide2.QtWidgets import *
