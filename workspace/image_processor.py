#!/usr/bin/env python3
import os
from PIL import Image, ImageFilter, ImageEnhance
import cv2
import numpy as np
from pathlib import Path

def cut_and_resize_image(input_path, output_path, crop_box=None, new_size=(800, 600)):
    """
    Cut (crop) and resize an image
    crop_box: (left, top, right, bottom) or None for center crop
    new_size: (width, height) for final size
    """
    try:
        # Open the image
        with Image.open(input_path) as img:
            print(f"Original image size: {img.size}")
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Crop the image
            if crop_box:
                cropped = img.crop(crop_box)
            else:
                # Center crop to square
                width, height = img.size
                size = min(width, height)
                left = (width - size) // 2
                top = (height - size) // 2
                right = left + size
                bottom = top + size
                cropped = img.crop((left, top, right, bottom))
            
            print(f"Cropped size: {cropped.size}")
            
            # Resize the image
            resized = cropped.resize(new_size, Image.Resampling.LANCZOS)
            print(f"Final size: {resized.size}")
            
            # Save the processed image
            resized.save(output_path, quality=95)
            print(f"Saved processed image to: {output_path}")
            
            return output_path
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def apply_killing_effect(input_path, output_path):
    """
    Apply dramatic 'killing' effects - high contrast, dark mood
    """
    try:
        with Image.open(input_path) as img:
            # Apply dramatic effects
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # Reduce brightness slightly
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.8)
            
            # Increase saturation
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.5)
            
            # Apply edge enhancement
            img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
            
            # Save the dramatic version
            img.save(output_path, quality=95)
            print(f"Applied killing effects, saved to: {output_path}")
            
            return output_path
    
    except Exception as e:
        print(f"Error applying effects: {e}")
        return None

def main():
    # Find input image
    image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
    if not image_files:
        print("No image files found in current directory!")
        return
    
    input_image = image_files[0]
    print(f"Processing image: {input_image}")
    
    # Step 1: Cut and resize
    cut_resized_path = "cut_resized_image.jpg"
    result1 = cut_and_resize_image(input_image, cut_resized_path, new_size=(1024, 768))
    
    if result1:
        # Step 2: Apply killing effects
        final_path = "final_killed_image.jpg"
        result2 = apply_killing_effect(cut_resized_path, final_path)
        
        if result2:
            print(f"\n✅ SUCCESS! Final processed image: {final_path}")
            print(f"\n📊 Processing Summary:")
            print(f"   - Original: {input_image}")
            print(f"   - Cut & Resized: {cut_resized_path}")
            print(f"   - Final with effects: {final_path}")
        else:
            print("❌ Failed to apply effects")
    else:
        print("❌ Failed to cut and resize image")

if __name__ == "__main__":
    main()
