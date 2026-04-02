import torch
import sys
import os
from PIL import Image
import numpy as np

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from image_steg import ImageSteganography

def test_user_scenario():
    H_MODEL = "backend/checkpoints/netH.pth"
    R_MODEL = "backend/checkpoints/netR.pth"
    steg = ImageSteganography(h_model_path=H_MODEL, r_model_path=R_MODEL)
    
    # Square Cover (books-like colors)
    cover_np = np.zeros((500, 500, 3), dtype=np.uint8)
    cover_np[:, :] = [180, 160, 140] # Brownish/greyish
    cover_img = Image.fromarray(cover_np)
    cover_path = "cover_user_test.png"
    cover_img.save(cover_path)
    
    # Rectangular landscape Secret (train-like colors)
    secret_np = np.zeros((400, 800, 3), dtype=np.uint8)
    secret_np[:, :] = [100, 120, 150] # Bluish/greyish
    secret_img = Image.fromarray(secret_np)
    secret_path = "secret_user_test.png"
    secret_img.save(secret_path)
    
    output_path = "stego_user_test.png"
    
    print(f"Hiding rectangular secret in square cover WITH password (shuffling)...")
    steg.hide_image(cover_path, secret_path, output_path, password="test")
    
    # Check output
    stego_res = np.array(Image.open(output_path).convert('RGB'))
    
    print(f"Stego Image Stats:")
    print(f"Mean: {np.mean(stego_res)}")
    print(f"Std: {np.std(stego_res)}")
    
    os.remove(cover_path)
    os.remove(secret_path)

if __name__ == "__main__":
    test_user_scenario()
