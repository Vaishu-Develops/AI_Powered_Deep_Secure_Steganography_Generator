# Security Analysis

## Empirical Findings (4 image pairs)
- Mean PSNR(Cover,Stego): 15.4009 dB
- Mean PSNR(Secret,Revealed): 20.0465 dB
- Mean SSIM(Secret,Revealed): 0.5739

## Password Robustness
- PSNR drop with wrong password: 9.5590 dB
- SSIM drop with wrong password: 0.5134

## Attack Surface Notes
- Model inversion/extraction attacks remain possible if API access is uncontrolled.
- Text mode currently uses AES-ECB in backend/text_steg.py, which leaks pattern structure and is not semantically secure.
- Temporary and upload directories should be periodically cleaned to avoid data retention risk.
- Add rate limiting, authentication, and request size limits on API endpoints.

## Recommended Hardening
1. Replace AES-ECB with AES-GCM (authenticated encryption).
2. Use random nonces/IVs and store with ciphertext.
3. Add API auth + per-user quota + rate limiting.
4. Encrypt temporary files at rest or avoid disk persistence when possible.
