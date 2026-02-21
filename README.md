# 🔐 AI-Powered Deep Secure Steganography Generator

A full-stack steganography application combining **Deep Learning** and **AES Cryptography** to securely hide images and text within cover images.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?logo=pytorch)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)

---

## ✨ Features

- **Image-in-Image Hiding**: Hide a secret image inside a cover image using deep neural networks
- **Text-in-Image Hiding**: Embed encrypted text messages within images using LSB steganography
- **AES-256 Encryption**: All hidden data is encrypted before embedding
- **Password Protection**: Optional password-based pixel block shuffling for additional security
- **Modern Web UI**: Clean React interface with drag-and-drop file uploads
- **Real-time Processing**: Fast inference using pre-trained PyTorch models

---

## 🛠️ Tech Stack

### Frontend
- React 18 + Vite
- Axios (HTTP client)
- Framer Motion (animations)
- Lucide React (icons)

### Backend
- FastAPI (REST API)
- PyTorch (Deep Learning)
- OpenCV & Pillow (Image processing)
- PyCryptodome (AES encryption)

### AI/ML
- **HidingNet**: U-Net encoder-decoder architecture (6ch input → 3ch output)
- **RevealNet**: 6-layer CNN for secret extraction
- Pre-trained on ImageNet (45,000 images)

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- Node.js 18+ (with pnpm or npm)
- CUDA-compatible GPU (optional, for faster inference)

### 1. Clone Repository
```bash
git clone https://github.com/Vaishu-Develops/AI_Powered_Deep_Secure_Steganography_Generator.git
cd AI_Powered_Deep_Secure_Steganography_Generator
```

### 2. Setup Backend
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Download Model Weights
Download pre-trained models and place in `backend/checkpoints/`:
- `netH.pth` (HidingNet ~160MB)
- `netR.pth` (RevealNet ~3MB)

### 4. Setup Frontend
```bash
cd frontend
pnpm install   # or npm install
```

---

## 🚀 Running the Application

### Start Backend Server
```bash
cd backend
python main.py
```
Backend runs at: `http://localhost:8000`

### Start Frontend Dev Server
```bash
cd frontend
pnpm run dev   # or npm run dev
```
Frontend runs at: `http://localhost:5173`

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/hide-image` | POST | Hide secret image in cover image |
| `/reveal-image` | POST | Extract hidden image from container |
| `/hide-text` | POST | Hide encrypted text in image |
| `/extract-text` | POST | Extract and decrypt hidden text |

### Example: Hide Image
```bash
curl -X POST http://localhost:8000/hide-image \
  -F "cover=@cover.png" \
  -F "secret=@secret.png" \
  -F "password=mysecret"
```

### Example: Hide Text
```bash
curl -X POST http://localhost:8000/hide-text \
  -F "image=@cover.png" \
  -F "message=Secret message here" \
  -F "password=mysecret"
```

---

## 🔬 How It Works

### Image Steganography (Deep Learning)
```
Cover Image (256×256) + Secret Image (256×256)
                ↓
        Concatenate (6 channels)
                ↓
         U-Net HidingNet
                ↓
        Container Image (3ch)
        (Looks like cover)
                ↓
           RevealNet
                ↓
      Revealed Secret Image
```

### Text Steganography (AES + LSB)
```
Secret Text + Password
        ↓
   SHA256 → AES Key
        ↓
  AES-256 Encryption
        ↓
  Convert to Binary
        ↓
  LSB Bit Embedding
        ↓
    Stego Image
```

### Security Layers
1. **AES-256 Encryption** - Text encrypted before embedding
2. **LSB Embedding** - Bits hidden in pixel least significant bits
3. **Block Shuffling** - Password-based pixel block scrambling
4. **Neural Encoding** - Deep network encodes data imperceptibly

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py              # FastAPI server & routes
│   ├── image_steg.py        # Deep learning steganography
│   ├── text_steg.py         # AES + LSB text steganography
│   ├── models/
│   │   ├── HidingUNet.py    # U-Net encoder-decoder
│   │   └── RevealNet.py     # CNN extractor
│   ├── checkpoints/
│   │   ├── netH.pth         # Trained HidingNet weights
│   │   └── netR.pth         # Trained RevealNet weights
│   ├── temp/                # Temporary output files
│   └── uploads/             # Uploaded files
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # Styling
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🎯 Algorithms

### U-Net Architecture (HidingNet)
- **Input**: 6 channels (cover + secret concatenated)
- **Encoder**: 7 downsampling blocks with skip connections
- **Decoder**: 7 upsampling blocks with concatenation
- **Output**: 3-channel container image

### RevealNet Architecture
- 6 convolutional layers (3→64→128→256→128→64→3)
- Batch normalization + ReLU activation
- Sigmoid output for pixel values [0,1]

### Loss Function
```
Total Loss = β × MSE(cover, container) + (1-β) × MSE(secret, revealed)
Where β = 0.75
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Cover-Container APD | 4.16 |
| Secret-Revealed APD | 4.40 |
| Image Resolution | 256×256 |
| Inference Time | ~0.5s (GPU) / ~2s (CPU) |

*APD = Averaged Pixel-wise Discrepancy (lower is better)*

---

## ⚠️ Disclaimer

This software is for **educational and research purposes only**. Users are responsible for complying with local laws and regulations regarding steganography and encryption.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Contact

**Vaishu Develops** - [GitHub Profile](https://github.com/Vaishu-Develops)

Project Link: [https://github.com/Vaishu-Develops/AI_Powered_Deep_Secure_Steganography_Generator](https://github.com/Vaishu-Develops/AI_Powered_Deep_Secure_Steganography_Generator)
