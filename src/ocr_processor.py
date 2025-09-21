from paddleocr import PaddleOCR
import numpy as np
import cv2

# 初始化PaddleOCR模型。模型文件在Docker构建阶段已下载并缓存。
# lang='ch' 支持中英文混合识别。
try:
    print("[INFO] Initializing PaddleOCR model...")
    ocr_model = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
    print("[INFO] PaddleOCR model initialized successfully.")
except Exception as e:
    print(f"[ERROR] Failed to initialize PaddleOCR model: {e}")
    ocr_model = None

def get_text_from_image(image_bytes: bytes) -> str:
    """使用本地PaddleOCR模型从图片字节流中识别文字。"""
    if ocr_model is None:
        print("[WARNING] OCR model is not available. Skipping OCR.")
        return ""
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            print("[WARNING] Could not decode image bytes for OCR.")
            return ""

        result = ocr_model.ocr(img, cls=True)
        texts = []
        if result and result[0] is not None:
             for line in result[0]:
                texts.append(line[1][0])
        
        ocr_text = " ".join(texts)
        if ocr_text:
            print(f"[INFO] OCR successful, extracted {len(ocr_text)} characters.")
            return f"\n[OCR Image Text]:\n{ocr_text}\n"
        return ""
    except Exception as e:
        print(f"[WARNING] An error occurred during OCR processing: {e}")
        return ""
