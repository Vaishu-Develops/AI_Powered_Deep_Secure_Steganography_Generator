import numpy as np
import os
import sys

# Add the current directory to sys.path so we can import backend
sys.path.append(os.getcwd())

from backend.text_steg import TextSteganography
import cv2

def verify():
    print("Starting verification...")
    
    # 1. Create a dummy image
    img_path = "test_image.png"
    output_path = "test_stego.png"
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(img_path, img)
    
    message = "Hello, this is a secret message!"
    password = "secret_password"
    
    try:
        # 2. Hide text
        print(f"Hiding text: '{message}'")
        TextSteganography.hide_text(img_path, message, password, output_path)
        print("Text hidden successfully.")
        
        # 3. Extract text
        print("Extracting text...")
        extracted_message = TextSteganography.extract_text(output_path, password)
        print(f"Extracted message: '{extracted_message}'")
        
        if message == extracted_message:
            print("VERIFICATION SUCCESS: Message matches!")
        else:
            print(f"VERIFICATION FAILURE: Message mismatch! Expected '{message}', got '{extracted_message}'")
            
    except Exception as e:
        print(f"VERIFICATION FAILURE: An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if os.path.exists(img_path):
            os.remove(img_path)
        if os.path.exists(output_path):
            os.remove(output_path)

if __name__ == "__main__":
    verify()
