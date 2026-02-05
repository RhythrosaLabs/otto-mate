"""
Brand Brain System for Otto
===========================

Centralized brand asset management and brand-aware content generation.
Ported from printify_clean with enhancements.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

logger = logging.getLogger(__name__)


class BrandBrain:
    """
    Manages brand assets, guidelines, and brand-aware content generation.
    
    Features:
    - Asset management (logos, fonts, guidelines)
    - Brand profile with visual identity and writing style
    - Knowledge base processing for brand documents
    - Prompt enhancement with brand context
    - Logo/watermark application to videos
    - Brand color application to images
    """

    def __init__(self, brand_dir: str = "data/brand_brain"):
        """Initialize BrandBrain with directory structure."""
        self.brand_dir = Path(brand_dir)
        self.assets_dir = self.brand_dir / "assets"
        self.logos_dir = self.assets_dir / "logos"
        self.fonts_dir = self.assets_dir / "fonts"
        self.colors_dir = self.assets_dir / "colors"
        self.guidelines_dir = self.assets_dir / "guidelines"
        self.embeddings_dir = self.brand_dir / "embeddings"
        self.config_dir = self.brand_dir / "config"
        self.config_file = self.config_dir / "brand_profile.yaml"

        self._ensure_directories()

    def _ensure_directories(self):
        """Create brand brain directory structure."""
        for directory in [
            self.logos_dir,
            self.fonts_dir,
            self.colors_dir,
            self.guidelines_dir,
            self.embeddings_dir,
            self.config_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    # ============================================
    # ASSET MANAGEMENT
    # ============================================

    def save_asset(self, file_path: str, category: str, filename: Optional[str] = None) -> str:
        """
        Save an asset file to the appropriate folder.

        Args:
            file_path: Path to the source file
            category: 'logo', 'font', 'guideline', etc.
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        category_map = {
            "logo": self.logos_dir,
            "font": self.fonts_dir,
            "guideline": self.guidelines_dir,
            "color": self.colors_dir,
        }

        target_dir = category_map.get(category, self.assets_dir)
        source = Path(file_path)
        target_name = filename or source.name
        target_path = target_dir / target_name

        shutil.copy2(source, target_path)
        logger.info(f"Saved {category} asset: {target_path}")
        return str(target_path)

    def save_asset_from_bytes(self, data: bytes, filename: str, category: str) -> str:
        """
        Save asset from binary data.

        Args:
            data: Binary file data
            filename: Filename to save as
            category: Asset category

        Returns:
            Path to saved file
        """
        category_map = {
            "logo": self.logos_dir,
            "font": self.fonts_dir,
            "guideline": self.guidelines_dir,
        }

        target_dir = category_map.get(category, self.assets_dir)
        target_path = target_dir / filename

        with open(target_path, "wb") as f:
            f.write(data)

        logger.info(f"Saved {category} asset: {target_path}")
        return str(target_path)

    def get_assets(self, category: str) -> List[Path]:
        """Get all assets in a category."""
        category_map = {
            "logo": self.logos_dir,
            "font": self.fonts_dir,
            "guideline": self.guidelines_dir,
        }

        target_dir = category_map.get(category, self.assets_dir)
        return list(target_dir.glob("*")) if target_dir.exists() else []

    def delete_asset(self, file_path: str) -> bool:
        """Delete an asset file."""
        try:
            Path(file_path).unlink(missing_ok=True)
            logger.info(f"Deleted asset: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete asset: {e}")
            return False

    def get_primary_logo(self) -> Optional[str]:
        """Get the primary logo path."""
        profile = self.load_profile()
        logo_path = profile.get("visual_identity", {}).get("logo_files", {}).get("main")
        if logo_path and Path(logo_path).exists():
            return logo_path
        # Fallback to first logo in directory
        logos = self.get_assets("logo")
        if logos:
            return str(logos[0])
        return None

    # ============================================
    # KNOWLEDGE BASE
    # ============================================

    def _read_file_content(self, file_path: Path) -> str:
        """Read content from a file based on its extension."""
        suffix = file_path.suffix.lower()
        if suffix in [".txt", ".md", ".json", ".yaml", ".yml"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif suffix == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                return "\n".join(page.extract_text() for page in reader.pages)
            except ImportError:
                return f"[PDF Processing Unavailable for {file_path.name}]"
            except Exception as e:
                return f"[Error reading PDF {file_path.name}: {str(e)}]"
        return ""

    def process_knowledge_base(self) -> Dict:
        """
        Process all files in guidelines directory and create a knowledge base.

        Returns:
            Dict containing processed text from all documents
        """
        knowledge_base = {
            "documents": [],
            "last_updated": datetime.now().isoformat(),
            "total_docs": 0
        }

        guideline_files = self.get_assets("guideline")

        for file_path in guideline_files:
            try:
                content = self._read_file_content(file_path)
                if content:
                    knowledge_base["documents"].append({
                        "filename": file_path.name,
                        "content": content[:50000],  # Limit per file
                        "type": file_path.suffix.lower(),
                    })
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")

        knowledge_base["total_docs"] = len(knowledge_base["documents"])

        # Save processed knowledge base
        kb_file = self.brand_dir / "brand_knowledge.json"
        with open(kb_file, "w") as f:
            json.dump(knowledge_base, f, indent=2)

        logger.info(f"Processed {knowledge_base['total_docs']} brand documents")
        return knowledge_base

    def get_knowledge_base(self) -> Dict:
        """Get processed knowledge base."""
        kb_file = self.brand_dir / "brand_knowledge.json"
        if kb_file.exists():
            try:
                with open(kb_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    # ============================================
    # BRAND PROFILE MANAGEMENT
    # ============================================

    def load_profile(self) -> Dict:
        """Load brand profile from YAML."""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return yaml.safe_load(f) or self._get_default_profile()
        return self._get_default_profile()

    def save_profile(self, profile: Dict):
        """Save brand profile to YAML."""
        with open(self.config_file, "w") as f:
            yaml.dump(profile, f, default_flow_style=False, indent=2)
        logger.info("Brand profile saved")

    def update_profile(self, updates: Dict):
        """Update specific fields in brand profile."""
        profile = self.load_profile()
        self._deep_update(profile, updates)
        self.save_profile(profile)

    def _deep_update(self, base: Dict, updates: Dict):
        """Recursively update nested dictionary."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def _get_default_profile(self) -> Dict:
        """Default brand profile template."""
        return {
            "brand_name": "My Brand",
            "tagline": "Your tagline here",
            "visual_identity": {
                "primary_colors": ["#667eea", "#764ba2"],
                "secondary_colors": ["#f59e0b", "#10b981"],
                "fonts": {
                    "primary": "Montserrat",
                    "secondary": "Open Sans"
                },
                "logo_files": {
                    "main": None,
                    "icon": None,
                    "video": None,
                    "audio": None
                },
            },
            "writing_style": {
                "tone": ["professional", "friendly"],
                "avoid": ["overly casual", "excessive punctuation"],
                "voice": "Clear and engaging",
                "examples": [],
            },
            "content_guidelines": {
                "hashtags": [],
                "keywords": [],
                "cta_phrases": [],
            },
            "social_media": {
                "instagram": {
                    "posting_frequency": "Daily",
                    "best_times": ["9am", "3pm", "7pm"],
                    "content_mix": "60% product, 30% lifestyle, 10% behind-scenes",
                },
                "twitter": {
                    "posting_frequency": "Multiple daily",
                    "best_times": ["8am", "12pm", "5pm"],
                },
                "tiktok": {
                    "posting_frequency": "Daily",
                    "best_times": ["7pm", "9pm"],
                },
            },
            "target_audience": {
                "demographics": [],
                "interests": [],
                "pain_points": [],
            },
        }

    # ============================================
    # BRAND-AWARE CONTENT GENERATION
    # ============================================

    def get_brand_context(self) -> str:
        """Get brand context as formatted text for AI prompts."""
        profile = self.load_profile()

        context = f"""BRAND: {profile['brand_name']}
TAGLINE: {profile['tagline']}

BRAND VOICE: {profile['writing_style']['voice']}
TONE: {', '.join(profile['writing_style']['tone'])}
AVOID: {', '.join(profile['writing_style']['avoid'])}

COLORS: {', '.join(profile['visual_identity']['primary_colors'])}
TARGET AUDIENCE: {', '.join(profile['target_audience']['demographics'])}

EXAMPLE POSTS THAT MATCH OUR STYLE:
{self._format_examples(profile['writing_style']['examples'])}

KEY HASHTAGS: {' '.join(profile['content_guidelines']['hashtags'])}
KEYWORDS: {', '.join(profile['content_guidelines']['keywords'])}
"""
        return context

    def _format_examples(self, examples: List[str]) -> str:
        """Format example posts."""
        if not examples:
            return "No examples provided yet"
        return "\n".join(f"- {ex}" for ex in examples[:5])

    def enhance_prompt(self, base_prompt: str, content_type: str) -> str:
        """
        Enhance any prompt with brand context.

        Args:
            base_prompt: Original prompt
            content_type: 'social_post', 'blog', 'email', 'video_script', etc.

        Returns:
            Enhanced prompt with brand guidelines
        """
        profile = self.load_profile()
        brand_context = self.get_brand_context()

        enhanced = f"""You are creating {content_type} for {profile['brand_name']}.

{brand_context}

Now generate the following, matching our brand style and tone:

{base_prompt}

IMPORTANT: Maintain brand consistency. Match the style of our example posts above."""

        return enhanced

    def get_chat_system_prompt(self) -> str:
        """Get enhanced system prompt for chat assistant."""
        profile = self.load_profile()

        return f"""You are a Personal Assistant for {profile['brand_name']}.

{self.get_brand_context()}

Always maintain brand consistency in your responses. Use the brand voice and tone described above.
When generating content, match the style of the example posts provided.
"""

    # ============================================
    # MEDIA PROCESSING
    # ============================================

    def apply_logo_to_video(self, video_path: str, position: str = "bottom-right") -> str:
        """
        Add logo watermark to video.

        Args:
            video_path: Path to video file
            position: 'top-left', 'top-right', 'bottom-left', 'bottom-right'

        Returns:
            Path to video with logo
        """
        logo_path = self.get_primary_logo()
        if not logo_path:
            logger.warning("No logo found, skipping watermark")
            return video_path

        try:
            from moviepy.editor import CompositeVideoClip, ImageClip, VideoFileClip

            video = VideoFileClip(video_path)
            logo = ImageClip(logo_path).set_duration(video.duration)

            # Resize logo to 10% of video width
            logo = logo.resize(width=int(video.w * 0.1))

            # Set opacity
            logo = logo.set_opacity(0.8)

            # Position logo
            margins = 20
            positions = {
                "top-left": (margins, margins),
                "top-right": (video.w - logo.w - margins, margins),
                "bottom-left": (margins, video.h - logo.h - margins),
                "bottom-right": (video.w - logo.w - margins, video.h - logo.h - margins),
            }
            logo = logo.set_position(positions.get(position, positions["bottom-right"]))

            # Composite
            final = CompositeVideoClip([video, logo])

            output_path = video_path.replace(".mp4", "_branded.mp4")
            final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)

            video.close()
            logger.info(f"Applied logo watermark: {output_path}")
            return output_path

        except ImportError:
            logger.warning("MoviePy not available for logo application")
            return video_path
        except Exception as e:
            logger.error(f"Logo application failed: {e}")
            return video_path

    def apply_brand_colors_to_image(self, image_path: str, intensity: float = 0.12) -> str:
        """
        Apply brand color tint to image.

        Args:
            image_path: Path to image file
            intensity: Color overlay intensity (0.0 to 1.0)

        Returns:
            Path to branded image
        """
        try:
            from PIL import Image, ImageEnhance

            profile = self.load_profile()
            primary_colors = profile.get("visual_identity", {}).get("primary_colors", [])

            if not primary_colors:
                logger.warning("No brand colors defined, skipping color grading")
                return image_path

            # Load image
            img = Image.open(image_path)

            # Convert hex to RGB
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip("#")
                return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

            brand_rgb = hex_to_rgb(primary_colors[0])

            # Create color overlay
            overlay = Image.new("RGB", img.size, brand_rgb)

            # Convert to RGBA for blending
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            overlay = overlay.convert("RGBA")

            # Blend with low opacity
            blended = Image.blend(img, overlay, alpha=intensity)

            # Enhance saturation
            enhancer = ImageEnhance.Color(blended.convert("RGB"))
            result = enhancer.enhance(1.15)

            # Save result
            output_path = str(
                Path(image_path).parent
                / f"{Path(image_path).stem}_branded{Path(image_path).suffix}"
            )
            result.save(output_path, quality=95)

            logger.info(f"Applied brand color grading: {output_path}")
            return output_path

        except ImportError:
            logger.warning("Pillow not available for color grading")
            return image_path
        except Exception as e:
            logger.error(f"Color grading failed: {e}")
            return image_path

    # ============================================
    # STYLE ANALYSIS
    # ============================================

    def analyze_writing_samples(self, samples: str) -> Dict[str, Any]:
        """
        Analyze writing samples to extract style patterns.

        Args:
            samples: Text samples (social posts, blog excerpts, etc.)

        Returns:
            Dictionary with extracted style characteristics
        """
        # This would typically call an LLM for analysis
        # For now, return basic structure
        return {
            "tone": [],
            "common_phrases": [],
            "sentence_patterns": "",
            "emotional_appeal": "",
            "formatting_style": "",
            "target_audience": "",
        }

    def train_from_examples(self, examples: List[str]):
        """
        Train brand brain from example posts.
        Updates brand profile with the examples.

        Args:
            examples: List of example posts/content
        """
        profile = self.load_profile()
        profile["writing_style"]["examples"] = examples[:10]  # Store up to 10
        self.save_profile(profile)
        logger.info(f"Added {len(examples)} examples to brand profile")

    # ============================================
    # EXPORT/IMPORT
    # ============================================

    def export_brand_kit(self, output_path: str) -> str:
        """
        Export complete brand kit as a zip file.

        Args:
            output_path: Path for output zip file

        Returns:
            Path to created zip file
        """
        import zipfile

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all files from brand directory
            for file_path in self.brand_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.brand_dir)
                    zf.write(file_path, arcname)

        logger.info(f"Exported brand kit: {output_path}")
        return output_path

    def import_brand_kit(self, zip_path: str):
        """
        Import brand kit from a zip file.

        Args:
            zip_path: Path to brand kit zip file
        """
        import zipfile

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(self.brand_dir)

        logger.info(f"Imported brand kit from: {zip_path}")


# Singleton instance
_brand_brain = None


def get_brand_brain() -> BrandBrain:
    """Get the singleton BrandBrain instance."""
    global _brand_brain
    if _brand_brain is None:
        _brand_brain = BrandBrain()
    return _brand_brain
