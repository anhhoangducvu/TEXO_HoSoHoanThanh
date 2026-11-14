# -*- coding: utf-8 -*-
"""
Đọc PDF ảnh scan bằng OCR (tùy chọn). Cần Tesseract và gói tiếng Việt:
  - Windows: cài Tesseract (UB Mannheim), tick "Vietnamese"; pip install pytesseract
  - Streamlit Cloud: file packages.txt có  tesseract-ocr  và  tesseract-ocr-vie
Máy không có Tesseract thì công cụ vẫn chạy, chỉ không có nút đọc OCR.
OCR chỉ để đọc DANH MỤC (tên hồ sơ, số, ngày) – độ chính xác thấp hơn file gốc, phải kiểm tra lại.
"""
import io
import os
import shutil

_TRANG_THAI = None


def san_sang():
    """(True, mô tả) nếu dùng được OCR tiếng Việt."""
    global _TRANG_THAI
    if _TRANG_THAI is not None:
        return _TRANG_THAI
    try:
        import pytesseract
        if os.name == "nt" and not shutil.which("tesseract"):
            for p in (r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
                if os.path.exists(p):
                    pytesseract.pytesseract.tesseract_cmd = p
                    break
        ver = pytesseract.get_tesseract_version()
        langs = pytesseract.get_languages(config="")
        if "vie" not in langs:
            _TRANG_THAI = (False, f"Tesseract {ver} chưa có gói tiếng Việt (vie).")
        else:
            _TRANG_THAI = (True, f"Tesseract {ver} · tiếng Việt")
    except Exception as e:  # chưa cài
        _TRANG_THAI = (False, f"Chưa cài Tesseract OCR ({type(e).__name__}).")
    return _TRANG_THAI


def ocr_pdf(data, max_trang=15, dpi=200, trang=None):
    """Trả (text, số trang đã đọc). trang: danh sách chỉ số trang cần đọc (mặc định các trang đầu)."""
    import pypdfium2 as pdfium
    import pytesseract
    pdf = pdfium.PdfDocument(io.BytesIO(data))
    idx = list(trang) if trang else list(range(len(pdf)))
    idx = idx[:max_trang]
    out = []
    for i in idx:
        img = pdf[i].render(scale=dpi / 72).to_pil().convert("L")
        out.append(pytesseract.image_to_string(img, lang="vie+eng", config="--psm 6"))
    pdf.close()
    return "\n".join(out), len(idx)
