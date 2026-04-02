import torch
import sys
import os
from PIL import Image
import numpy as np
import cv2

# Add backend to path to import models
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from image_steg import ImageSteganography

def test_padding():
    H_MODEL = "backend/checkpoints/netH.pth"
    R_MODEL = "backend/checkpoints/netR.pth"
    steg = ImageSteganography(h_model_path=H_MODEL, r_model_path=R_MODEL)
    
    # 1. Square Cover, Rectangular Secret
    cover_img = Image.new("RGB", (400, 400), (255, 255, 255))
    cover_path = "cover_test.png"
    cover_img.save(cover_path)
    
    # Light blue secret
    secret_img = Image.new("RGB", (400, 200), (100, 150, 255))
    secret_path = "secret_test.png"
    secret_img.save(secret_path)
    
    output_path = "stego_test_output.png"
    
    print(f"Hiding rectangular secret in square cover...")
    steg.hide_image(cover_path, secret_path, output_path)
    
    # Inspect Stego img
    stego_res = np.array(Image.open(output_path).convert('RGB'))
    
    print(f"Stego Image Stats:")
    print(f"Mean: {np.mean(stego_res)}")
    print(f"Std: {np.std(stego_res)}")
    print(f"Min: {np.min(stego_res)}")
    print(f"Max: {np.max(stego_res)}")
    
    # Check if there is a grid by taking a small slice
    print("Slice top left [0:5, 0:5, 0]:")
    print(stego_res[0:5, 0:5, 0])
    
    os.remove(cover_path)
    os.remove(secret_path)

if __name__ == "__main__":
    test_padding()
