import torch
import sys
import os
from PIL import Image
import numpy as np

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from image_steg import ImageSteganography

def test_resolution():
    steg = ImageSteganography()
    # Test if model handles 512x512
    # Create random tensors
    cover = torch.rand(1, 3, 512, 512).to(steg.device)
    secret = torch.rand(1, 3, 512, 512).to(steg.device)
    input_img = torch.cat([cover, secret], dim=1)
    
    try:
        with torch.no_grad():
            output = steg.h_net(input_img)
        print("SUCCESS! Model successfully processed 512x512 tensor.")
        print(f"Output shape: {output.shape}")
        
        # Test 1024x1024
        cover = torch.rand(1, 3, 1024, 1024).to(steg.device)
        secret = torch.rand(1, 3, 1024, 1024).to(steg.device)
        input_img = torch.cat([cover, secret], dim=1)
        with torch.no_grad():
            output = steg.h_net(input_img)
        print("SUCCESS! Model successfully processed 1024x1024 tensor.")
        print(f"Output shape: {output.shape}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_resolution()
