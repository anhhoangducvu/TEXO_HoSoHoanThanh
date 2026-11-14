# TEXO · Kiểm tra Hồ sơ chất lượng dự án (NĐ 207/2026 – Phụ lục VII)

Công cụ nội bộ Phòng Kỹ thuật – Công ty CP TEXO Tư vấn và Đầu tư.
Anh em đoàn tư vấn tự kiểm tra từ xa **quyển danh mục hồ sơ hoàn thành** (giai đoạn, gói thầu, hạng mục, công trình) trước khi trình ký, thay vì chỉ đăng tải hồ sơ lên VPĐT rồi để đó.

## Kiểm tra theo 3 vòng (v2.0 – 14/11/2026)

| Vòng | Đọc gì | Kết luận |
|---|---|---|
| ① Đầu vào | Chỉ "vỏ" file: định dạng (.doc/.xls đời cũ, ảnh, file nén), dung lượng, file hỏng / đặt mật khẩu, **PDF ảnh scan** (từng trang), **ảnh chụp dán vào Word/Excel**, số trang. Sau đó nhận diện sơ bộ: loại tài liệu, nhà thầu, **thầu chính hay thầu phụ**, **nhà thầu lớn / hạng mục / nhỏ**, loại nghiệm thu | ĐẠT / ĐẠT CÓ LƯU Ý / TRẢ LẠI. Bộ nhiều file: file lỗi bị loại và ghi rõ, file đạt vẫn đi tiếp. Có phiếu vòng 1 và tin nhắn Zalo hướng dẫn gửi lại |
| ② Sơ bộ | Chỉ các **thành phần cơ bản**: hợp đồng, danh sách nhân sự, biên bản nghiệm thu (giai đoạn / gói thầu / hoàn thành / khối lượng đợt), danh mục NT vật liệu, NT công việc, bản vẽ hoàn công. Thầu phụ thêm: văn bản chấp thuận thầu phụ, HĐ tổng thầu / thầu chính với CĐT. Nhà thầu lớn thêm GPXD, thiết kế duyệt; nhà thầu lớn và hạng mục thêm danh mục thí nghiệm | ĐỦ HỒ SƠ CƠ BẢN / CÒN ĐIỂM CẦN LÀM RÕ / THIẾU HỒ SƠ CƠ BẢN (đề nghị bổ sung trước khi kiểm tra chi tiết). Phiếu vòng 2 + tin nhắn |
| ③ Chi tiết | Đối chiếu Phụ lục VII trong **phạm vi theo quy mô nhà thầu** | Phiếu kiểm tra Word A4 + Excel như bản trước |

Công cụ chỉ kiểm tra **hồ sơ của nhà thầu** – không yêu cầu hồ sơ của TVGS (báo cáo giám sát…).

**Quy mô nhà thầu quyết định độ dài danh mục phải kiểm tra** – danh mục hồ sơ hoàn thành theo PL VII là bộ hồ sơ chủ đầu tư tập hợp gửi cơ quan quản lý nhà nước:
- **Nhà thầu lớn** (tổng thầu, thầu chính, thiết kế – thi công, phần ngầm, kết cấu phần thân): rà đủ Phụ lục VII như trước.
- **Nhà thầu hạng mục** (cọc khoan nhồi, tường vây, cơ điện, PCCC, thang máy, mặt dựng…): bộ cốt lõi + hồ sơ kỹ thuật của hạng mục (thí nghiệm, biện pháp, thiết bị); GPXD chỉ đối chiếu; không hỏi pháp lý dự án.
- **Nhà thầu nhỏ** (sơn bả, hoàn thiện, camera, cung cấp – lắp đặt đơn giản…): chỉ bộ cốt lõi – không bắt lập lại danh mục đủ Phụ lục.
Ma trận chi tiết: cột "Hạng mục (tối đa)", "Nhỏ (tối đa)" trong `core/kb.py` (`PHAM_VI_QUY_MO`). Nhận diện tự động chỉ là gợi ý – người kiểm tra xác nhận ở mục "Phạm vi kiểm tra".

**PDF scan:** công cụ chỉ ra ngay file / trang scan và đề nghị gửi bản Word/Excel gốc (bản scan có chữ ký nộp kèm để lưu). Máy có Tesseract tiếng Việt thì hiện thêm ô "Thử đọc PDF scan bằng OCR" (tối đa 15 trang, độ chính xác thấp – phải đối chiếu lại). Streamlit Cloud: file `packages.txt` đã khai báo `tesseract-ocr`, `tesseract-ocr-vie`. Máy Windows: cài Tesseract (bản UB Mannheim, tick Vietnamese) nếu muốn dùng OCR – không cài vẫn chạy bình thường.

## Bộ lọc của vòng 3

| Bộ lọc | Nội dung |
|---|---|
| Đủ thành phần | Đối chiếu từng mục Phụ lục VII (I.1 → III.16) và các mục bổ sung của P.KT về hồ sơ nhà thầu (báo cáo hoàn thành của nhà thầu, nhật ký thi công) theo loại nghiệm thu **và quy mô nhà thầu** |
| Đúng hình thức | Mục là **văn bản** phải có số/ngày · mục cần **phê duyệt/chấp thuận** phải có văn bản phê duyệt · mục là **quyển hồ sơ** phải có danh mục chi tiết |
| Truy được trên VPĐT | Dòng nào chưa có mã HS · mã nào **gom nhiều mục** · mã trùng, sai định dạng · đối chiếu báo cáo đăng tải và danh sách xuất VPĐT |
| Nhất quán | Ngày kiểu Mỹ, ngày sai, ngày sau ngày nghiệm thu, ngày tương lai · chuỗi "lần 1, 2…" bị đứt · nghị định theo ngày nghiệm thu |

Mỗi mục còn có **câu hỏi kiểm tra chuyên môn** (ví dụ: hợp đồng là thầu chính hay thầu phụ, GPXD hay miễn phép theo trường hợp nào, đã có biên bản nghiệm thu nội bộ hệ thống PCCC chưa, chạy thử đơn động/liên động, biên bản NT hoàn thành có thời điểm bảo hành và đánh giá PCCC chưa…) để người kiểm tra đặt ra khi mở từng quyển. Chọn **vai trò nhà thầu**: tổng thầu/thầu chính thì kiểm tra kỹ pháp lý dự án; thầu phụ/nhà thầu nhỏ thì pháp lý dự án chỉ đối chiếu nếu có. Thiếu mã VPĐT chỉ ghi nhận "chưa đăng tải / chưa thể hiện", không làm trượt kết luận.

Đầu ra: phiếu vòng 1, phiếu vòng 2 (Word A4 mẫu TEXO) + tin nhắn Zalo; vòng 3 có màn hình tổng quan + **Phiếu kiểm tra Word A4** (letterhead TEXO, kết luận, đối chiếu PL VII, phát hiện, bản đồ mã VPĐT, câu hỏi cho đoàn, khối ký, phụ lục danh mục) + **Excel** (tổng quan, đối chiếu, danh mục đã đọc có lọc, bản đồ mã).

Đầu vào: `.docx`, `.pdf` có lớp chữ, `.xlsx`. File `.doc`/`.xls` cũ và PDF scan được vòng 1 chỉ ra kèm cách gửi lại.

**Không bắt buộc theo mẫu.** Phụ lục VII chỉ yêu cầu có danh mục (bản vẽ, hoàn công, nghiệm thu…), không quy định mẫu – công cụ đọc theo nội dung từng dòng (nhận diện cột theo tên: nội dung, số hiệu, ngày, đơn vị, mã TEXO-E…).

**Nạp nhiều danh mục rời cùng lúc** (v1.2): một quyển, hoặc nhiều file theo loại / theo đợt – VD danh mục NTCV đợt 1, 2, 3 + NT vật liệu đợt 1, 2 + hoàn công đợt 2 + hồ sơ thiết kế + thay đổi thiết kế + pháp lý. Mỗi file (mỗi sheet) được đọc như một danh mục, nhận diện loại và đợt từ tên file / tiêu đề, gộp thành một bộ rồi đối chiếu PL VII; có **ma trận đợt** chỉ ra đợt bị hụt (VD hoàn công mới có đợt 2 trong khi NTCV có đợt 1–3). Báo cáo đăng tải VPĐT nạp lẫn vào cũng được – tự chuyển sang phần đối chiếu mã.

**Mẫu danh mục tham khảo** (nút "Tải mẫu" trong app, `core/mau.py`): sheet hướng dẫn, danh mục tổng theo PL VII, và các sheet pháp lý, thiết kế, thay đổi thiết kế, NT vật liệu, thí nghiệm, NTCV, hoàn công, thiết bị, nghiệm thu – khác. Cột "Mục PL VII" (tùy chọn) giúp xếp đúng mục ngay; dòng STT = "VD" là ví dụ, app tự bỏ qua.

## Chạy trên máy (Windows)

1. Cài Python 3.10+ (tick "Add to PATH").
2. Nháy đúp `run_app.bat` → trình duyệt mở `http://localhost:8501`.
3. Mật khẩu mặc định: `texo2026` – đổi bằng biến môi trường `APP_PASSWORD` hoặc file `.streamlit/secrets.toml` (xem `secrets.toml.example`).

## Đưa lên mạng cho anh em dùng (Streamlit Community Cloud)

1. Đẩy thư mục này lên GitHub (repo private). `.gitignore` đã chặn file key và thư mục `samples/`.
2. share.streamlit.io → New app → chọn repo, file `app.py`.
3. Settings → Secrets: `APP_PASSWORD = "…"`. **Không** dán API key AI vào đây – mỗi người tự dán key của mình trong thanh bên.

## Bộ não AI (tùy chọn)

Không có key: chạy đầy đủ theo bộ quy tắc, miễn phí, dữ liệu không rời máy.
Có key (Claude / Gemini / OpenAI / endpoint tương thích OpenAI): dán key → **Lấy danh sách model** → chọn model → **Kiểm tra kết nối**. Tab "AI rà soát" gửi kết quả của bộ quy tắc cho AI để phân loại dòng chưa xếp được, nhận xét tổng quan, chỉ thêm rủi ro và câu hỏi cho đoàn. Khi bật AI, nội dung danh mục được gửi tới nhà cung cấp đã chọn.

Lỗi thường gặp: 401/403 – key sai hoặc thiếu Base URL · 404 – model đã bị gỡ, lấy lại danh sách · 429 – hết hạn mức, đổi model nhẹ hơn.

## Cấu trúc

```
app.py                 giao diện Streamlit
core/kb.py             CƠ SỞ TRI THỨC: Phụ lục VII → quy tắc (hình thức, áp dụng B/Đ, từ khóa, câu hỏi kiểm tra),
                       phạm vi theo quy mô nhà thầu, thành phần cốt lõi vòng 2, ngưỡng vòng 1
core/vong.py           3 vòng: vòng 1 (vỏ file + nhận diện), vòng 2 (thành phần cốt lõi), tin nhắn Zalo
core/cot_loi.py        nhận diện nhà thầu, tìm thành phần cốt lõi (dùng chung vòng 2, vòng 3)
core/ocr.py            đọc PDF scan bằng Tesseract (tùy chọn)
core/report_vong.py    phiếu vòng 1, vòng 2 (texo_docx.py – bộ dựng Word mẫu TEXO)
core/parser.py         đọc Word/PDF/Excel → dòng chuẩn hóa, cây cấp, mã VPĐT, thông tin chung
core/checker.py        các bộ lọc và kết luận
core/llm.py            gọi AI đa nhà cung cấp qua REST
core/report_docx.py    phiếu kiểm tra Word
core/report_xlsx.py    bảng tính Excel (texo_xlsx_kit)
assets/                logo TEXO, nguyên văn Phụ lục VII
```

## Nâng chất lượng không cần AI

Mở `core/kb.py`:
- Thêm từ khóa (viết **không dấu, chữ thường**) vào `tu_khoa` của mục tương ứng; từ loại trừ vào `loai_tru`.
- Đổi mức áp dụng B/Đ/- theo loại nghiệm thu trong `ap_dung`.
- `MUC_COT_LOI`: mục thiếu là 🔴 Phải xử lý.
- `CAU_HOI`: câu đề nghị đoàn bổ sung · `CAU_HOI_KT`: câu hỏi kiểm tra theo từng mục · `I9_THANH_PHAN`, `III8_THANH_PHAN`: thành phần tối thiểu.

- `PHAM_VI_QUY_MO`, `MUC_COT_LOI_QM`: phạm vi theo quy mô nhà thầu · `NT_LON`, `NT_HANG_MUC`, `NT_NHO`, `NT_PHU`: từ khóa nhận diện nhà thầu · `THANH_PHAN_COT_LOI`: thành phần vòng 2 · `VONG1`: ngưỡng dung lượng, số trang, trang scan.

Ma trận áp dụng theo loại nghiệm thu và quy mô nhà thầu là cách áp dụng nội bộ của P.KT, không phải nội dung Nghị định.

Chạy không giao diện (3 vòng): `python kiem_tra_danh_muc.py <file…> [--vong 1|2|3] [--quy-mo lon|hang_muc|nho] [--vai-tro chinh|phu] [--ocr]`.

Lõi `core/` dùng chung với skill `texo-kiemtra-hoso-chatluong` (thư mục `scripts/core/`) – sửa một nơi, chép sang nơi kia.

Văn bản pháp lý, tiêu chuẩn dẫn trong hồ sơ: kiểm tra hiệu lực bản mới nhất bằng công cụ **TEXO Legal Reviewer**.

Người xây dựng: Hoàng Đức Vũ – Trưởng phòng Kỹ thuật, Công ty CP TEXO Tư vấn và Đầu tư.
