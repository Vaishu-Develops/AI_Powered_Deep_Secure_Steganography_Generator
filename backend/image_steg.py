import torch
import torchvision.transforms as transforms
from PIL import Image
try:
    from .models import UnetGenerator, RevealNet
except ImportError:
    from models import UnetGenerator, RevealNet
import os
import hashlib
import numpy as np
import cv2

class ImageSteganography:
    def __init__(self, h_model_path=None, r_model_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.h_net = UnetGenerator(input_nc=6, output_nc=3, num_downs=7).to(self.device).eval()
        self.r_net = RevealNet().to(self.device).eval()
        
        if h_model_path:
            if not os.path.exists(h_model_path):
                raise FileNotFoundError(f"Hiding model weights not found at: {h_model_path}")
            self.h_net.load_state_dict(torch.load(h_model_path, map_location=self.device))
            
        if r_model_path:
            if not os.path.exists(r_model_path):
                raise FileNotFoundError(f"Reveal model weights not found at: {r_model_path}")
            self.r_net.load_state_dict(torch.load(r_model_path, map_location=self.device))

        self.to_tensor = transforms.ToTensor()

    def _get_permutation(self, length, password):
        seed_hash = hashlib.sha256(password.encode()).digest()
        seed = int.from_bytes(seed_hash[:4], 'big')
        rng = np.random.RandomState(seed)
        return rng.permutation(length)

    def _shuffle_image(self, img_pil, password):
        img_np = np.array(img_pil)
        h, w = img_np.shape[:2]
        block_size = 4
        
        num_blocks_h = h // block_size
        num_blocks_w = w // block_size
        
        blocks = img_np.reshape(num_blocks_h, block_size, num_blocks_w, block_size, 3)
        blocks = blocks.transpose(0, 2, 1, 3, 4).reshape(-1, block_size, block_size, 3)
        
        perm = self._get_permutation(len(blocks), password)
        shuffled_blocks = blocks[perm]
        
        shuffled_np = shuffled_blocks.reshape(num_blocks_h, num_blocks_w, block_size, block_size, 3)
        shuffled_np = shuffled_np.transpose(0, 2, 1, 3, 4).reshape(h, w, 3)
        return Image.fromarray(shuffled_np)

    def _unshuffle_image(self, img_pil, password):
        img_np = np.array(img_pil)
        h, w = img_np.shape[:2]
        block_size = 4
        
        num_blocks_h = h // block_size
        num_blocks_w = w // block_size
        
        blocks = img_np.reshape(num_blocks_h, block_size, num_blocks_w, block_size, 3)
        blocks = blocks.transpose(0, 2, 1, 3, 4).reshape(-1, block_size, block_size, 3)
        
        perm = self._get_permutation(len(blocks), password)
        unshuffled_blocks = np.zeros_like(blocks)
        unshuffled_blocks[perm] = blocks
        
        unshuffled_np = unshuffled_blocks.reshape(num_blocks_h, num_blocks_w, block_size, block_size, 3)
        unshuffled_np = unshuffled_np.transpose(0, 2, 1, 3, 4).reshape(h, w, 3)
        return Image.fromarray(unshuffled_np)

    def _get_optimal_size(self, w, h, max_dim=768, multiple=128):
        """Calculates new dimensions maintaining aspect ratio, capped by max_dim, rounded to multiple."""
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            new_w = w * scale
            new_h = h * scale
        else:
            new_w = w
            new_h = h
            
        final_w = max(multiple, round(new_w / multiple) * multiple)
        final_h = max(multiple, round(new_h / multiple) * multiple)
        return int(final_w), int(final_h)

    def hide_image(self, cover_path, secret_path, output_path, password=None):
        cover_pil = Image.open(cover_path).convert('RGB')
        secret_pil = Image.open(secret_path).convert('RGB')
        
        # 1. Determine optimal resolution based on Cover image aspect ratio
        w, h = cover_pil.size
        opt_w, opt_h = self._get_optimal_size(w, h, max_dim=768)
        
        # 2. Resize BOTH carefully to this new optimal resolution
        cover_pil = cover_pil.resize((opt_w, opt_h), Image.LANCZOS)
        secret_pil = secret_pil.resize((opt_w, opt_h), Image.LANCZOS)

        # 3. Apply password shuffling if requested
        if password:
            secret_pil = self._shuffle_image(secret_pil, password)
        
        # 4. Convert to tensors
        cover = self.to_tensor(cover_pil).unsqueeze(0).to(self.device)
        secret = self.to_tensor(secret_pil).unsqueeze(0).to(self.device)
        
        input_img = torch.cat([cover, secret], dim=1)
        with torch.no_grad():
            container = self.h_net(input_img)
            
        container_img = transforms.ToPILImage()(container.squeeze(0).cpu().clamp(0, 1))
        container_img.save(output_path)
        return True

    def reveal_image(self, container_path, output_path, password=None):
        # Stego image is ALREADY perfectly sized (multiples of 128)
        img_pil = Image.open(container_path).convert('RGB')
        
        # But let's guarantee it's correctly sized just in case it was resized by user
        w, h = img_pil.size
        # Force rounding to nearest 128 (usually it will do nothing because we saved it exactly)
        opt_w = max(128, round(w / 128) * 128)
        opt_h = max(128, round(h / 128) * 128)
        if (w, h) != (opt_w, opt_h):
            img_pil = img_pil.resize((opt_w, opt_h), Image.LANCZOS)
            
        container = self.to_tensor(img_pil).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            revealed = self.r_net(container)
            
        revealed_img_pil = transforms.ToPILImage()(revealed.squeeze(0).cpu().clamp(0, 1))
        
        if password:
            revealed_img_pil = self._unshuffle_image(revealed_img_pil, password)
            
            img_np = np.array(revealed_img_pil)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            deblocked = cv2.bilateralFilter(img_bgr, d=5, sigmaColor=50, sigmaSpace=50)
            img_rgb_final = cv2.cvtColor(deblocked, cv2.COLOR_BGR2RGB)
            revealed_img_pil = Image.fromarray(img_rgb_final)
            
        revealed_img_pil.save(output_path)
        return True
