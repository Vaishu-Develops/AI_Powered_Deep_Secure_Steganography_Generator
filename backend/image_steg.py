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
        
        if h_model_path and os.path.exists(h_model_path):
            self.h_net.load_state_dict(torch.load(h_model_path, map_location=self.device))
        if r_model_path and os.path.exists(r_model_path):
            self.r_net.load_state_dict(torch.load(r_model_path, map_location=self.device))

        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
        ])

    def _get_permutation(self, length, password):
        seed_hash = hashlib.sha256(password.encode()).digest()
        seed = int.from_bytes(seed_hash[:4], 'big')
        rng = np.random.RandomState(seed)
        perm = rng.permutation(length)
        return perm

    def _shuffle_image(self, img_pil, password):
        # Resize to 256x256 first
        img_resized = img_pil.resize((256, 256)).convert('RGB')
        img_np = np.array(img_resized)
        
        block_size = 4
        num_blocks = 256 // block_size
        
        # Reshape to (num_blocks, block_size, num_blocks, block_size, 3)
        # Then (num_blocks * num_blocks, block_size, block_size, 3)
        blocks = img_np.reshape(num_blocks, block_size, num_blocks, block_size, 3)
        blocks = blocks.transpose(0, 2, 1, 3, 4).reshape(-1, block_size, block_size, 3)
        
        perm = self._get_permutation(len(blocks), password)
        shuffled_blocks = blocks[perm]
        
        # Reshape back to (256, 256, 3)
        shuffled_np = shuffled_blocks.reshape(num_blocks, num_blocks, block_size, block_size, 3)
        shuffled_np = shuffled_np.transpose(0, 2, 1, 3, 4).reshape(256, 256, 3)
        
        return Image.fromarray(shuffled_np)

    def _unshuffle_image(self, img_pil, password):
        img_np = np.array(img_pil)
        block_size = 4
        num_blocks = 256 // block_size
        
        blocks = img_np.reshape(num_blocks, block_size, num_blocks, block_size, 3)
        blocks = blocks.transpose(0, 2, 1, 3, 4).reshape(-1, block_size, block_size, 3)
        
        perm = self._get_permutation(len(blocks), password)
        unshuffled_blocks = np.zeros_like(blocks)
        unshuffled_blocks[perm] = blocks
        
        unshuffled_np = unshuffled_blocks.reshape(num_blocks, num_blocks, block_size, block_size, 3)
        unshuffled_np = unshuffled_np.transpose(0, 2, 1, 3, 4).reshape(256, 256, 3)
        
        return Image.fromarray(unshuffled_np)

    def _make_square(self, img_pil):
        """Pads an image to square with black bars while maintaining aspect ratio."""
        w, h = img_pil.size
        if w == h:
            return img_pil
        
        max_dim = max(w, h)
        new_img = Image.new("RGB", (max_dim, max_dim), (0, 0, 0))
        
        # Center the image
        left = (max_dim - w) // 2
        top = (max_dim - h) // 2
        new_img.paste(img_pil, (left, top))
        return new_img

    def hide_image(self, cover_path, secret_path, output_path, password=None):
        cover_pil = Image.open(cover_path)
        if cover_pil.mode != 'RGB':
            cover_pil = cover_pil.convert('RGB')
        
        secret_pil = Image.open(secret_path)
        if secret_pil.mode != 'RGB':
            secret_pil = secret_pil.convert('RGB')

        # Handle rectangular images via padding to square
        cover_pil = self._make_square(cover_pil)
        secret_pil = self._make_square(secret_pil)

        if password:
            secret_pil = self._shuffle_image(secret_pil, password)
        
        cover = self.transform(cover_pil).unsqueeze(0).to(self.device)
        secret = self.transform(secret_pil).unsqueeze(0).to(self.device)
        
        input_img = torch.cat([cover, secret], dim=1)
        with torch.no_grad():
            container = self.h_net(input_img)
            
        container_img = transforms.ToPILImage()(container.squeeze(0).cpu().clamp(0, 1))
        container_img.save(output_path)
        return True

    def reveal_image(self, container_path, output_path, password=None):
        container = self.transform(Image.open(container_path).convert('RGB')).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            revealed = self.r_net(container)
            
        revealed_img_pil = transforms.ToPILImage()(revealed.squeeze(0).cpu().clamp(0, 1))
        
        if password:
            revealed_img_pil = self._unshuffle_image(revealed_img_pil, password)
            
            # Post-processing: Deblocking filter
            # Convert to numpy/cv2 format (HWC, BGR)
            img_np = np.array(revealed_img_pil)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            # Apply a light deblocking filter
            # Bilateral filter is good for smoothing flat areas while keeping edges sharp
            deblocked = cv2.bilateralFilter(img_bgr, d=5, sigmaColor=50, sigmaSpace=50)
            
            # Convert back to RGB and PIL
            img_rgb_final = cv2.cvtColor(deblocked, cv2.COLOR_BGR2RGB)
            revealed_img_pil = Image.fromarray(img_rgb_final)
            
        revealed_img_pil.save(output_path)
        return True
