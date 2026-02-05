"""
Storage Module
==============

File storage and management.
"""

from .file_storage import FileStorage, StorageConfig
from .universal_capture import (
    UniversalFileCapture, 
    get_file_capture, 
    auto_capture_result,
    CapturedFile
)

__all__ = [
    "FileStorage", 
    "StorageConfig",
    "UniversalFileCapture",
    "get_file_capture",
    "auto_capture_result",
    "CapturedFile"
]
