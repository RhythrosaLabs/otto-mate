"""
Translator Plugin
=================

Translate text between languages with multiple backend support.

Example usage:
    >>> result = await plugin.translate_text("Hello world", target_lang="es")
    >>> result = await plugin.detect_language("Bonjour le monde")
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from langdetect import detect, detect_langs
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False

from src.core.plugin_system import ToolPlugin


class TranslatorPlugin(ToolPlugin):
    """Plugin for text translation and language detection."""
    
    LANGUAGES = {
        "en": "English", "es": "Spanish", "fr": "French", "de": "German",
        "it": "Italian", "pt": "Portuguese", "ru": "Russian", "zh": "Chinese",
        "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "hi": "Hindi",
        "nl": "Dutch", "pl": "Polish", "tr": "Turkish", "vi": "Vietnamese",
        "th": "Thai", "sv": "Swedish", "da": "Danish", "no": "Norwegian",
        "fi": "Finnish", "el": "Greek", "he": "Hebrew", "id": "Indonesian",
        "ms": "Malay", "cs": "Czech", "hu": "Hungarian", "ro": "Romanian",
        "uk": "Ukrainian", "bg": "Bulgarian", "hr": "Croatian", "sk": "Slovak"
    }
    
    # Demo translations for common phrases
    DEMO_TRANSLATIONS = {
        "hello": {"es": "hola", "fr": "bonjour", "de": "hallo", "it": "ciao", "ja": "こんにちは", "zh": "你好"},
        "thank you": {"es": "gracias", "fr": "merci", "de": "danke", "it": "grazie", "ja": "ありがとう", "zh": "谢谢"},
        "goodbye": {"es": "adiós", "fr": "au revoir", "de": "auf wiedersehen", "it": "arrivederci", "ja": "さようなら"},
        "how are you": {"es": "¿cómo estás?", "fr": "comment allez-vous?", "de": "wie geht es dir?"},
    }
    
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        
        self.default_target = self.settings.get("default_target_language", "en")
        self.provider = self.settings.get("api_provider", "libre")
        self.deepl_key = self.settings.get("deepl_api_key")
        
        self.register_tool(
            name="translate_text",
            func=self.translate_text,
            description="Translate text from one language to another",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to translate"},
                "target_lang": {"type": "string", "required": False, "description": "Target language code (e.g., 'es', 'fr')"},
                "source_lang": {"type": "string", "required": False, "description": "Source language (auto-detect if not specified)"}
            }
        )
        
        self.register_tool(
            name="detect_language",
            func=self.detect_language,
            description="Detect the language of a text",
            parameters={
                "text": {"type": "string", "required": True}
            }
        )
        
        self.register_tool(
            name="translate_batch",
            func=self.translate_batch,
            description="Translate multiple texts at once",
            parameters={
                "texts": {"type": "array", "required": True, "description": "List of texts to translate"},
                "target_lang": {"type": "string", "required": True}
            }
        )
        
        self.register_tool(
            name="get_supported_languages",
            func=self.get_supported_languages,
            description="Get list of supported languages for translation",
            parameters={}
        )
    
    async def translate_text(self, text: str, target_lang: Optional[str] = None,
                            source_lang: Optional[str] = None) -> Dict[str, Any]:
        """Translate text to target language."""
        try:
            target_lang = target_lang or self.default_target
            
            if target_lang not in self.LANGUAGES:
                return {
                    "error": f"Unsupported language: {target_lang}",
                    "supported": list(self.LANGUAGES.keys()),
                    "success": False
                }
            
            # Detect source language if not provided
            if not source_lang:
                detection = await self.detect_language(text)
                source_lang = detection.get("language", "en")
            
            # Try real translation if API available
            if self.deepl_key and HAS_REQUESTS:
                translated = await self._translate_deepl(text, target_lang, source_lang)
                if translated:
                    return translated
            
            if HAS_REQUESTS:
                translated = await self._translate_libre(text, target_lang, source_lang)
                if translated:
                    return translated
            
            # Demo translation
            text_lower = text.lower().strip()
            if text_lower in self.DEMO_TRANSLATIONS:
                demo_trans = self.DEMO_TRANSLATIONS[text_lower]
                if target_lang in demo_trans:
                    return {
                        "success": True,
                        "demo_mode": True,
                        "original": text,
                        "translated": demo_trans[target_lang],
                        "source_language": source_lang,
                        "target_language": target_lang,
                        "target_language_name": self.LANGUAGES.get(target_lang)
                    }
            
            # Simulated response
            return {
                "success": True,
                "demo_mode": True,
                "original": text,
                "translated": f"[{self.LANGUAGES.get(target_lang, target_lang)}] {text}",
                "source_language": source_lang,
                "target_language": target_lang,
                "note": "Install translation dependencies for real translations"
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of text."""
        try:
            if HAS_LANGDETECT and len(text.strip()) > 10:
                detected = detect(text)
                probabilities = detect_langs(text)
                
                return {
                    "success": True,
                    "language": detected,
                    "language_name": self.LANGUAGES.get(detected, detected),
                    "confidence": round(probabilities[0].prob * 100, 1),
                    "alternatives": [
                        {"lang": str(p).split(":")[0], "confidence": round(p.prob * 100, 1)}
                        for p in probabilities[:3]
                    ]
                }
            
            # Simple heuristic detection for demo
            text_lower = text.lower()
            
            if any(c in text for c in "日本語かなカナ"):
                lang = "ja"
            elif any(c in text for c in "한국어"):
                lang = "ko"
            elif any(ord(c) > 0x4E00 and ord(c) < 0x9FFF for c in text):
                lang = "zh"
            elif any(c in text for c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"):
                lang = "ru"
            elif "ñ" in text_lower or any(w in text_lower for w in ["hola", "gracias", "como"]):
                lang = "es"
            elif any(w in text_lower for w in ["bonjour", "merci", "bien"]):
                lang = "fr"
            elif any(w in text_lower for w in ["danke", "guten", "ich"]):
                lang = "de"
            else:
                lang = "en"
            
            return {
                "success": True,
                "demo_mode": True,
                "language": lang,
                "language_name": self.LANGUAGES.get(lang, lang),
                "confidence": 85.0,
                "note": "Basic detection - install langdetect for better accuracy"
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def translate_batch(self, texts: List[str], target_lang: str) -> Dict[str, Any]:
        """Translate multiple texts."""
        try:
            results = []
            
            for text in texts[:20]:  # Limit to 20 texts
                translation = await self.translate_text(text, target_lang)
                results.append({
                    "original": text,
                    "translated": translation.get("translated", text),
                    "success": translation.get("success", False)
                })
            
            return {
                "success": True,
                "target_language": target_lang,
                "count": len(results),
                "translations": results
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported languages."""
        return {
            "success": True,
            "count": len(self.LANGUAGES),
            "languages": self.LANGUAGES
        }
    
    async def _translate_libre(self, text: str, target: str, source: str) -> Optional[Dict]:
        """Use LibreTranslate API."""
        try:
            # LibreTranslate public API
            url = "https://libretranslate.com/translate"
            payload = {
                "q": text,
                "source": source,
                "target": target,
                "format": "text"
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "original": text,
                    "translated": data["translatedText"],
                    "source_language": source,
                    "target_language": target,
                    "provider": "libretranslate"
                }
        except:
            pass
        return None
    
    async def _translate_deepl(self, text: str, target: str, source: str) -> Optional[Dict]:
        """Use DeepL API."""
        try:
            url = "https://api-free.deepl.com/v2/translate"
            headers = {"Authorization": f"DeepL-Auth-Key {self.deepl_key}"}
            payload = {
                "text": [text],
                "target_lang": target.upper()
            }
            if source:
                payload["source_lang"] = source.upper()
            
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "original": text,
                    "translated": data["translations"][0]["text"],
                    "source_language": data["translations"][0].get("detected_source_language", source).lower(),
                    "target_language": target,
                    "provider": "deepl"
                }
        except:
            pass
        return None
