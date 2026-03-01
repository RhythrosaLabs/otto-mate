"""
Image Processor Plugin
======================

Advanced image processing capabilities including resize, crop, filters, and effects.

Example usage:
    >>> result = await plugin.resize_image("/path/to/image.jpg", width=800)
    >>> result = await plugin.apply_filter("/path/to/image.jpg", filter="blur")
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from io import BytesIO

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

from src.core.plugin_system import ToolPlugin


class ImageProcessorPlugin(ToolPlugin):
    """Plugin for advanced image processing and manipulation."""
    
    FILTERS = {
        "blur": ImageFilter.BLUR if HAS_PILLOW else None,
        "sharpen": ImageFilter.SHARPEN if HAS_PILLOW else None,
        "contour": ImageFilter.CONTOUR if HAS_PILLOW else None,
        "edge_enhance": ImageFilter.EDGE_ENHANCE if HAS_PILLOW else None,
        "emboss": ImageFilter.EMBOSS if HAS_PILLOW else None,
        "smooth": ImageFilter.SMOOTH if HAS_PILLOW else None,
    }
    
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        
        if not HAS_PILLOW:
            self.register_tool(
                name="resize_image",
                func=self._missing_deps,
                description="[Requires: pip install pillow]",
                parameters={"image_path": {"type": "string", "required": True}}
            )
            return
        
        self.default_quality = self.settings.get("default_quality", 85)
        self.max_dimension = self.settings.get("max_dimension", 4096)
        
        # Register image tools
        self.register_tool(
            name="resize_image",
            func=self.resize_image,
            description="Resize an image to specified dimensions while maintaining aspect ratio",
            parameters={
                "image_path": {"type": "string", "required": True, "description": "Path to the image file"},
                "width": {"type": "integer", "required": False, "description": "Target width in pixels"},
                "height": {"type": "integer", "required": False, "description": "Target height in pixels"},
                "output_path": {"type": "string", "required": False, "description": "Output file path (optional)"}
            }
        )
        
        self.register_tool(
            name="crop_image",
            func=self.crop_image,
            description="Crop an image to specified dimensions",
            parameters={
                "image_path": {"type": "string", "required": True},
                "x": {"type": "integer", "required": True, "description": "Left position"},
                "y": {"type": "integer", "required": True, "description": "Top position"},
                "width": {"type": "integer", "required": True, "description": "Crop width"},
                "height": {"type": "integer", "required": True, "description": "Crop height"}
            }
        )
        
        self.register_tool(
            name="apply_filter",
            func=self.apply_filter,
            description="Apply a filter effect to an image (blur, sharpen, contour, edge_enhance, emboss, smooth)",
            parameters={
                "image_path": {"type": "string", "required": True},
                "filter_name": {"type": "string", "required": True, "description": "Filter to apply"},
                "intensity": {"type": "number", "required": False, "description": "Filter intensity 0.0-2.0 (default: 1.0)"}
            }
        )
        
        self.register_tool(
            name="convert_format",
            func=self.convert_format,
            description="Convert image to a different format (JPEG, PNG, WEBP, GIF)",
            parameters={
                "image_path": {"type": "string", "required": True},
                "target_format": {"type": "string", "required": True, "description": "Target format (jpeg, png, webp, gif)"},
                "quality": {"type": "integer", "required": False, "description": "Quality for lossy formats (1-100)"}
            }
        )
        
        self.register_tool(
            name="get_image_info",
            func=self.get_image_info,
            description="Get detailed information about an image (dimensions, format, color mode, etc.)",
            parameters={
                "image_path": {"type": "string", "required": True}
            }
        )
        
        self.register_tool(
            name="create_thumbnail",
            func=self.create_thumbnail,
            description="Create a thumbnail of an image",
            parameters={
                "image_path": {"type": "string", "required": True},
                "size": {"type": "integer", "required": False, "description": "Max dimension (default: 256)"}
            }
        )
    
    async def _missing_deps(self, **kwargs) -> Dict[str, Any]:
        return {
            "error": "Missing dependencies. Install with: pip install pillow",
            "success": False
        }
    
    async def resize_image(self, image_path: str, width: Optional[int] = None, 
                          height: Optional[int] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Resize an image maintaining aspect ratio."""
        try:
            img = Image.open(image_path)
            original_size = img.size
            
            if width and height:
                new_size = (width, height)
            elif width:
                ratio = width / img.width
                new_size = (width, int(img.height * ratio))
            elif height:
                ratio = height / img.height
                new_size = (int(img.width * ratio), height)
            else:
                return {"error": "Specify width or height", "success": False}
            
            # Clamp to max dimension
            new_size = (min(new_size[0], self.max_dimension), min(new_size[1], self.max_dimension))
            
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            
            if not output_path:
                output_path = self._generate_output_path(image_path, "_resized")
            
            resized.save(output_path, quality=self.default_quality)
            
            return {
                "success": True,
                "original_size": original_size,
                "new_size": new_size,
                "output_path": output_path
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def crop_image(self, image_path: str, x: int, y: int, 
                        width: int, height: int, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Crop an image to specified region."""
        try:
            img = Image.open(image_path)
            cropped = img.crop((x, y, x + width, y + height))
            
            if not output_path:
                output_path = self._generate_output_path(image_path, "_cropped")
            
            cropped.save(output_path, quality=self.default_quality)
            
            return {
                "success": True,
                "crop_region": {"x": x, "y": y, "width": width, "height": height},
                "output_path": output_path
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def apply_filter(self, image_path: str, filter_name: str, 
                          intensity: float = 1.0, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Apply a filter to an image."""
        try:
            filter_name = filter_name.lower()
            if filter_name not in self.FILTERS:
                return {
                    "error": f"Unknown filter: {filter_name}. Available: {list(self.FILTERS.keys())}",
                    "success": False
                }
            
            img = Image.open(image_path)
            filtered = img.filter(self.FILTERS[filter_name])
            
            # Apply intensity via blending
            if intensity != 1.0:
                filtered = Image.blend(img, filtered, min(max(intensity, 0), 2))
            
            if not output_path:
                output_path = self._generate_output_path(image_path, f"_{filter_name}")
            
            filtered.save(output_path, quality=self.default_quality)
            
            return {
                "success": True,
                "filter": filter_name,
                "intensity": intensity,
                "output_path": output_path
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def convert_format(self, image_path: str, target_format: str, 
                            quality: Optional[int] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Convert image to different format."""
        try:
            format_map = {"jpeg": "JPEG", "jpg": "JPEG", "png": "PNG", "webp": "WEBP", "gif": "GIF"}
            target_format = target_format.lower()
            
            if target_format not in format_map:
                return {"error": f"Unsupported format: {target_format}", "success": False}
            
            img = Image.open(image_path)
            
            # Handle RGBA for formats that don't support it
            if img.mode == "RGBA" and target_format in ["jpeg", "jpg"]:
                img = img.convert("RGB")
            
            if not output_path:
                base = Path(image_path).stem
                output_path = str(Path(image_path).parent / f"{base}.{target_format}")
            
            save_kwargs = {}
            if quality and target_format in ["jpeg", "jpg", "webp"]:
                save_kwargs["quality"] = quality
            
            img.save(output_path, format=format_map[target_format], **save_kwargs)
            
            return {
                "success": True,
                "format": target_format,
                "output_path": output_path,
                "file_size": os.path.getsize(output_path)
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """Get detailed image information."""
        try:
            img = Image.open(image_path)
            file_size = os.path.getsize(image_path)
            
            return {
                "success": True,
                "path": image_path,
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "aspect_ratio": round(img.width / img.height, 2),
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "has_transparency": img.mode in ("RGBA", "LA", "P"),
                "is_animated": getattr(img, "is_animated", False)
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def create_thumbnail(self, image_path: str, size: int = 256, 
                              output_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a thumbnail."""
        try:
            img = Image.open(image_path)
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            if not output_path:
                output_path = self._generate_output_path(image_path, "_thumb")
            
            img.save(output_path, quality=self.default_quality)
            
            return {
                "success": True,
                "thumbnail_size": img.size,
                "output_path": output_path
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _generate_output_path(self, original_path: str, suffix: str) -> str:
        """Generate output path with suffix."""
        p = Path(original_path)
        return str(p.parent / f"{p.stem}{suffix}{p.suffix}")
