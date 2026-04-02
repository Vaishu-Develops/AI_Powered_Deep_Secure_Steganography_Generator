import torch
import sys
import os
from PIL import Image
import numpy as np

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from image_steg import ImageSteganography

def test_dynamic_size():
    H_MODEL = "backend/checkpoints/netH.pth"
    R_MODEL = "backend/checkpoints/netR.pth"
    steg = ImageSteganography(h_model_path=H_MODEL, r_model_path=R_MODEL)
    
    # Square Cover (books-like colors) - High Res
    cover_np = np.zeros((1080, 1080, 3), dtype=np.uint8)
    cover_np[:, :] = [180, 160, 140]
    cover_img = Image.fromarray(cover_np)
    cover_path = "cover_user_test.png"
    cover_img.save(cover_path)
    
    # Rectangular landscape Secret (train-like colors)
    secret_np = np.zeros((400, 800, 3), dtype=np.uint8)
    secret_np[:, :] = [100, 120, 150]
    secret_img = Image.fromarray(secret_np)
    secret_path = "secret_user_test.png"
    secret_img.save(secret_path)
    
    output_path = "stego_dynamic.png"
    reveal_path = "reveal_dynamic.png"
    password = "dynamic_test"
    
    print(f"Hiding rectangular secret in square cover WITH dynamic sizing...")
    steg.hide_image(cover_path, secret_path, output_path, password=password)
    
    # Check output
    stego_res = Image.open(output_path).convert('RGB')
    print(f"Stego Image Output Size: {stego_res.size}")
    
    steg.reveal_image(output_path, reveal_path, password=password)
    reveal_res = Image.open(reveal_path).convert('RGB')
    print(f"Reveal Image Output Size: {reveal_res.size}")
    
    os.remove(cover_path)
    os.remove(secret_path)
    os.remove(output_path)
    os.remove(reveal_path)

if __name__ == "__main__":
    test_dynamic_size()
