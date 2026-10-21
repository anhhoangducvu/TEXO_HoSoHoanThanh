# -*- coding: utf-8 -*-
"""
CƠ SỞ TRI THỨC – Phụ lục VII NĐ 207/2026/NĐ-CP (Danh mục hồ sơ hoàn thành công trình)
chuyển thành bộ quy tắc máy đọc được.

Mỗi mục có:
  code        : mã mục PL VII (I.1 … III.16) hoặc T.x (kiểm tra bổ sung của P.KT)
  ten         : tên rút gọn
  nguyen_van  : trích yêu cầu (rút gọn từ nguyên văn)
  hinh_thuc   : "VB"     – văn bản đơn lẻ có số/ngày (quyết định, giấy phép, thông báo)
                "PD"     – phải có văn bản phê duyệt/chấp thuận/thẩm định kèm theo
                "QUYEN"  – một quyển/tập hồ sơ: danh mục chỉ là mục lục, phải xem quyển
  can_dm_kem  : PL VII yêu cầu "có danh mục … kèm theo" (bản vẽ, thay đổi thiết kế…)
  neu_co      : PL VII ghi "(nếu có)" → thiếu thì hỏi, không tự đánh trượt
  ap_dung     : {"GD": B|Đ|-, "HT": B|Đ|-}
                GD = nghiệm thu giai đoạn / bộ phận / hoàn thành gói thầu (Điều 23)
                HT = nghiệm thu hoàn thành hạng mục công trình, công trình (Điều 24)
                B  = phải có hoặc phải nêu căn cứ · Đ = đối chiếu nếu có · - = không xét
  tu_khoa     : biểu thức chính quy trên văn bản đã BỎ DẤU, chữ thường
  loai_tru    : biểu thức loại trừ (nếu khớp thì KHÔNG gán mục này)

Ma trận áp dụng là cách áp dụng nội bộ của Phòng Kỹ thuật, không phải nội dung Nghị định.
Muốn nâng chất lượng nhận diện mà không cần AI: bổ sung từ khóa vào đây.
"""

NGAY_HIEU_LUC_207 = (2026, 7, 1)

NHOM = {
    "I": "HỒ SƠ CHUẨN BỊ ĐẦU TƯ XÂY DỰNG VÀ HỢP ĐỒNG",
    "II": "HỒ SƠ KHẢO SÁT XÂY DỰNG, THIẾT KẾ XÂY DỰNG CÔNG TRÌNH",
    "III": "HỒ SƠ QUẢN LÝ THI CÔNG XÂY DỰNG CÔNG TRÌNH",
    "T": "KIỂM TRA BỔ SUNG CỦA PHÒNG KỸ THUẬT (ngoài PL VII)",
}

LOAI_NT = {
    "GD": "Nghiệm thu giai đoạn / bộ phận công trình (Điều 23)",
    "GT": "Nghiệm thu hoàn thành gói thầu (Điều 23.1.b)",
    "HT": "Nghiệm thu hoàn thành hạng mục công trình / công trình (Điều 24)",
}
# Gói thầu áp dụng cột GD của ma trận
COT_MA_TRAN = {"GD": "GD", "GT": "GD", "HT": "HT"}

MUC = [
    # ------------------------------------------------------------------ I
    dict(code="I.1", ten="Chủ trương đầu tư, BC nghiên cứu tiền khả thi",
         nguyen_van="Quyết định chủ trương đầu tư xây dựng và Báo cáo nghiên cứu tiền khả thi (nếu có).",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "Đ", "HT": "B"},
         tu_khoa=[r"chu truong dau tu", r"tien kha thi"]),
    dict(code="I.2", ten="QĐ phê duyệt dự án, BCNCKT / BCKTKT",
         nguyen_van="Quyết định phê duyệt dự án đầu tư xây dựng công trình và Báo cáo nghiên cứu khả thi hoặc Báo cáo kinh tế - kỹ thuật.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=False, ap_dung={"GD": "Đ", "HT": "B"},
         tu_khoa=[r"phe duyet (dieu chinh )?du an", r"du an dau tu .*ke hoach lua chon", r"nghien cuu kha thi",
                  r"kinh te\W*ky thuat", r"\bbcnckt\b", r"\bbcktkt\b", r"quyet dinh dau tu"]),
    dict(code="I.3", ten="Nhiệm vụ thiết kế, thẩm định dự án, TKCS",
         nguyen_van="Nhiệm vụ thiết kế, các văn bản thẩm định, tham gia ý kiến của cơ quan liên quan trong thẩm định dự án và thiết kế cơ sở.",
         hinh_thuc="PD", can_dm_kem=False, neu_co=False, ap_dung={"GD": "Đ", "HT": "B"},
         tu_khoa=[r"nhiem vu thiet ke", r"thiet ke co so", r"\btkcs\b", r"tham dinh du an", r"thong bao ket qua tham dinh du an"]),
    dict(code="I.4", ten="Phương án đền bù GPMB, tái định cư",
         nguyen_van="Phương án đền bù giải phóng mặt bằng và xây dựng tái định cư (nếu có).",
         hinh_thuc="PD", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"giai phong mat bang", r"den bu", r"tai dinh cu", r"\bgpmb\b"]),
    dict(code="I.5", ten="Thỏa thuận quy hoạch, đấu nối, ĐTM, an toàn",
         nguyen_van="Văn bản của cơ quan có thẩm quyền về thỏa thuận quy hoạch, đấu nối ngoài hàng rào, đánh giá tác động môi trường, bảo đảm an toàn…",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "B"},
         tu_khoa=[r"quy hoach", r"thoa thuan dau noi", r"tac dong moi truong", r"\bdtm\b", r"an toan giao thong",
                  r"cong trinh lan can", r"chap thuan .*dau noi"]),
    dict(code="I.6", ten="Giao đất, cho thuê đất",
         nguyen_van="Quyết định giao đất, cho thuê đất hoặc hợp đồng thuê đất.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=False, ap_dung={"GD": "-", "HT": "B"},
         tu_khoa=[r"giao dat", r"thue dat", r"quyen su dung dat", r"so do"]),
    dict(code="I.7", ten="Giấy phép xây dựng",
         nguyen_van="Giấy phép xây dựng, trừ trường hợp được miễn.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"giay phep xay dung", r"\bgpxd\b", r"mien giay phep"],
         loai_tru=[r"thuc hien giay phep"]),
    dict(code="I.8", ten="Lựa chọn nhà thầu, hợp đồng CĐT – nhà thầu",
         nguyen_van="Quyết định chỉ định thầu, phê duyệt kết quả lựa chọn nhà thầu và hợp đồng xây dựng giữa chủ đầu tư với các nhà thầu.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"hop dong", r"chi dinh thau", r"lua chon nha thau", r"trung thau", r"phu luc (so )?\d+", r"phu luc hop dong",
                  r"\bhdxd\b", r"\bhdkt\b"],
         loai_tru=[r"hop dong lao dong", r"hop dong mua ban", r"hop dong (cung cap|thue) (may|thiet bi)",
                   r"thanh toan", r"quyet toan", r"nha cung cap", r"nha thau phu\b(?!\s*hop)"]),
    dict(code="I.9", ten="Năng lực nhà thầu",
         nguyen_van="Các tài liệu chứng minh năng lực của các nhà thầu theo quy định.",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"nang luc", r"dang ky kinh doanh", r"dang ky doanh nghiep", r"chung chi hanh nghe", r"ban chi huy",
                  r"chi huy truong", r"can bo (quan ly|ky thuat)", r"nhan su", r"nha thau phu\b(?!\s*hop)", r"phong thi nghiem",
                  r"\blas\b", r"bang cap", r"bo nhiem", r"so do to chuc"]),
    dict(code="I.10", ten="Hồ sơ khác giai đoạn chuẩn bị đầu tư",
         nguyen_van="Các hồ sơ, tài liệu khác có liên quan trong giai đoạn chuẩn bị đầu tư xây dựng.",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"chuan bi dau tu"]),
    # ------------------------------------------------------------------ II
    dict(code="II.1", ten="Nhiệm vụ, phương án, báo cáo khảo sát",
         nguyen_van="Nhiệm vụ khảo sát, phương án kỹ thuật khảo sát, báo cáo kết quả khảo sát xây dựng.",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=False, ap_dung={"GD": "-", "HT": "B"},
         tu_khoa=[r"khao sat", r"dia chat", r"dia hinh"],
         loai_tru=[r"phe duyet (bao cao )?(ket qua )?khao sat"]),
    dict(code="II.2", ten="Phê duyệt báo cáo kết quả khảo sát",
         nguyen_van="Văn bản phê duyệt báo cáo kết quả khảo sát xây dựng (khi không phê duyệt trực tiếp lên báo cáo).",
         hinh_thuc="PD", can_dm_kem=False, neu_co=False, ap_dung={"GD": "-", "HT": "B"},
         tu_khoa=[r"phe duyet (bao cao )?(ket qua )?khao sat", r"nghiem thu (ket qua )?khao sat"]),
    dict(code="II.3", ten="Thẩm tra, thẩm định, QĐ phê duyệt thiết kế + danh mục bản vẽ, chỉ dẫn kỹ thuật",
         nguyen_van="Kết quả thẩm tra, thẩm định thiết kế; QĐ phê duyệt thiết kế kèm hồ sơ thiết kế đã phê duyệt (có danh mục bản vẽ kèm theo); chỉ dẫn kỹ thuật.",
         hinh_thuc="PD", can_dm_kem=True, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"thiet ke ban ve thi cong", r"\btkbvtc\b", r"\bbvtc\b", r"tham tra thiet ke", r"tham dinh thiet ke",
                  r"phe duyet (ho so )?thiet ke", r"ho so thiet ke", r"chi dan ky thuat", r"ban ve thiet ke",
                  r"thiet ke (ket cau|kien truc|dien|nuoc|mep|co dien)", r"danh muc ban ve(?! hoan cong)", r"du toan"],
         loai_tru=[r"hoan cong", r"thay doi thiet ke", r"dieu chinh(,)? (bo sung )?(ho so )?thiet ke", r"nhiem vu thiet ke",
                   r"thiet ke co so", r"nghiem thu (ho so )?thiet ke"]),
    dict(code="II.4", ten="Thông báo chấp thuận nghiệm thu thiết kế",
         nguyen_van="Văn bản thông báo chấp thuận nghiệm thu thiết kế xây dựng công trình.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=False, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"nghiem thu (ho so )?thiet ke", r"chap thuan nghiem thu thiet ke"]),
    dict(code="II.5", ten="Hồ sơ khác giai đoạn khảo sát, thiết kế",
         nguyen_van="Các văn bản, tài liệu, hồ sơ khác có liên quan đến giai đoạn khảo sát, thiết kế.",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"ban ve trien khai", r"shop ?drawing", r"\bshop\b"]),
    # ------------------------------------------------------------------ III
    dict(code="III.1", ten="Danh mục thay đổi thiết kế + văn bản phê duyệt",
         nguyen_van="Danh mục các thay đổi thiết kế trong quá trình thi công và các văn bản thẩm định, phê duyệt của cấp có thẩm quyền.",
         hinh_thuc="PD", can_dm_kem=True, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"thay doi thiet ke", r"dieu chinh(,)? (bo sung )?(ho so )?thiet ke", r"thiet ke dieu chinh",
                  r"xu ly (ky thuat|thiet ke)", r"phat sinh", r"bien ban hien truong"]),
    dict(code="III.2", ten="Bản vẽ hoàn công (có danh mục bản vẽ)",
         nguyen_van="Bản vẽ hoàn công (có danh mục bản vẽ kèm theo).",
         hinh_thuc="QUYEN", can_dm_kem=True, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"hoan cong"]),
    dict(code="III.3", ten="Kế hoạch, biện pháp kiểm soát chất lượng",
         nguyen_van="Các kế hoạch, biện pháp kiểm tra, kiểm soát chất lượng thi công xây dựng công trình.",
         hinh_thuc="PD", can_dm_kem=False, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"bien phap thi cong", r"tien do thi cong", r"ke hoach (kiem tra|quan ly|kiem soat)? ?chat luong",
                  r"he thong quan ly chat luong", r"ke hoach nghiem thu", r"ke hoach thi nghiem", r"bien phap( to chuc)? thi cong",
                  r"quy trinh kiem soat", r"to chuc thi cong", r"\bbptc\b"],
         loai_tru=[r"an toan lao dong", r"\batld\b", r"pccc|phong chay"]),
    dict(code="III.4", ten="Xuất xứ, hợp quy, hợp chuẩn vật liệu – sản phẩm",
         nguyen_van="Chứng từ xuất xứ, nhãn mác, công bố tiêu chuẩn; chứng nhận/công bố hợp quy; chứng nhận hợp chuẩn (nếu có).",
         hinh_thuc="QUYEN", can_dm_kem=True, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"xuat xu", r"\bco\b.*\bcq\b", r"\bcq\b", r"hop quy", r"hop chuan", r"vat lieu dau vao", r"vat tu dau vao",
                  r"nghiem thu vat (lieu|tu)", r"phe duyet vat (lieu|tu)", r"chung chi chat luong", r"nha san xuat",
                  r"nha cung cap", r"hop dong mua ban", r"phieu xuat (kho|xuong)", r"vat lieu"],
         loai_tru=[r"thi nghiem"]),
    dict(code="III.5", ten="Kết quả quan trắc, đo đạc, thí nghiệm",
         nguyen_van="Các kết quả quan trắc (nếu có), đo đạc, thí nghiệm trong quá trình thi công.",
         hinh_thuc="QUYEN", can_dm_kem=True, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"thi nghiem", r"quan trac", r"do dac", r"lay mau", r"\bnen mau\b", r"do lun", r"do nghieng", r"trac dac"],
         loai_tru=[r"doi chung", r"thu tai", r"nen tinh", r"phong thi nghiem", r"kha nang chiu luc", r"sieu am", r"\bpda\b", r"\bpit\b"]),
    dict(code="III.6", ten="Biên bản nghiệm thu công việc, bộ phận, giai đoạn",
         nguyen_van="Các biên bản nghiệm thu công việc xây dựng, nghiệm thu bộ phận hoặc giai đoạn (nếu có) trong quá trình thi công.",
         hinh_thuc="QUYEN", can_dm_kem=True, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"nghiem thu cong viec", r"\bntcv\b", r"nghiem thu bo phan", r"nghiem thu giai doan", r"ho so chat luong",
                  r"ho so nghiem thu", r"bien ban nghiem thu", r"hoan thanh goi thau", r"nghiem thu noi bo"],
         loai_tru=[r"hoan thanh (hang muc|cong trinh|dua vao su dung)", r"thanh lap", r"quyet dinh", r"nhan su", r"vat (lieu|tu)", r"thiet ke", r"khao sat", r"pccc|phong chay"]),
    dict(code="III.7", ten="Thí nghiệm đối chứng, kiểm định, thử tải",
         nguyen_van="Kết quả thí nghiệm đối chứng, kiểm định chất lượng công trình, thử nghiệm khả năng chịu lực kết cấu (nếu có).",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=True, ap_dung={"GD": "Đ", "HT": "Đ"},
         tu_khoa=[r"doi chung", r"kiem dinh chat luong", r"thu tai", r"nen tinh", r"kha nang chiu luc", r"sieu am",
                  r"\bpda\b", r"\bpit\b", r"thi nghiem coc", r"kiem dinh"],
         loai_tru=[r"kiem dinh (an toan|thiet bi|may|ky thuat an toan)", r"thiet bi nang", r"\bthi nghiem va kiem dinh\b.*cong ty"]),
    dict(code="III.8", ten="Hồ sơ QLCL thiết bị lắp đặt",
         nguyen_van="Hồ sơ quản lý chất lượng của thiết bị lắp đặt vào công trình.",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=False, ap_dung={"GD": "-", "HT": "B"},
         tu_khoa=[r"thiet bi (lap dat|cong nghe)", r"chay thu", r"van hanh thu", r"nghiem thu thiet bi", r"lap dat thiet bi"],
         loai_tru=[r"may moc thiet bi (thi cong)?$", r"ho so may moc"]),
    dict(code="III.9", ten="Quy trình vận hành, quy trình bảo trì",
         nguyen_van="Quy trình vận hành, khai thác công trình (nếu có); quy trình bảo trì công trình.",
         hinh_thuc="PD", can_dm_kem=False, neu_co=False, ap_dung={"GD": "-", "HT": "B"},
         tu_khoa=[r"quy trinh (van hanh|bao tri|khai thac)", r"bao tri", r"huong dan (su dung|van hanh)"]),
    dict(code="III.10a", ten="Di dân lòng hồ, di tích lịch sử – văn hóa",
         nguyen_van="Văn bản của cơ quan có thẩm quyền về di dân vùng lòng hồ, khảo sát di tích lịch sử, văn hóa (nếu có).",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"di dan", r"long ho", r"di tich"]),
    dict(code="III.10b", ten="PCCC: nghiệm thu hệ thống / văn bản của cơ quan có thẩm quyền",
         nguyen_van="Văn bản thỏa thuận, chấp thuận, xác nhận của cơ quan nhà nước có thẩm quyền về an toàn phòng cháy, chữa cháy.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "Đ", "HT": "B"},
         tu_khoa=[r"(nghiem thu|tham duyet|chap thuan|ket qua|giay chung nhan|van ban).*(pccc|phong chay|chua chay)",
                  r"(pccc|phong chay chua chay).*(nghiem thu|tham duyet|chap thuan)"],
         loai_tru=[r"noi quy", r"tieu lenh", r"doi (pccc|phong chay)", r"huan luyen", r"trong (pham vi )?thi cong",
                   r"ban atvsld"]),
    dict(code="III.10c", ten="Chấp thuận về an toàn môi trường",
         nguyen_van="Văn bản của cơ quan có thẩm quyền về an toàn môi trường.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "B"},
         tu_khoa=[r"giay phep moi truong", r"(xac nhan|chap thuan|van ban).*moi truong", r"cong trinh bao ve moi truong"],
         loai_tru=[r"ve sinh moi truong", r"\bvsmt\b", r"noi quy", r"ke hoach"]),
    dict(code="III.10d", ten="An toàn lao động, an toàn vận hành thiết bị (kiểm định)",
         nguyen_van="Văn bản của cơ quan có thẩm quyền về an toàn lao động, an toàn vận hành hệ thống thiết bị công trình, thiết bị công nghệ.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "Đ", "HT": "B"},
         tu_khoa=[r"kiem dinh (an toan|thiet bi|may|ky thuat an toan)", r"thiet bi nang", r"an toan van hanh",
                  r"thang may.*kiem dinh", r"kiem dinh.*thang may", r"binh ap luc"]),
    dict(code="III.10đ", ten="Thực hiện giấy phép xây dựng",
         nguyen_van="Văn bản của cơ quan có thẩm quyền về thực hiện Giấy phép xây dựng (trường hợp phải có GPXD).",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"thuc hien giay phep", r"kiem tra .*giay phep"]),
    dict(code="III.10e", ten="Cho phép đấu nối hạ tầng kỹ thuật",
         nguyen_van="Văn bản cho phép đấu nối với công trình hạ tầng kỹ thuật và các công trình khác có liên quan.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "B"},
         tu_khoa=[r"cho phep dau noi", r"dau noi (dien|nuoc|cap nuoc|thoat nuoc|ha tang|giao thong)"],
         loai_tru=[r"thoa thuan dau noi"]),
    dict(code="III.10g", ten="Hoàn thành hạ tầng kỹ thuật theo kế hoạch dự án",
         nguyen_van="Văn bản của cơ quan chuyên môn về việc hoàn thành các công trình hạ tầng kỹ thuật có liên quan của dự án.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"hoan thanh (cac )?(cong trinh )?ha tang ky thuat"]),
    dict(code="III.10h", ten="Văn bản khác theo pháp luật chuyên ngành",
         nguyen_van="Các văn bản khác theo quy định của pháp luật có liên quan.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"phap luat chuyen nganh"]),
    dict(code="III.11", ten="Hồ sơ giải quyết sự cố",
         nguyen_van="Hồ sơ giải quyết sự cố công trình (nếu có).",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=True, ap_dung={"GD": "Đ", "HT": "Đ"},
         tu_khoa=[r"su co"]),
    dict(code="III.12", ten="Phụ lục tồn tại cần khắc phục",
         nguyen_van="Phụ lục các tồn tại cần sửa chữa, khắc phục (nếu có) sau khi đưa vào sử dụng.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "Đ", "HT": "Đ"},
         tu_khoa=[r"ton tai", r"khac phuc", r"sua chua"]),
    dict(code="III.13", ten="Biên bản nghiệm thu hoàn thành hạng mục / công trình",
         nguyen_van="Biên bản nghiệm thu hoàn thành hạng mục công trình, công trình xây dựng.",
         hinh_thuc="VB", can_dm_kem=False, neu_co=False, ap_dung={"GD": "-", "HT": "B"},
         tu_khoa=[r"nghiem thu hoan thanh (toan bo )?(hang muc|cong trinh|dua vao su dung|.*dua vao su dung)",
                  r"bien ban nghiem thu hoan thanh(?! goi thau)", r"\bbbnt\W*htmct\b", r"\bhthmct\b"],
         loai_tru=[r"phieu yeu cau", r"pccc", r"thong bao", r"ket qua (kiem tra|nghiem thu hoan thanh cong trinh du an)"]),
    dict(code="III.14", ten="Thông báo của cơ quan có thẩm quyền (khoản 4 Điều 57 Luật XD 135/2025)",
         nguyen_van="Văn bản thông báo của cơ quan có thẩm quyền quy định tại khoản 4 Điều 57 Luật Xây dựng 135/2025/QH15 (nếu có).",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"thong bao .*(chap thuan|ket qua) nghiem thu", r"ket qua nghiem thu hoan thanh cong trinh du an",
                  r"so xay dung", r"cuc giam dinh", r"co quan chuyen mon"]),
    dict(code="III.15", ten="Hồ sơ kiểm tra công tác nghiệm thu",
         nguyen_van="Các hồ sơ, tài liệu trong quá trình kiểm tra công tác nghiệm thu theo quy định (nếu có).",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "Đ"},
         tu_khoa=[r"kiem tra cong tac nghiem thu"]),
    dict(code="III.16", ten="Hồ sơ khác giai đoạn thi công và nghiệm thu",
         nguyen_van="Các hồ sơ/văn bản/tài liệu khác có liên quan trong giai đoạn thi công xây dựng và nghiệm thu.",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=True, ap_dung={"GD": "Đ", "HT": "Đ"},
         tu_khoa=[r"ban giao (moc|mat bang|tim|coc)", r"an toan lao dong", r"\batld\b", r"\batvsld\b", r"ve sinh moi truong",
                  r"\bvsmt\b", r"bao hiem", r"cong nhan", r"may moc", r"noi quy", r"tieu lenh", r"phong chay|pccc", r"bao ho",
                  r"huan luyen", r"so cap cuu", r"lut bao", r"cuu ho", r"phieu yeu cau nghiem thu", r"anh (hien truong|thi cong)",
                  r"bao cao (tuan|thang|dinh ky)"]),
    # ------------------------------------------------------------------ T (bổ sung P.KT)
    dict(code="T.1", ten="Báo cáo hoàn thành công tác giám sát (Phụ lục IVb)",
         nguyen_van="Báo cáo hoàn thành công tác giám sát thi công gói thầu/giai đoạn/hạng mục/công trình của TVGS (Phụ lục IVb NĐ 207).",
         hinh_thuc="VB", can_dm_kem=False, neu_co=False, ap_dung={"GD": "B", "HT": "B"},
         tu_khoa=[r"bao cao .*(tu van giam sat|tvgs|cong tac giam sat)", r"bao cao hoan thanh cong tac giam sat"]),
    dict(code="T.2", ten="Báo cáo hoàn thành của nhà thầu thi công",
         nguyen_van="Báo cáo hoàn thành hạng mục/gói thầu của nhà thầu thi công (căn cứ đề nghị nghiệm thu).",
         hinh_thuc="VB", can_dm_kem=False, neu_co=True, ap_dung={"GD": "Đ", "HT": "Đ"},
         tu_khoa=[r"bao cao hoan thanh"], loai_tru=[r"giam sat|tvgs"]),
    dict(code="T.3", ten="Nhật ký thi công xây dựng",
         nguyen_van="Nhật ký thi công xây dựng công trình (căn cứ nghiệm thu, đối chiếu với biên bản).",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=False, ap_dung={"GD": "Đ", "HT": "B"},
         tu_khoa=[r"nhat ky"]),
    dict(code="T.9", ten="Hồ sơ thanh toán, quyết toán, khối lượng (ngoài PL VII)",
         nguyen_van="Hồ sơ giá trị/thanh toán/quyết toán không thuộc danh mục hồ sơ hoàn thành – nên lưu tách riêng.",
         hinh_thuc="QUYEN", can_dm_kem=False, neu_co=True, ap_dung={"GD": "-", "HT": "-"},
         tu_khoa=[r"(gia tri|ho so) thanh toan", r"\bthanh toan\b", r"quyet toan(?! (cong trinh|hang muc)$)", r"tong hop khoi luong",
                  r"khoi luong (quyet toan|thanh toan|hoan thanh)", r"bao lanh", r"hoa don"],
         loai_tru=[r"ho so chat luong", r"hoan cong", r"nhat ky", r"nghiem thu", r"ban ve", r"thi nghiem"]),
]

MUC_BY_CODE = {m["code"]: m for m in MUC}

# Hồ sơ pháp lý dự án do Chủ đầu tư lập/lưu: danh mục của hạng mục/gói thầu có thể chỉ DẪN số hiệu.
CDT_LUU = {"I.1", "I.2", "I.3", "I.4", "I.5", "I.6", "I.7", "I.10", "II.1", "II.2", "II.4", "II.5",
           "III.10a", "III.10c", "III.10đ", "III.10e", "III.10g", "III.10h", "III.14", "III.15"}
for _m in MUC:
    _m["chu_the"] = "CĐT" if _m["code"] in CDT_LUU else "Nhà thầu / TVGS"

# Thứ tự ưu tiên khi một dòng khớp nhiều mục: mục cụ thể trước, mục "khác" sau.
UU_TIEN = ["III.13", "III.14", "III.15", "T.1", "T.2", "III.10b", "III.10d", "III.10c", "III.10e", "III.10đ",
           "III.10g", "III.10a", "II.2", "II.4", "III.2", "III.1", "III.7", "III.8", "III.9", "III.11", "III.12",
           "III.5", "III.4", "III.6", "T.3", "T.9", "I.3", "I.1", "I.2", "I.4", "I.6", "I.7", "II.3", "II.1", "II.5", "I.5",
           "III.3", "I.9", "I.8", "III.16", "I.10", "III.10h"]

# Mục cốt lõi: thiếu là 🔴 (Phải xử lý) thay vì 🟠
MUC_COT_LOI = {"GD": {"I.8", "II.3", "III.2", "III.6", "T.1"},
               "HT": {"I.2", "I.8", "II.3", "III.2", "III.6", "III.13", "T.1"}}

HINH_THUC_LABEL = {
    "VB": "Văn bản có số/ngày",
    "PD": "Phải có văn bản phê duyệt / chấp thuận",
    "QUYEN": "Quyển hồ sơ (danh mục chỉ là mục lục)",
}

# Câu hỏi gợi ý cho đoàn tư vấn khi thiếu mục (rule-based)
CAU_HOI = {
    "I.2": "Đề nghị bổ sung số, ngày QĐ phê duyệt dự án (hoặc BCKTKT) làm căn cứ.",
    "I.7": "Bổ sung số, ngày Giấy phép xây dựng; nếu được miễn phép thì ghi rõ miễn theo trường hợp nào và dẫn tài liệu thể hiện việc miễn.",
    "I.8": "Bổ sung hợp đồng thi công (số, ngày) và các phụ lục hợp đồng của gói thầu đang nghiệm thu.",
    "II.3": "Bổ sung số, ngày QĐ phê duyệt thiết kế (TKBVTC) và danh mục bản vẽ kèm theo.",
    "III.1": "Có thay đổi thiết kế trong thi công không? Nếu không có, danh mục phải ghi rõ 'Không có thay đổi'.",
    "III.2": "Bổ sung quyển bản vẽ hoàn công kèm danh mục bản vẽ (số hiệu bản vẽ, ngày lập).",
    "III.4": "Bổ sung danh mục nghiệm thu vật liệu đầu vào kèm CO/CQ, hợp quy theo từng đợt.",
    "III.5": "Bổ sung danh mục kết quả thí nghiệm (số phiếu, ngày, đơn vị thí nghiệm) và đối chiếu với thiết kế.",
    "III.6": "Bổ sung danh mục biên bản nghiệm thu công việc (số biên bản, ngày, phạm vi) đủ cho phạm vi nghiệm thu.",
    "III.8": "Hạng mục có thiết bị lắp đặt không? Nếu có, bổ sung hồ sơ QLCL thiết bị (CO/CQ, chạy thử).",
    "III.9": "Quy trình bảo trì, quy trình vận hành do bên nào lập (thiết kế / nhà thầu cung cấp – lắp đặt thiết bị)? Đề nghị bổ sung hoặc cho biết nơi lưu.",
    "III.10b": "Đã có biên bản nghiệm thu (nội bộ) hệ thống PCCC trước khi đưa công trình vào sử dụng chưa? Có văn bản của cơ quan có thẩm quyền về PCCC (nếu thuộc diện) không?",
    "III.13": "Bổ sung biên bản nghiệm thu hoàn thành hạng mục/công trình (đủ thành phần ký theo Điều 24.6).",
    "T.1": "Bổ sung báo cáo hoàn thành công tác giám sát của TVGS theo Phụ lục IVb NĐ 207.",
    "T.3": "Bổ sung nhật ký thi công để đối chiếu ngày nghiệm thu.",
}


# ---------------------------------------------------------------------------------------------
# CÂU HỎI KIỂM TRA THEO TỪNG MỤC (ghi chú chuyên môn của Trưởng phòng KT trên Phụ lục VII).
# Dùng để đặt câu hỏi cho đoàn, không tự kết luận đạt / không đạt.
CAU_HOI_KT = {
    "I": ["Nhà thầu đang nghiệm thu là tổng thầu / thầu chính hay thầu phụ? Hồ sơ pháp lý dự án và pháp lý nhà thầu "
          "cần kiểm tra kỹ khi là nhà thầu lớn, tổng thầu hoặc thầu chính thi công."],
    "I.1": ["Chủ trương đầu tư đã đủ để xác minh cấp công trình và pháp lý dự án chưa?"],
    "I.3": ["Nhiệm vụ thiết kế, văn bản thẩm định dự án / thiết kế cơ sở có khớp với hồ sơ thiết kế đang thi công không?"],
    "I.5": ["Với công trình giao thông, công trình lớn ảnh hưởng tới cộng đồng: đã có các văn bản về quy hoạch, đấu nối, "
            "ĐTM, an toàn giao thông, an toàn công trình lân cận chưa?"],
    "I.7": ["Có Giấy phép xây dựng không? Nếu được miễn thì miễn theo trường hợp nào, có tài liệu thể hiện không?"],
    "I.8": ["Hợp đồng trong danh mục là hợp đồng thầu chính hay thầu phụ? Nếu chỉ có hợp đồng thầu phụ, đề nghị bổ sung "
            "hợp đồng tổng thầu / hợp đồng thầu chính với chủ đầu tư."],
    "I.9": ["Đã có tối thiểu: hồ sơ năng lực (kinh nghiệm đã thực hiện), sơ đồ tổ chức, sơ đồ nhân sự, danh sách máy móc thiết bị chưa?",
            "Năng lực tài chính của nhà thầu có bảo đảm cho phần việc được giao không?"],
    "II.1": ["(Gói tư vấn khảo sát / giám sát khảo sát) Nhiệm vụ khảo sát, phương án kỹ thuật khảo sát đã được CĐT phê duyệt chưa?"],
    "II.2": ["Báo cáo kết quả khảo sát đã được chủ đầu tư phê duyệt (chấp thuận) chưa, bằng văn bản nào?"],
    "II.3": ["Thiết kế triển khai đã qua đủ các bước thẩm tra, thẩm định, phê duyệt chưa? Có danh mục bản vẽ và chỉ dẫn kỹ thuật kèm theo không?"],
    "II.4": ["Đã có văn bản chấp thuận nghiệm thu thiết kế chưa?"],
    "III": ["Phần quản lý thi công là trọng tâm: đánh giá kỹ hồ sơ chất lượng, công nghệ thi công và thiết bị của hạng mục."],
    "III.1": ["Thay đổi thiết kế (nếu có) đã có văn bản thẩm định, phê duyệt chưa? Hồ sơ đã đăng tải VPĐT chưa, mã HS là bao nhiêu?"],
    "III.8": ["Đã có hồ sơ lắp đặt thiết bị, biên bản chạy thử đơn động, chạy thử liên động chưa?"],
    "III.9": ["Quy trình vận hành, quy trình bảo trì do bên thiết kế lập hay nhà thầu cung cấp – lắp đặt thiết bị lập? Đã bàn giao cho CĐT chưa?"],
    "III.10b": ["Đã có biên bản nghiệm thu nội bộ hệ thống PCCC trước khi đưa công trình vào sử dụng chưa?"],
    "III.10đ": ["Công trình có thi công đúng Giấy phép xây dựng không: đúng thời hạn giấy phép, đúng quy mô ghi trong giấy phép?"],
    "III.10g": ["(Dự án nhà ở để bán) Đã hoàn thành phần móng / hạ tầng kỹ thuật theo điều kiện được phép bán hàng chưa, có văn bản xác nhận chưa?"],
    "III.12": ["Khi nghiệm thu còn phần việc phải sửa chữa, khắc phục không? Nếu có, đã có biên bản xác nhận tồn tại và tài liệu "
               "chứng minh đã khắc phục chưa?"],
    "III.13": ["Biên bản nghiệm thu hoàn thành đã theo đúng nội dung Điều 24.5 NĐ 207 chưa: có thời điểm tính bảo hành, thời gian bảo hành, "
               "đánh giá sự phù hợp về PCCC chưa?"],
}

# Thành phần tối thiểu của hồ sơ năng lực nhà thầu (mục I.9) – từ khóa không dấu
I9_THANH_PHAN = {
    "Hồ sơ năng lực / kinh nghiệm": r"nang luc|kinh nghiem|dang ky kinh doanh|chung chi nang luc",
    "Sơ đồ tổ chức": r"so do to chuc|to chuc cong truong|ban chi huy|bch",
    "Nhân sự (bổ nhiệm, bằng cấp, chứng chỉ)": r"nhan su|bo nhiem|chi huy truong|can bo|bang cap|chung chi hanh nghe",
    "Máy móc, thiết bị thi công": r"may moc|thiet bi thi cong|may thi cong|danh muc may",
}
# Hồ sơ thiết bị (mục III.8)
III8_THANH_PHAN = {
    "Hồ sơ lắp đặt thiết bị": r"lap dat thiet bi|nghiem thu (lap dat )?thiet bi",
    "Chạy thử đơn động": r"chay thu don dong|don dong",
    "Chạy thử liên động": r"chay thu lien dong|lien dong",
}

VAI_TRO = {"chinh": "Tổng thầu / thầu chính thi công (kiểm tra kỹ pháp lý dự án)",
           "phu": "Thầu phụ / nhà thầu chuyên ngành quy mô nhỏ (pháp lý dự án chỉ đối chiếu nếu có)"}
