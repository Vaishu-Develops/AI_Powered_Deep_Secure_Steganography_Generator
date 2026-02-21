import cv2
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA256
import base64

class TextSteganography:
    @staticmethod
    def _get_cipher(password):
        key = SHA256.new(password.encode()).digest()
        return AES.new(key, AES.MODE_ECB)

    @staticmethod
    def encrypt_text(text, password):
        cipher = TextSteganography._get_cipher(password)
        padded_data = pad(text.encode(), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_data).decode()

    @staticmethod
    def decrypt_text(encrypted_b64, password):
        cipher = TextSteganography._get_cipher(password)
        encrypted_data = base64.b64decode(encrypted_b64.encode())
        decrypted_padded = cipher.decrypt(encrypted_data)
        return unpad(decrypted_padded, AES.block_size).decode()

    @staticmethod
    def hide_text(image_path, text, password, output_path):
        # Encrypt text first
        secret_data = TextSteganography.encrypt_text(text, password)
        # Add a delimiter to mark the end of the message
        secret_data += "###EOF###"
        
        # Convert text to binary
        binary_data = ''.join(format(ord(char), '08b') for char in secret_data)
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Image not found")
        
        flat_img = img.flatten()
        
        if len(binary_data) > len(flat_img):
            raise ValueError(f"Message too long for this image. Need {len(binary_data)} bits, but image only has {len(flat_img)} pixels.")
        
        # Modify LSB using vectorized operations
        n = len(binary_data)
        bits = np.array([int(b) for b in binary_data], dtype=np.uint8)
        flat_img[:n] = (flat_img[:n] & 0xFE) | bits
            
        new_img = flat_img.reshape(img.shape)
        success = cv2.imwrite(output_path, new_img)
        if not success:
            raise IOError(f"Failed to write stego image to {output_path}")
        return True

    @staticmethod
    def extract_text(image_path, password):
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Image not found")
        
        flat_img = img.flatten()
        
        # Extract LSB efficiently
        lsbs = (flat_img & 1).astype(np.uint8)
        
        # Convert to bytes
        # We process in chunks to find the delimiter without converting the entire image
        binary_str = "".join(lsbs.astype(str))
        
        # Convert binary strings to characters
        decoded_data = ""
        for i in range(0, len(binary_str), 8):
            byte_str = binary_str[i:i+8]
            if len(byte_str) < 8:
                break
            char = chr(int(byte_str, 2))
            decoded_data += char
            if decoded_data.endswith("###EOF###"):
                break
        
        if not decoded_data.endswith("###EOF###"):
            raise ValueError("No secret message found or wrong password")
            
        encrypted_message = decoded_data[:-9]
        return TextSteganography.decrypt_text(encrypted_message, password)
