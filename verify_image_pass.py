import numpy as np
import os
import sys
from PIL import Image

# Add the current directory to sys.path so we can import backend
sys.path.append(os.getcwd())

from backend.image_steg import ImageSteganography

def verify():
    print("Starting image password verification...")
    
    # Initialize Stego
    # Paths for models (might need adjustment if running from D:\Stegen)
    H_MODEL = "backend/checkpoints/netH.pth"
    R_MODEL = "backend/checkpoints/netR.pth"
    steg = ImageSteganography(h_model_path=H_MODEL, r_model_path=R_MODEL)
    
    # 1. Create dummy images
    cover_path = "test_cover.png"
    secret_path = "test_secret.png"
    stego_path = "test_stego_img.png"
    revealed_correct_path = "revealed_correct.png"
    revealed_wrong_path = "revealed_wrong.png"
    
    # Create a simple cover (say, blue)
    cover = Image.new('RGB', (256, 256), color=(0, 0, 255))
    cover.save(cover_path)
    # Create a simple secret (say, red with some text or pattern)
    secret = Image.new('RGB', (256, 256), color=(255, 0, 0))
    secret.save(secret_path)
    
    password = "super_secret_pass"
    wrong_password = "wrong_pass"
    
    try:
        # 2. Hide image with password
        print(f"Hiding image with password: '{password}'")
        steg.hide_image(cover_path, secret_path, stego_path, password=password)
        print("Image hidden successfully.")
        
        # 3. Reveal with correct password
        print("Revealing with correct password...")
        steg.reveal_image(stego_path, revealed_correct_path, password=password)
        
        # 4. Reveal with wrong password
        print("Revealing with wrong password...")
        steg.reveal_image(stego_path, revealed_wrong_path, password=wrong_password)
        
        # Check if revealed_correct matches secret (roughly)
        res_correct = np.array(Image.open(revealed_correct_path))
        orig_secret = np.array(Image.open(secret_path))
        
        # Since it's DL, it won't be identical, but should be close in mean
        diff = np.mean(np.abs(res_correct.astype(float) - orig_secret.astype(float)))
        print(f"Mean Difference (Correct Password): {diff:.4f}")
        
        # Check if revealed_wrong is very different
        res_wrong = np.array(Image.open(revealed_wrong_path))
        diff_wrong = np.mean(np.abs(res_wrong.astype(float) - orig_secret.astype(float)))
        print(f"Mean Difference (Wrong Password): {diff_wrong:.4f}")
        
        if diff < 50 and diff_wrong > 50:
            print("VERIFICATION SUCCESS: Password protection works!")
        else:
            print("VERIFICATION FAILURE: Diff mismatch.")
            
    except Exception as e:
        print(f"VERIFICATION FAILURE: An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        for p in [cover_path, secret_path, stego_path, revealed_correct_path, revealed_wrong_path]:
            if os.path.exists(p):
                os.remove(p)

if __name__ == "__main__":
    verify()
