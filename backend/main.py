# Trigger redeploy with LFS weights
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
import gc
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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
H_MODEL = os.path.join(BASE_DIR, "weights", "netH.pth")
R_MODEL = os.path.join(BASE_DIR, "weights", "netR.pth")

# Reassemble netH.pth from parts if needed (to bypass Git LFS bandwidth limits)
def assemble_models():
    print(f"Checking models in {BASE_DIR}/weights...")
    h_parts = [
        os.path.join(BASE_DIR, "weights", "netH_part1.bin"),
        os.path.join(BASE_DIR, "weights", "netH_part2.bin")
    ]
    
    # Check netH.pth
    needs_h = not os.path.exists(H_MODEL)
    if os.path.exists(H_MODEL):
        with open(H_MODEL, 'rb') as f:
            if b'version https://git-lfs' in f.read(100):
                print("netH.pth is an LFS pointer, needs reassembly.")
                needs_h = True
    
    if needs_h:
        print("Assembling netH.pth from chunks...")
        try:
            with open(H_MODEL, 'wb') as f_out:
                for p in h_parts:
                    if os.path.exists(p):
                        print(f"Reading part: {p}")
                        with open(p, 'rb') as f_in:
                            f_out.write(f_in.read())
                    else:
                        print(f"ERROR: Model chunk missing: {p}")
            print("Successfully reassembled netH.pth")
        except Exception as e:
            print(f"CRITICAL ERROR during assembly: {str(e)}")

    # Check netR.pth (it's small but could still be an LFS pointer if not pushed correctly)
    if os.path.exists(R_MODEL):
        with open(R_MODEL, 'rb') as f:
            if b'version https://git-lfs' in f.read(100):
                print("WARNING: netR.pth is still an LFS pointer! Reveal functionality will fail.")
    else:
        print("ERROR: netR.pth is missing!")

print("Starting startup sequence...")
assemble_models()
image_steg = ImageSteganography(h_model_path=H_MODEL, r_model_path=R_MODEL)
print("Application ready (Models will be loaded lazily on first request).")

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
        gc.collect()
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
        gc.collect()
        return FileResponse(output_path, media_type="image/png", filename="revealed_secret.png")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

# Configure Static Files (Frontend)
# Looking for frontend/dist relative to backend folder
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")

if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/")
    async def serve_spa():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    # Catch-all for SPA support
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        if full_path.startswith("hide") or full_path.startswith("reveal"):
            return None
        path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(path):
            return FileResponse(path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
