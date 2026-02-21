import numpy as np
import cv2

def reproduce():
    # Simulate the code in text_steg.py
    # Create a small dummy image
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    flat_img = img.flatten()
    
    binary_data = "10101010"
    
    print(f"Original flat_img[0]: {flat_img[0]}, type: {type(flat_img[0])}")
    
    try:
        for i in range(len(binary_data)):
            # This is line 49 in text_steg.py
            val = (flat_img[i] & 254) | int(binary_data[i])
            print(f"Index {i}: (flat_img[{i}] & 254) | {binary_data[i]} = {val}, type: {type(val)}")
            flat_img[i] = val
        print("Success with uint8")
    except OverflowError as e:
        print(f"Caught expected OverflowError: {e}")
    except Exception as e:
        print(f"Caught unexpected exception: {e}")

    # Now let's try with int8 to see if that's the cause
    print("\nTrying with int8...")
    img_int8 = np.zeros((10, 10, 3), dtype=np.int8)
    flat_img_int8 = img_int8.flatten()
    try:
        for i in range(len(binary_data)):
            val = (flat_img_int8[i] & 254) | int(binary_data[i])
            print(f"Index {i}: (flat_img_int8[{i}] & 254) | {binary_data[i]} = {val}, type: {type(val)}")
            # If val is 254, and we assign to int8, it might overflow
            flat_img_int8[i] = val
        print("Success with int8 (Wait, why?)")
    except OverflowError as e:
        print(f"Caught expected OverflowError in int8: {e}")
    except Exception as e:
        print(f"Caught unexpected exception in int8: {e}")

if __name__ == "__main__":
    reproduce()
