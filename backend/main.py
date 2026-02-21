from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import uuid
try:
    from .text_steg import TextSteganography
    from .image_steg import ImageSteganography
except ImportError:
    from text_steg import TextSteganography
    from image_steg import ImageSteganography

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
TEMP_DIR = "temp"

for d in [UPLOAD_DIR, TEMP_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Initialize Image Steganography
H_MODEL = "backend/checkpoints/netH.pth"
R_MODEL = "backend/checkpoints/netR.pth"
image_steg = ImageSteganography(h_model_path=H_MODEL, r_model_path=R_MODEL)

@app.post("/hide-text")
async def hide_text(
    image: UploadFile = File(...),
    message: str = Form(...),
    password: str = Form(...)
):
    print(f"Received hide-text request: msg_len={len(message)}, filename={image.filename}")
    temp_id = str(uuid.uuid4())
    ext = os.path.splitext(image.filename)[1] or ".png"
    input_path = os.path.join(UPLOAD_DIR, f"{temp_id}{ext}")
    output_path = os.path.join(TEMP_DIR, f"stego_{temp_id}.png")
    
    try:
        image.file.seek(0)
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        print(f"File saved to {input_path}")
            
        TextSteganography.hide_text(input_path, message, password, output_path)
        print(f"Stego image created at {output_path}")
        return FileResponse(output_path, media_type="image/png", filename="stego_text.png")
    except Exception as e:
        print(f"Error in hide_text: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/extract-text")
async def extract_text(
    image: UploadFile = File(...),
    password: str = Form(...)
):
    print(f"Received extract-text request: filename={image.filename}")
    temp_id = str(uuid.uuid4())
    ext = os.path.splitext(image.filename)[1] or ".png"
    input_path = os.path.join(UPLOAD_DIR, f"{temp_id}{ext}")
    
    try:
        image.file.seek(0)
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        secret_message = TextSteganography.extract_text(input_path, password)
        return {"message": secret_message}
    except Exception as e:
        print(f"Error in extract_text: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/hide-image")
async def hide_image(
    cover: UploadFile = File(...),
    secret: UploadFile = File(...),
    password: str = Form(None)
):
    temp_id = str(uuid.uuid4())
    cover_path = os.path.join(UPLOAD_DIR, f"cover_{temp_id}_{cover.filename}")
    secret_path = os.path.join(UPLOAD_DIR, f"secret_{temp_id}_{secret.filename}")
    output_path = os.path.join(TEMP_DIR, f"stego_img_{temp_id}.png")
    
    with open(cover_path, "wb") as buffer:
        shutil.copyfileobj(cover.file, buffer)
    with open(secret_path, "wb") as buffer:
        shutil.copyfileobj(secret.file, buffer)
        
    try:
        image_steg.hide_image(cover_path, secret_path, output_path, password=password)
        return FileResponse(output_path, media_type="image/png", filename="stego_image.png")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/reveal-image")
async def reveal_image(
    stego: UploadFile = File(...),
    password: str = Form(None)
):
    temp_id = str(uuid.uuid4())
    stego_path = os.path.join(UPLOAD_DIR, f"stego_{temp_id}_{stego.filename}")
    output_path = os.path.join(TEMP_DIR, f"revealed_{temp_id}.png")
    
    with open(stego_path, "wb") as buffer:
        shutil.copyfileobj(stego.file, buffer)
        
    try:
        image_steg.reveal_image(stego_path, output_path, password=password)
        return FileResponse(output_path, media_type="image/png", filename="revealed_secret.png")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
