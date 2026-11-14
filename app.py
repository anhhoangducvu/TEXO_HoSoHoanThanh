# -*- coding: utf-8 -*-
"""
TEXO · KIỂM TRA HỒ SƠ CHẤT LƯỢNG DỰ ÁN (NĐ 207/2026 – Phụ lục VII)
Phòng Kỹ thuật – Công ty CP TEXO Tư vấn và Đầu tư

Chạy:  streamlit run app.py
Lớp kiểm tra theo quy tắc chạy hoàn toàn trên máy; AI chỉ bật khi người dùng tự dán API key.
"""
import base64
import json
import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

from core import kb, llm
from core import ocr as ocr_mod
from core.checker import SEV_ICON, SEV_LABEL, ap_dung_ai, kiem_tra
from core.report_vong import build_v1, build_v2
from core.vong import V1_SEV, V2_THIEU, _chot_v1, tin_nhan, vong1, vong1_noi_dung, vong2
from core.mau import tao_mau_xlsx
from core.parser import danh_sach_sheet, doan_loai_nt, doc_danh_sach_vpdt, doc_file, doc_nhieu_file, doc_tu_ai, norm
from core.report_docx import xuat_docx
from core.report_xlsx import xuat_xlsx

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(APP_DIR, "assets", "logo_texo.png")
MARK = os.path.join(APP_DIR, "assets", "logo_mark.png")
SECRETS_FILE = os.path.join(APP_DIR, ".secrets_local.json")
VERSION = "2.1 · 14/11/2026"
APP_NAME = "Kiểm tra Hồ sơ chất lượng dự án"

st.set_page_config(page_title="TEXO · Kiểm tra Hồ sơ chất lượng dự án", page_icon=MARK if os.path.exists(MARK) else "📁",
                   layout="wide")

def logo_html(height=56, align="left"):
    """Logo hiển thị bằng thẻ <img> (giữ nguyên tỷ lệ, không bị cắt như st.image)."""
    try:
        with open(LOGO, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
    except Exception:
        return "<b>TEXO</b>"
    return (f'<div class="texo-logo" style="text-align:{align};padding:6px 0 10px 0;line-height:0">'
            f'<img src="data:image/png;base64,{b64}" alt="TEXO" '
            f'style="height:{height}px;width:auto;max-width:100%;object-fit:contain;display:inline-block"></div>')


@st.cache_data(show_spinner=False)
def _mau_xlsx():
    return tao_mau_xlsx()


st.markdown("""
<style>
:root { --indigo:#0C0150; --cyan:#01A0C7; --navy:#1F3864; }
.block-container { padding-top: 3.6rem; max-width: 1400px; }
header[data-testid="stHeader"] { background: transparent; }
.texo-logo img { image-rendering: auto; }
h1, h2, h3 { color: var(--indigo); }
.texo-band { border-left: 6px solid var(--cyan); background: #F3F6FB; padding: .7rem 1rem; border-radius: 6px; margin: .3rem 0 1rem; }
.kl { padding: .9rem 1.1rem; border-radius: 8px; font-weight: 600; font-size: 1.05rem; margin: .4rem 0 .8rem; }
.kl.high { background:#FDE4E1; color:#8B0000; border-left: 6px solid #C00000; }
.kl.mid  { background:#FFF1DE; color:#7A3608; border-left: 6px solid #C45911; }
.kl.ok   { background:#E4F3E6; color:#1B5E20; border-left: 6px solid #2E7D32; }
.small { font-size: .85rem; color: #595959; }
div[data-testid="stMetricValue"] { color: var(--indigo); }
</style>
""", unsafe_allow_html=True)


# ============================================================================ cổng mật khẩu
def _app_password():
    try:
        if "APP_PASSWORD" in st.secrets:
            return str(st.secrets["APP_PASSWORD"])
    except Exception:
        pass
    return os.environ.get("APP_PASSWORD", "texo2026")


if not st.session_state.get("auth"):
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(logo_html(64), unsafe_allow_html=True)
        st.markdown(f"### {APP_NAME}")
        st.caption("Phòng Kỹ thuật · Công cụ nội bộ")
        pw = st.text_input("Mật khẩu", type="password")
        if st.button("Vào", type="primary", use_container_width=True):
            if pw == _app_password():
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Mật khẩu chưa đúng.")
    st.stop()


# ============================================================================ sidebar: AI
def _load_saved():
    try:
        with open(SECRETS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


saved = _load_saved()
ss = st.session_state
ss.setdefault("models", [])

with st.sidebar:
    st.markdown(logo_html(48), unsafe_allow_html=True)
    st.markdown("**Người kiểm tra**")
    nguoi = st.text_input("Họ tên (ghi vào phiếu)", value=ss.get("nguoi", ""), label_visibility="collapsed",
                          placeholder="Họ và tên người kiểm tra")
    ss.nguoi = nguoi
    st.divider()
    st.markdown("**🧠 Bộ não AI (tùy chọn)**")
    st.caption("Không có key: công cụ vẫn chạy đầy đủ theo bộ quy tắc, miễn phí, dữ liệu không rời máy.")
    prov_keys = list(llm.PROVIDERS.keys())
    p_default = prov_keys.index(saved.get("provider", "anthropic")) if saved.get("provider") in prov_keys else 0
    provider = st.selectbox("Nhà cung cấp", prov_keys, index=p_default, format_func=lambda k: llm.PROVIDERS[k]["label"])
    key = st.text_input("API key", value=saved.get("key", "") if saved.get("provider") == provider else "", type="password")
    base_url = ""
    if llm.PROVIDERS[provider]["needs_base_url"]:
        base_url = st.text_input("Base URL (bắt buộc)", value=saved.get("base_url", ""), placeholder="https://openrouter.ai/api/v1")
    st.caption(llm.PROVIDERS[provider]["note"])
    if st.button("Lấy danh sách model", use_container_width=True, disabled=not key):
        ok, res = llm.list_models(provider, key, base_url)
        if ok and res:
            ss.models, ss.models_for = res, provider
            st.success(f"Có {len(res)} model.")
        else:
            ss.models = []
            st.error(res if not ok else "Không có model nào dùng được với key này.")
    model = ""
    if ss.models and ss.get("models_for") == provider:
        pref = [i for i, m in enumerate(ss.models) if any(x in m for x in ("sonnet", "gpt-4o", "flash-latest", "flash"))]
        idx = ss.models.index(saved["model"]) if saved.get("model") in ss.models else (pref[0] if pref else 0)
        model = st.selectbox("Model", ss.models, index=idx)
    elif saved.get("model") and saved.get("provider") == provider:
        model = saved["model"]
        st.caption(f"Model đã lưu: `{model}` (bấm 'Lấy danh sách model' để đổi)")
    if st.button("Kiểm tra kết nối", use_container_width=True, disabled=not (key and model)):
        with st.spinner("Đang gọi thử…"):
            ok, msg = llm.test_connection(provider, model, key, base_url)
        (st.success if ok else st.error)(("Kết nối được: " if ok else "") + msg)
    luu = st.checkbox("Lưu key tại máy này", value=bool(saved.get("key")))
    if luu:
        st.warning("Chỉ lưu trên máy cá nhân. Không dùng chung máy/tài khoản đã lưu key, không deploy công khai kèm file key. "
                   "Lộ key do cách sử dụng không phải lỗi phần mềm.", icon="⚠️")
        if key and st.button("Lưu cấu hình AI", use_container_width=True):
            with open(SECRETS_FILE, "w", encoding="utf-8") as f:
                json.dump({"provider": provider, "key": key, "base_url": base_url, "model": model}, f)
            st.success("Đã lưu.")
    if saved.get("key") and st.button("Xoá key đã lưu", use_container_width=True):
        try:
            os.remove(SECRETS_FILE)
        except Exception:
            pass
        st.rerun()
    ai_ready = bool(key and model and (not llm.PROVIDERS[provider]["needs_base_url"] or base_url))
    if ai_ready:
        st.success(f"AI sẵn sàng · {model}")
        st.caption("Khi bấm dùng AI, nội dung danh mục được gửi tới nhà cung cấp đã chọn.")
    elif key and not model:
        st.info("Đã có key – bấm 'Lấy danh sách model' và chọn model.")
    else:
        st.info("Đang chạy bản KHÔNG AI.")
    st.divider()
    st.caption(f"Phiên bản {VERSION} · Kiểm tra 3 vòng\nCăn cứ: NĐ 207/2026/NĐ-CP · Phụ lục VII")
    st.caption("Văn bản pháp lý dẫn trong hồ sơ: kiểm tra bản mới nhất bằng công cụ TEXO Legal Reviewer.")
    st.caption("Người xây dựng: Hoàng Đức Vũ – Trưởng phòng Kỹ thuật")




# ============================================================================ main
h1, h2 = st.columns([0.75, 0.25])
with h1:
    st.markdown(f"## {APP_NAME}")
    st.markdown('<div class="texo-band">Kiểm tra theo <b>3 vòng</b>: <b>① Đầu vào</b> – file đọc được chưa (scan, ảnh chụp, '
                'file cũ, quá nặng) và nhà thầu là ai · <b>② Sơ bộ</b> – có đủ hồ sơ cơ bản chưa (hợp đồng, nhân sự, biên bản '
                'nghiệm thu, danh mục NT vật liệu, NT công việc, hoàn công; thầu phụ thêm chấp thuận thầu phụ và HĐ thầu chính) · '
                '<b>③ Chi tiết</b> – đối chiếu <b>Phụ lục VII NĐ 207/2026</b> trong phạm vi đúng với quy mô nhà thầu: '
                'chỉ tổng thầu, thầu chính, phần ngầm, kết cấu phần thân mới phải rà đủ Phụ lục.</div>', unsafe_allow_html=True)

ocr_ok, ocr_msg = ocr_mod.san_sang()
c1, c2 = st.columns([0.55, 0.45])
with c1:
    st.markdown("#### Tài liệu cần kiểm tra")
    fs = st.file_uploader("Danh mục hồ sơ – một quyển, hoặc nhiều file rời (theo loại, theo đợt)",
                          type=["docx", "pdf", "xlsx", "xlsm", "doc", "xls"], key="f_dm", accept_multiple_files=True,
                          help="Không bắt buộc theo mẫu nào: công cụ đọc theo nội dung từng dòng. Nộp bản Word/Excel gốc hoặc PDF xuất "
                               "trực tiếp (có chữ); bản scan có chữ ký chỉ để lưu.")
    fs = fs or []
    dung_ocr = False
    if ocr_ok:
        dung_ocr = st.checkbox("Thử đọc PDF scan bằng OCR (chậm hơn, độ chính xác thấp – phải đối chiếu lại)",
                               value=False, help=ocr_msg)
    else:
        st.caption("PDF scan: máy chủ chưa có OCR – đề nghị đoàn gửi bản Word/Excel gốc của danh mục.")
    m1, m2 = st.columns([0.55, 0.45])
    with m1:
        st.download_button("📥 Tải mẫu danh mục tham khảo (Excel)", data=_mau_xlsx(), use_container_width=True,
                           file_name="Mau danh muc ho so chat luong - tham khao.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with m2:
        st.caption("Mẫu chỉ để tham khảo, không bắt buộc. Nhà thầu nhỏ chỉ cần các thành phần cơ bản.")
    with st.expander("Đối chiếu thêm (tùy chọn)"):
        f_bc = st.file_uploader("Báo cáo đăng tải hồ sơ VPĐT của đoàn (.docx/.pdf/.xlsx)", type=["docx", "pdf", "xlsx"], key="f_bc")
        f_vp = st.file_uploader("Danh sách hồ sơ xuất từ VPĐT (để kiểm tra mã có tồn tại)", type=["xlsx", "docx", "pdf"], key="f_vp")
        st.caption("Báo cáo đăng tải nạp lẫn trong ô tài liệu cũng được – công cụ tự nhận ra và đưa sang phần đối chiếu.")

# ------------------------------------------------------------------ vòng 1 (tự chạy khi nạp file)
sig = tuple((f.name, f.size) for f in fs) + (("ocr", dung_ocr),)
if fs and ss.get("v1_sig") != sig:
    with st.spinner("Vòng 1 – kiểm tra đầu vào…"):
        ss.v1 = vong1([(f.name, f.getvalue()) for f in fs], ocr=dung_ocr)
    ss.v1_sig = sig
    for x in ("doc", "doc_sig", "bc_auto", "v2", "v2_args", "R", "R_args", "ai"):
        ss.pop(x, None)
if not fs:
    for x in ("v1", "v1_sig", "doc", "doc_sig", "bc_auto", "v2", "v2_args", "R", "R_args", "ai"):
        ss.pop(x, None)
v1 = ss.get("v1")
doc_ok = [f for f, t in zip(fs, v1.tep) if t["doc_duoc"]] if v1 else []

with c1:
    sheet_sel, nhieu_sheet = {}, []
    for f in doc_ok:
        if f.name.lower().endswith(("xlsx", "xlsm")):
            try:
                all_sh = [x for x in danh_sach_sheet(f.getvalue()) if x not in ("_ds",)]
            except Exception as e:
                st.error(f"Không đọc được danh sách sheet của {f.name}: {e}")
                continue
            if len(all_sh) <= 1:
                sheet_sel[f.name] = [None]
            else:
                nhieu_sheet.append((f, all_sh))
    if nhieu_sheet:
        with st.expander(f"Chọn sheet của {len(nhieu_sheet)} file Excel nhiều sheet", expanded=len(fs) == 1):
            for f, all_sh in nhieu_sheet:
                la_mau = sum(1 for x in all_sh if x[:2].strip(". ").isdigit()) >= 3
                mac_dinh = [x for x in all_sh if norm(x) not in ("huong dan",)] if la_mau else all_sh[:1]
                sheet_sel[f.name] = st.multiselect(f"Sheet cần đọc – {f.name}", all_sh, default=mac_dinh, key=f"sh_{f.name}",
                                                   help="File có nhiều sheet trùng nội dung (tổng hợp + từng nhà thầu): chỉ chọn sheet "
                                                        "cần kiểm tra. Mỗi sheet được đọc như một danh mục riêng.")

doc, bc_auto = None, None
if v1 and doc_ok:
    parts = []
    for f in doc_ok:
        if f.name in sheet_sel:
            for sh in sheet_sel[f.name]:
                parts.append((f"{f.name} › {sh}" if sh else f.name, f.name, f.getvalue(), sh))
        else:
            parts.append((f.name, f.name, f.getvalue(), None))
    dsig = tuple((p[0], len(p[2])) for p in parts) + (("ocr", dung_ocr),)
    if ss.get("doc_sig") != dsig:
        with st.spinner("Đang đọc danh mục…"):
            if len(parts) == 1:
                d0 = doc_file(parts[0][1], parts[0][2], sheets=[parts[0][3]] if parts[0][3] else None, ocr=dung_ocr)
                ss.doc, ss.bc_auto = d0, None
            else:
                ss.doc, ss.bc_auto, _tep = doc_nhieu_file(parts, ocr=dung_ocr)
            v1.muc = [m for m in v1.muc if m.get("tep") or m.get("tong_hop")]  # bỏ kết quả nội dung lần đọc trước
            _chot_v1(v1)
            vong1_noi_dung(v1, ss.doc, " ".join(f.name for f in doc_ok))
        ss.doc_sig = dsig
        for x in ("v2", "v2_args", "R", "R_args", "ai"):
            ss.pop(x, None)
    doc, bc_auto = ss.doc, ss.get("bc_auto")
elif v1 and not doc_ok:
    vong1_noi_dung(v1, None)

nd = (v1.nhan_dien if v1 else {}) or {}
meta0 = (doc or {}).get("meta", {})
info_phieu = dict(du_an=meta0.get("du_an", ""), nha_thau=meta0.get("nha_thau", "") or nd.get("nha_thau", ""),
                  ho_so=fs[0].name if len(fs) == 1 else f"{len(fs)} file danh mục", nguoi=ss.get("nguoi", ""))

# ------------------------------------------------------------------ phạm vi (xác nhận nhận diện)
with c2:
    st.markdown("#### Phạm vi kiểm tra")
    if not v1:
        st.info("Nạp danh mục ở bên trái – vòng 1 chạy ngay khi nạp file.")
    goi_y = nd.get("loai_goi_y")
    opts = list(kb.LOAI_NT.keys())
    loai = st.radio("Loại nghiệm thu", opts, index=opts.index(goi_y) if goi_y in opts else 0,
                    format_func=lambda k: kb.LOAI_NT[k] + ("  ← nhận diện từ tiêu đề" if k == goi_y else ""), disabled=not doc)
    vt_opts = ["chinh", "phu"]
    vai_tro = st.radio("Nhà thầu là", vt_opts, index=vt_opts.index(nd.get("vai_tro", "chinh")), horizontal=True,
                       format_func=lambda k: {"chinh": "Tổng thầu / thầu chính", "phu": "Thầu phụ"}[k], disabled=not doc,
                       help="Thầu phụ: hỏi thêm văn bản chấp thuận nhà thầu phụ và hợp đồng của tổng thầu / thầu chính với chủ đầu tư.")
    qm_opts = list(kb.QUY_MO.keys())
    quy_mo = st.radio("Quy mô nhà thầu – quyết định độ dài danh mục phải kiểm tra", qm_opts,
                      index=qm_opts.index(nd.get("quy_mo", "lon")), format_func=lambda k: kb.QUY_MO[k], disabled=not doc)
    if nd:
        st.caption(f"Gợi ý tự động: {'thầu phụ' if nd['vai_tro'] == 'phu' else 'thầu chính'} ({nd['ly_do_vai_tro']}) · "
                   f"{kb.QUY_MO_NGAN[nd['quy_mo']].lower()} ({nd['ly_do_quy_mo']}). Kiểm tra lại trước khi rà soát.")

# ------------------------------------------------------------------ hiển thị 3 vòng
st.markdown("---")
v2 = ss.get("v2")
R = ss.get("R")
ICON_V = {"high": "🔴", "mid": "🟠", "ok": "🟢"}


def _chip(lbl, kl, sev):
    return f"{ICON_V.get(sev, '⚪')} **{lbl}** – {kl}" if kl else f"⚪ **{lbl}** – chưa chạy"


s1, s2, s3 = st.columns(3)
s1.markdown(_chip("Vòng 1 · Đầu vào", v1.ket_luan if v1 else "", V1_SEV.get(v1.ket_luan) if v1 else None))
s2.markdown(_chip("Vòng 2 · Sơ bộ", v2.ket_luan if v2 else "", v2.sev if v2 else None))
s3.markdown(_chip("Vòng 3 · Chi tiết", R["ket_luan"].split(" – ")[0] if R else "", R["ket_luan_sev"] if R else None))

if not v1:
    st.markdown("##### Ba vòng kiểm tra")
    a, b, c = st.columns(3)
    a.markdown("**① Kiểm tra đầu vào**  \nFile Word/Excel/PDF có chữ đọc được chưa; PDF scan, ảnh chụp dán vào Word, file .doc/.xls "
               "đời cũ, file quá nặng, đặt mật khẩu được chỉ ra ngay kèm cách gửi lại. Bộ nhiều file: file lỗi bị loại, file đạt vẫn đi tiếp.")
    b.markdown("**② Rà soát sơ bộ**  \nChỉ tìm thành phần cơ bản: hợp đồng, danh sách nhân sự, biên bản nghiệm thu, danh mục NT vật liệu, "
               "NT công việc, bản vẽ hoàn công. Thầu phụ thêm chấp thuận thầu phụ, HĐ thầu chính – CĐT. Nhà thầu lớn thêm GPXD, thiết kế duyệt.")
    c.markdown("**③ Kiểm tra chi tiết**  \nĐối chiếu Phụ lục VII theo đúng quy mô: tổng thầu / thầu chính / phần ngầm / phần thân rà đủ; "
               "nhà thầu hạng mục và nhà thầu nhỏ chỉ các mục của phần việc mình làm – không bắt lập lại danh mục đủ Phụ lục.")
    st.stop()


def _tin_nhan_box(txt, key):
    st.text_area("Tin nhắn gửi đoàn (chọn hết, sao chép, dán Zalo)", value=txt, key=key,
                 height=min(420, 60 + 22 * txt.count("\n")))


# ---- VÒNG 1
with st.expander(f"① Vòng 1 – Kiểm tra đầu vào: {v1.ket_luan} · {len(v1.tep_doc_duoc)}/{len(v1.tep)} file đọc được",
                 expanded=v1.tra_lai or (v2 is None and bool(v1.muc))):
    st.dataframe(pd.DataFrame([{"File": t["ten"], "Định dạng": t["dinh_dang"], "Dung lượng (MB)": t["mb"],
                                "Trang": str(t.get("so_trang") or ""), "Trang scan": str(t.get("trang_scan") or ""),
                                "Sheet": str(t.get("so_sheet") or ""), "Kết luận": t["ket_luan"]} for t in v1.tep]),
                 hide_index=True, use_container_width=True)
    for m in v1.muc:
        (st.error if m["muc"] == "Trả lại" else st.warning)(
            f"{(m['tep'] + ': ') if m.get('tep') else ''}{m['noi_dung']}  \n➜ {m['xu_ly']}")
    if not v1.muc:
        st.success("Các file đều đọc được.")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button("⬇️ Phiếu vòng 1 (Word)", data=build_v1(v1, info_phieu), use_container_width=True,
                           file_name=f"Phieu vong 1 - kiem tra dau vao - {datetime.now():%Y%m%d}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with d2:
        if v1.tra_lai or v1.muc:
            _tin_nhan_box(tin_nhan(v1, None, info_phieu), "tn1")
if v1.tra_lai:
    st.error("Vòng 1: TRẢ LẠI – chưa đọc được danh mục nào. Gửi phiếu / tin nhắn ở trên cho đoàn để nộp lại bản đọc được.")
    st.stop()
if doc is not None:
    for w in doc["warnings"]:
        st.caption("⚠ " + w)
    if not doc["rows"] and ai_ready and doc.get("text"):
        if st.button("Nhờ AI trích danh mục từ văn bản"):
            with st.spinner("AI đang trích xuất…"):
                res = llm.ai_trich_xuat(provider, model, key, doc["text"], base_url)
            if res["ok"]:
                ss.doc = doc_tu_ai(res["data"])
                st.rerun()
            else:
                st.error(res["error"])

# ---- VÒNG 2
v2_args = dict(loai=loai, vai_tro=vai_tro, quy_mo=quy_mo)
if v2 is not None and ss.get("v2_args") != v2_args:
    for x in ("v2", "v2_args", "R", "R_args", "ai"):
        ss.pop(x, None)
    v2, R = None, None
if st.button("② Rà soát sơ bộ – thành phần cơ bản", type="primary" if v2 is None else "secondary",
             use_container_width=True, disabled=not (doc and doc["rows"])):
    ss.v2 = vong2(doc, loai, vai_tro, quy_mo)
    ss.v2_args = v2_args
    for x in ("R", "R_args", "ai"):
        ss.pop(x, None)
    st.rerun()
if v2 is not None:
    with st.expander(f"② Vòng 2 – Rà soát sơ bộ: {v2.ket_luan}", expanded=R is None):
        st.markdown(f'<div class="kl {v2.sev}">{ICON_V.get(v2.sev, "")} {v2.ket_luan}. {v2.nhan_xet}</div>', unsafe_allow_html=True)
        tt_lab = {"co": "🟢 Có", "thieu_dm": "🟠 Chưa có danh mục chi tiết"}
        st.dataframe(pd.DataFrame([{"Thành phần": c["ten"], "Bắt buộc": "✔" if c["chan"] else "",
                                    "Hiện trạng": tt_lab.get(c["trang_thai"], "🔴 Chưa thấy" if c["chan"] else "🟠 Chưa thấy"),
                                    "Số dòng": c["so_dong"], "Ví dụ dòng tìm thấy": "; ".join(c["mau"][:2])}
                                   for c in v2.thanh_phan]), hide_index=True, use_container_width=True)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("⬇️ Phiếu vòng 2 (Word)", data=build_v2(v2, v1, info_phieu), use_container_width=True,
                               file_name=f"Phieu vong 2 - ra soat so bo - {datetime.now():%Y%m%d}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.caption(f"Vòng 3 sẽ xét {len(v2.pham_vi_v3['B'])} mục bắt buộc, {len(v2.pham_vi_v3['D'])} mục đối chiếu "
                       f"({kb.QUY_MO_NGAN[quy_mo].lower()}).")
        with d2:
            _tin_nhan_box(tin_nhan(v1, v2, info_phieu), "tn2")

# ---- VÒNG 3
co_ngay = False
ngay_nt = None
chay = False
if v2 is not None:
    e1, e2 = st.columns([0.5, 0.5])
    with e1:
        co_ngay = st.checkbox("Nhập ngày nghiệm thu (để chọn nghị định và soát ngày tài liệu)")
        ngay_nt = st.date_input("Ngày nghiệm thu", value=date.today(), format="DD/MM/YYYY") if co_ngay else None
    with e2:
        cho_phep = True
        if v2.ket_luan == V2_THIEU:
            cho_phep = st.checkbox("Vẫn kiểm tra chi tiết dù còn thiếu hồ sơ cơ bản", value=False)
        chay = st.button("③ Kiểm tra chi tiết – Phụ lục VII", type="primary" if R is None else "secondary",
                         use_container_width=True, disabled=not cho_phep)
if chay:
    bc = doc_file(f_bc.name, f_bc.getvalue()) if f_bc is not None else bc_auto
    vp = doc_danh_sach_vpdt(f_vp.name, f_vp.getvalue()) if f_vp is not None else None
    with st.spinner("Vòng 3 – đối chiếu Phụ lục VII…"):
        ss.R = kiem_tra(doc, loai, ngay_nt=ngay_nt, bc_dang_tai=bc, ds_vpdt=vp, vai_tro=vai_tro, quy_mo=quy_mo)
    ss.R["vong"] = {"v1": v1.ket_luan, "v2": v2.ket_luan}
    ss.R_args = dict(loai=loai, ngay_nt=ngay_nt, bc=bc, vp=vp, vai_tro=vai_tro, quy_mo=quy_mo)
    ss.pop("ai", None)
    st.rerun()

R = ss.get("R")
if not R:
    st.stop()

# ============================================================================ kết quả
k = R["kpi"]
st.markdown(f"#### ③ Vòng 3 – Kiểm tra chi tiết · {kb.QUY_MO_NGAN[R['quy_mo']]}"
            f"{' · thầu phụ' if R.get('vai_tro') == 'phu' else ''} · {R['loai_nt_label']}")
st.markdown(f'<div class="kl {R["ket_luan_sev"]}">{SEV_ICON.get(R["ket_luan_sev"], "")} {R["ket_luan"]}</div>', unsafe_allow_html=True)
m = st.columns(6)
m[0].metric("Mục bắt buộc có", f"{k['muc_B_co']}/{k['muc_B']}", f"{k['ty_le_B']}%", delta_color="off")
m[1].metric("Dòng hồ sơ chi tiết", k["dong_chi_tiet"])
m[2].metric("Dòng có mã VPĐT", f"{k['ty_le_co_ma']}%")
m[3].metric("Số mã HS", k["so_ma"], f"{k['so_ma_gom']} mã gom nhiều mục" if k["so_ma_gom"] else None, delta_color="inverse")
m[4].metric("🔴 Phải xử lý", k["high"])
m[5].metric("🟠 Nên xử lý", k["mid"])
meta = R["meta"]
st.markdown(f'<div class="small"><b>{meta.get("tieu_de", "")}</b> · Dự án: {meta.get("du_an", "–")} · '
            f'Hạng mục/gói thầu: {meta.get("hang_muc") or meta.get("goi_thau") or "–"} · Nhà thầu: {meta.get("nha_thau", "–")} · '
            f'Căn cứ: {R["nghi_dinh"]}' + (f' · Hồ sơ từ {k["tu_ngay"]} đến {k["den_ngay"]}' if k["tu_ngay"] else "") + "</div>",
            unsafe_allow_html=True)

TAB_NAMES = ["📚 Bức tranh bộ hồ sơ", "✅ Đối chiếu PL VII", "🚩 Phát hiện", "🗂 Mã VPĐT", "📄 Danh mục đã đọc", "🧠 AI rà soát", "⬇️ Tải phiếu"]
co_tep = bool(R.get("tep"))
tabs = st.tabs((["🧩 Các danh mục đã nạp"] if co_tep else []) + TAB_NAMES)
if co_tep:
    with tabs[0]:
        st.caption("Mỗi file (hoặc mỗi sheet) được đọc như một danh mục riêng rồi gộp thành một bộ. Loại danh mục và đợt được nhận diện "
                   "từ tên file / tiêu đề; từng dòng vẫn được xếp mục PL VII theo nội dung.")
        dft = pd.DataFrame([{"Danh mục": t["ten"], "Loại nhận diện": t["loai_label"], "Đợt": t["dot"] or "",
                             "Số dòng": t["so_dong"], "Mục PL VII (số dòng)": ", ".join(f"{c} ({n})" for c, n in (t.get("muc_dem") or {}).items()),
                             "Số mã HS": t.get("so_ma", ""), "Ghi chú": "Đưa sang đối chiếu mã" if t["loai"] == "bao_cao_dang_tai" else
                             ("; ".join(t["canh_bao"]) if t["canh_bao"] else "")} for t in R["tep"]])
        st.dataframe(dft, hide_index=True, use_container_width=True)
        loais = {}
        for t in R["tep"]:
            if t["dot"] and t["loai"] not in ("bao_cao_dang_tai", "tong", "phap_ly", "khac"):
                loais.setdefault(t["loai_label"], set()).add(t["dot"])
        if loais:
            mx = max(max(v) for v in loais.values())
            st.markdown("**Ma trận đợt** – ô trống là đợt chưa có danh mục")
            st.dataframe(pd.DataFrame([{"Loại": k, **{f"Đợt {d}": ("✅" if d in v else "—") for d in range(1, mx + 1)}}
                                       for k, v in loais.items()]), hide_index=True, use_container_width=True)
    tabs = tabs[1:]

with tabs[0]:
    st.caption("Bộ hồ sơ sắp theo trình tự Phụ lục VII – để nắm toàn bộ thành phần, số hiệu và nơi lưu trên VPĐT mà không phải tải từng file.")
    by_code = {}
    for r in R["rows"]:
        if r.get("muc"):
            by_code.setdefault(r["muc"], []).append(r)
    for g in ("I", "II", "III", "T"):
        its = [it for it in R["items"] if it["nhom"] == g and (it["yeu_cau"] != "-" or it["so_dong"])]
        if not its:
            continue
        n_ok = len([i for i in its if i["so_dong"]])
        with st.expander(f"{g}. {kb.NHOM[g]} — {n_ok}/{len(its)} mục có hồ sơ", expanded=(g == "III")):
            for q in kb.CAU_HOI_KT.get(g, []):
                st.info(q, icon="🎯")
            for it in its:
                rs = by_code.get(it["code"], [])
                st.markdown(f"{SEV_ICON[it['trang_thai']]} **{it['code']} · {it['ten']}** "
                            f"<span class='small'>· {it['hinh_thuc_label']} · yêu cầu {it['yeu_cau']} · {it['ket_luan']}</span>",
                            unsafe_allow_html=True)
                if rs:
                    df = pd.DataFrame([{"ID": r["id"], "Nội dung": r["noi_dung"], "Số VB": r["so_vb"], "Ngày": r["ngay_raw"],
                                        "Mã VPĐT": ", ".join(r["ma"]) or (f"({', '.join(r['ma_ke_thua'])})" if r["ma_ke_thua"] else "")}
                                       for r in rs])
                    st.dataframe(df, hide_index=True, use_container_width=True, height=min(38 + 35 * len(df), 300))
                if it.get("cau_hoi_kt"):
                    st.markdown("<div class='small'>❓ " + "<br>❓ ".join(it["cau_hoi_kt"]) + "</div>", unsafe_allow_html=True)

with tabs[1]:
    df = pd.DataFrame([{"Mục": it["code"], "Thành phần hồ sơ": it["ten"], "YC": it["yeu_cau"], "Hình thức": it["hinh_thuc_label"],
                        "Chủ thể lưu": it.get("chu_the", ""), "Số dòng": it["so_dong"], "Có số/ngày": it["so_co_so_hieu"],
                        "Mã VPĐT": ", ".join(it["ma"]), "Đánh giá": f"{SEV_ICON[it['trang_thai']]} {SEV_LABEL[it['trang_thai']]}",
                        "Kết luận": it["ket_luan"]} for it in R["items"]])
    an = st.checkbox("Ẩn mục không xét", value=True)
    if an:
        df = df[df["YC"] != "-"]
    st.dataframe(df, hide_index=True, use_container_width=True, height=620)
    st.caption("YC: B – phải có hoặc phải nêu căn cứ · Đ – đối chiếu nếu có. Ma trận áp dụng theo loại nghiệm thu là cách áp dụng nội bộ của P.KT.")

with tabs[2]:
    lv = st.multiselect("Mức độ", ["high", "mid", "info"], default=["high", "mid", "info"], format_func=lambda s: f"{SEV_ICON[s]} {SEV_LABEL[s]}")
    for f in R["findings"]:
        if f["muc_do"] not in lv:
            continue
        with st.container(border=True):
            st.markdown(f"{SEV_ICON[f['muc_do']]} **{f['tieu_de']}**  <span class='small'>({f['ma_loi']})</span>", unsafe_allow_html=True)
            if f["chi_tiet"]:
                st.markdown(f"<div class='small'>{f['chi_tiet']}</div>", unsafe_allow_html=True)
            if f.get("de_xuat"):
                st.markdown(f"➜ {f['de_xuat']}")

with tabs[3]:
    if R["ma_map"]:
        df = pd.DataFrame([{"Mã HS": ma, "Dòng trực tiếp": len(e["dong"]), "Dòng kế thừa": len(e["dong_ke_thua"]),
                            "Mục PL VII": ", ".join(sorted(c for c in e["muc"] if c)),
                            "Đánh giá": "🟠 Gom nhiều mục" if e.get("gom") else "🟢 Rõ",
                            "Nội dung": "; ".join(dict.fromkeys(e["noi_dung"]))[:250]} for ma, e in R["ma_map"].items()])
        st.dataframe(df, hide_index=True, use_container_width=True, height=480)
    else:
        st.info("Danh mục chưa có mã hồ sơ VPĐT.")
    dc = R.get("doi_chieu", {})
    if dc.get("bao_cao"):
        st.markdown("**Đối chiếu với báo cáo đăng tải**")
        b1, b2 = st.columns(2)
        b1.markdown("Có trong báo cáo, thiếu trong danh mục")
        b1.dataframe(pd.DataFrame(dc["bao_cao"]["chi_bc"], columns=["Mã", "Nội dung", "Mục PL VII"]), hide_index=True, use_container_width=True)
        b2.markdown("Có trong danh mục, không có trong báo cáo")
        b2.dataframe(pd.DataFrame({"Mã": dc["bao_cao"]["chi_dm"]}), hide_index=True, use_container_width=True)
    if dc.get("vpdt"):
        st.markdown(f"**Đối chiếu danh sách VPĐT** ({dc['vpdt']['tong']} mã trong file xuất): "
                    f"{len(dc['vpdt']['khong_ton_tai'])} mã không tìm thấy.")
        if dc["vpdt"]["khong_ton_tai"]:
            st.write(", ".join(dc["vpdt"]["khong_ton_tai"]))

with tabs[4]:
    src = {"tu_khoa": "Từ khóa", "ke_thua": "Kế thừa nhóm", "ai": "AI", "tep": "Theo loại danh mục", "mau": "Ghi trong mẫu"}
    df = pd.DataFrame([{"ID": r["id"], "Cấp": r["cap"], "STT": r["stt"], "Nội dung": ("· " * max(0, r["cap"] - 1)) + r["noi_dung"],
                        "Số VB": r["so_vb"], "Ngày": r["ngay_raw"], "Đơn vị": r["don_vi"], "Mã VPĐT": ", ".join(r["ma"]),
                        "Mã nhóm": ", ".join(r["ma_ke_thua"]), "Mục PL VII": r.get("muc") or "",
                        "Nguồn": src.get(r.get("muc_nguon"), ""), "Danh mục (file)": r.get("nguon", "")} for r in R["rows"]])
    st.dataframe(df, hide_index=True, use_container_width=True, height=620)

with tabs[5]:
    if not ai_ready:
        st.info("Dán API key và chọn model ở thanh bên trái để dùng AI. Không có AI, kết quả theo quy tắc ở các tab khác vẫn đầy đủ.")
    else:
        st.markdown("AI đọc **kết quả của bộ quy tắc** (không thay thế) để: phân loại các dòng chưa xếp được, nhận xét tổng quan, "
                    "chỉ thêm rủi ro và đề xuất câu hỏi cho đoàn.")
        st.caption("Nội dung danh mục sẽ được gửi tới nhà cung cấp AI đã chọn.")
        if st.button("🧠 Nhờ AI rà soát bổ sung", type="primary"):
            with st.spinner("AI đang đọc danh mục (20–60 giây)…"):
                res = llm.ai_ra_soat(provider, model, key, R, base_url)
            ss.ai = res
            if res.get("ok"):
                n = ap_dung_ai(ss.doc["rows"], res["data"].get("phan_loai_bo_sung"))
                a = ss.R_args
                ss.R = kiem_tra(ss.doc, a["loai"], ngay_nt=a["ngay_nt"], bc_dang_tai=a["bc"], ds_vpdt=a["vp"], vai_tro=a["vai_tro"],
                                quy_mo=a["quy_mo"])
                ss.R["vong"] = {"v1": ss.v1.ket_luan, "v2": ss.v2.ket_luan}
                ss.ai_n = n
                st.rerun()
        res = ss.get("ai")
        if res:
            if not res.get("ok"):
                st.error(res.get("error"))
                if res.get("raw"):
                    with st.expander("Phản hồi thô"):
                        st.code(res["raw"])
            else:
                d = res["data"]
                if res.get("truncated"):
                    st.warning("Phản hồi có thể bị cắt cụt – đã tự vá JSON, nên kiểm tra lại.")
                st.success(f"AI đã phân loại bổ sung {ss.get('ai_n', 0)} dòng (đã cập nhật vào các tab).")
                st.markdown("**Nhận xét tổng quan**")
                st.write(d.get("nhan_xet_tong_quan", ""))
                for x in d.get("rui_ro_bo_sung") or []:
                    s = x.get("muc_do") if x.get("muc_do") in SEV_ICON else "info"
                    st.markdown(f"{SEV_ICON[s]} {x.get('noi_dung', '')}  \n➜ {x.get('de_xuat', '')}")
                if d.get("cau_hoi_cho_doan"):
                    st.markdown("**Câu hỏi cho đoàn**")
                    for i, q in enumerate(d["cau_hoi_cho_doan"], 1):
                        st.markdown(f"{i}. {q}")

with tabs[6]:
    ten_nguon = fs[0].name if len(fs) == 1 else f"Bộ hồ sơ {len(R.get('tep') or fs)} danh mục"
    base = os.path.splitext(fs[0].name)[0][:60] if len(fs) == 1 else f"Bo ho so {len(R.get('tep') or fs)} danh muc"
    stamp = datetime.now().strftime("%Y%m%d")
    ai_res = ss.get("ai") if ss.get("ai", {}).get("ok") else None
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Phiếu kiểm tra (Word A4)**  \nKết luận, đối chiếu PL VII, phát hiện, bản đồ mã VPĐT, câu hỏi cho đoàn, phụ lục danh mục.")
        st.download_button("⬇️ Tải phiếu Word", data=xuat_docx(R, ss.get("nguoi", ""), ten_nguon, ai_res),
                           file_name=f"Phieu kiem tra HS chat luong - {base} - {stamp}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with d2:
        st.markdown("**Bảng tính (Excel)**  \nTổng quan, đối chiếu PL VII, danh mục đã đọc có lọc, bản đồ mã VPĐT – để anh em lọc và cập nhật.")
        st.download_button("⬇️ Tải Excel", data=xuat_xlsx(R, ten_nguon, ai_res),
                           file_name=f"Doi chieu PL VII - {base} - {stamp}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
