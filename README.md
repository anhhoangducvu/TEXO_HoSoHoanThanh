# TEXO · Kiểm tra Hồ sơ chất lượng dự án (NĐ 207/2026 – Phụ lục VII)

Công cụ nội bộ Phòng Kỹ thuật – Công ty CP TEXO Tư vấn và Đầu tư.
Anh em đoàn tư vấn tự kiểm tra từ xa **quyển danh mục hồ sơ hoàn thành** (giai đoạn, gói thầu, hạng mục, công trình) trước khi trình ký, thay vì chỉ đăng tải hồ sơ lên VPĐT rồi để đó.

## Công cụ làm gì

| Bộ lọc | Nội dung |
|---|---|
| Đủ thành phần | Đối chiếu từng mục Phụ lục VII (I.1 → III.16) và 3 mục kiểm tra bổ sung của P.KT (báo cáo hoàn thành TVGS, báo cáo nhà thầu, nhật ký) theo loại nghiệm thu: giai đoạn/bộ phận, hoàn thành gói thầu, hoàn thành hạng mục/công trình |
| Đúng hình thức | Mục là **văn bản** phải có số/ngày · mục cần **phê duyệt/chấp thuận** phải có văn bản phê duyệt · mục là **quyển hồ sơ** (hoàn công, NTCV, vật liệu, thí nghiệm…) phải có danh mục chi tiết, không chỉ một dòng tên quyển |
| Truy được trên VPĐT | Dòng nào chưa có mã HS · mã nào **gom nhiều mục** (nén chung một cục) · mã trùng, sai định dạng, dùng mã VB thay mã HS · đối chiếu với báo cáo đăng tải của đoàn và danh sách xuất từ VPĐT |
| Nhất quán | Ngày kiểu Mỹ, ngày sai, ngày sau ngày nghiệm thu, ngày trong tương lai · chuỗi "lần 1, 2, … " bị đứt · dòng kê sẵn chưa có hồ sơ · nghị định áp dụng theo ngày nghiệm thu (trước 01/7/2026 → NĐ 06/2021) |

Mỗi mục còn có **câu hỏi kiểm tra chuyên môn** (ví dụ: hợp đồng là thầu chính hay thầu phụ, GPXD hay miễn phép theo trường hợp nào, đã có biên bản nghiệm thu nội bộ hệ thống PCCC chưa, chạy thử đơn động/liên động, biên bản NT hoàn thành có thời điểm bảo hành và đánh giá PCCC chưa…) để người kiểm tra đặt ra khi mở từng quyển. Chọn **vai trò nhà thầu**: tổng thầu/thầu chính thì kiểm tra kỹ pháp lý dự án; thầu phụ/nhà thầu nhỏ thì pháp lý dự án chỉ đối chiếu nếu có. Thiếu mã VPĐT chỉ ghi nhận "chưa đăng tải / chưa thể hiện", không làm trượt kết luận.

Đầu ra: màn hình tổng quan + **Phiếu kiểm tra Word A4** (letterhead TEXO, kết luận, đối chiếu PL VII, phát hiện, bản đồ mã VPĐT, câu hỏi cho đoàn, khối ký, phụ lục danh mục) + **Excel** (tổng quan, đối chiếu, danh mục đã đọc có lọc, bản đồ mã).

Đầu vào: `.docx`, `.pdf` có lớp chữ (không phải scan), `.xlsx`. File `.doc` cũ: mở bằng Word, lưu lại `.docx`.

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
core/kb.py             CƠ SỞ TRI THỨC: Phụ lục VII → quy tắc (hình thức, áp dụng B/Đ, từ khóa, câu hỏi kiểm tra)
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

Ma trận áp dụng theo loại nghiệm thu là cách áp dụng nội bộ của P.KT, không phải nội dung Nghị định.
