import os
import numpy as np
import cv2
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
 
st.set_page_config(page_title="Chandrayaan Crater Hazard Mapper", page_icon="🌙", layout="wide")
 
# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
st.sidebar.title("🚀 Mission Config")
mission_mode = st.sidebar.selectbox(
    "Target Mission Profile",
    ["Chandrayaan-4 (Sample Return Site)", "Chandrayaan-5 (LUPEX Polar Rover)", "Chandrayaan-3 (Archive Validation)"],
)
gsd = st.sidebar.number_input("Ground sampling distance (m / px)", 0.05, 50.0, 0.25, 0.05)
depth_ratio = st.sidebar.slider("Depth / diameter ratio", 0.05, 0.30, 0.20, 0.01)
 
st.sidebar.markdown("---")
WEIGHTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "best.pt")  # trained YOLOv8 weights next to app.py
 
 
@st.cache_resource
def load_yolo_safe(path, mtime=0):
    """Returns (model, error). Never raises, so a bad file can't crash the app."""
    if not os.path.exists(path):
        return None, "not found"
    if os.path.getsize(path) < 1_000_000:
        return None, f"file is only {os.path.getsize(path)} bytes (a real model is several MB)"
    try:
        from ultralytics import YOLO
        m = YOLO(path)
        names = [str(v).lower() for v in m.names.values()]
        # a generic COCO model (80 classes: person, car...) is NOT a crater model
        if len(names) >= 20 or "person" in names:
            return None, "generic pretrained model, not trained on craters"
        return m, None
    except Exception as e:
        return None, str(e).splitlines()[0][:200]
 
 
_yolo_model, _yolo_err = load_yolo_safe(WEIGHTS, os.path.getmtime(WEIGHTS) if os.path.exists(WEIGHTS) else 0)
use_yolo = _yolo_model is not None
engine = st.sidebar.radio(
    "Detection engine",
    ["YOLOv8 (trained weights)", "Classical CV (no training)"] if use_yolo else ["Classical CV (no training)"],
)
 
st.sidebar.markdown("---")
st.sidebar.subheader("Detector tuning")
min_d = st.sidebar.slider("Min crater diameter (px)", 6, 200, 10)
max_d = st.sidebar.slider("Max crater diameter (px)", 20, 800, 160)
sens = st.sidebar.slider("Sensitivity", 1, 10, 6, help="Higher finds more (and fainter) craters")
min_score = st.sidebar.slider("Min rim-confidence", 0.2, 0.95, 0.78, 0.01)
 
 
# ----------------------------------------------------------------------------
# Detectors
# ----------------------------------------------------------------------------
def _ring_stats(gx, gy, mag, thr, x, y, r, n=96):
    a = np.linspace(0, 2*np.pi, n, endpoint=False)
    ca, sa = np.cos(a), np.sin(a)
    h, w = mag.shape
    px, py = x + r*ca, y + r*sa
    ok = (px >= 0) & (px < w-1) & (py >= 0) & (py < h-1)
    if ok.mean() < 0.75:
        return 0.0, 0.0
    xi = np.clip(px.astype(int), 0, w-1); yi = np.clip(py.astype(int), 0, h-1)
    m = mag[yi, xi]
    rad = np.abs(gx[yi, xi]*ca + gy[yi, xi]*sa)
    good = (m > thr) & (rad > 0.6*m) & ok
    # coverage: fraction of 12 angular sectors that contain rim evidence
    sect = good.reshape(12, n//12).any(axis=1)
    return float(good.sum()/n), float(sect.mean())
 
def detect_classical(rgb, min_d, max_d, sens, min_score):
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    H, W = gray.shape
    scale = 1.0
    if max(H, W) > 1400:
        scale = 1400.0/max(H, W)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    g = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
    gs = cv2.GaussianBlur(g, (0, 0), 1.0)
    gxs = cv2.Sobel(gs, cv2.CV_32F, 1, 0, ksize=3)
    gys = cv2.Sobel(gs, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gxs, gys)
    thr = np.percentile(mag, 70)
    gl = cv2.GaussianBlur(g, (0, 0), 2.4)
    gxl = cv2.Sobel(gl, cv2.CV_32F, 1, 0, ksize=3)
    gyl = cv2.Sobel(gl, cv2.CV_32F, 0, 1, ksize=3)
    magl = cv2.magnitude(gxl, gyl)
    thrl = np.percentile(magl, 70)
 
    rmin = max(3.0, min_d*scale/2); rmax = max(rmin+2, max_d*scale/2)
    cands = []
    # source 1: Hough, several radius bands and two smoothing levels
    p2 = int(np.interp(sens, [1, 10], [34, 12]))
    bands = np.unique(np.geomspace(rmin, rmax, 6).astype(int))
    for blur in (1.2, 2.2):
        gb = cv2.GaussianBlur(g, (0, 0), blur)
        for lo, hi in zip(bands[:-1], bands[1:]):
            c = cv2.HoughCircles(gb, cv2.HOUGH_GRADIENT, dp=1.2, minDist=max(3, lo*0.7),
                                 param1=100, param2=p2, minRadius=int(lo), maxRadius=int(hi))
            if c is not None:
                cands += [tuple(map(float, t)) for t in c[0]]
    for lo, hi in ((int(rmax*0.45), int(rmax)),):
        if hi > lo + 3:
            gb = cv2.GaussianBlur(g, (0, 0), 3.0)
            c = cv2.HoughCircles(gb, cv2.HOUGH_GRADIENT, dp=1.5, minDist=max(6, lo*0.8),
                                 param1=80, param2=max(10, p2-6), minRadius=lo, maxRadius=hi)
            if c is not None:
                cands += [tuple(map(float, t)) for t in c[0]]
    # source 2: DoG blobs (finds small dark pits Hough misses)
    gf = g.astype(np.float32)
    for s in np.geomspace(max(1.5, rmin/1.41), max(2.0, rmax/1.41), 10):
        d = cv2.GaussianBlur(gf, (0, 0), s) - cv2.GaussianBlur(gf, (0, 0), s*1.6)
        for sign in (1, -1):
            resp = sign*d
            dil = cv2.dilate(resp, np.ones((5, 5), np.uint8))
            t = np.percentile(resp, 99.0 - 0.15*sens)
            ys, xs = np.where((resp == dil) & (resp > t))
            for x, y in zip(xs, ys):
                cands.append((float(x), float(y), float(s*1.41)))
 
    # score + refine each candidate (small search over radius/centre)
    scored = []
    for x, y, r in cands:
        best = (0, None)
        for dr in (0.85, 1.0, 1.15):
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                cov, sec = _ring_stats(gxs, gys, mag, thr, x+dx, y+dy, r*dr)
                sc = 0.5*cov + 0.5*sec
                if r*dr >= 12:
                    cov2, sec2 = _ring_stats(gxl, gyl, magl, thrl, x+dx, y+dy, r*dr)
                    sc = max(sc, 0.5*cov2 + 0.5*sec2 - 0.08)
                if sc > best[0]:
                    best = (sc, (x+dx, y+dy, r*dr))
        if best[1] is not None and best[0] >= min_score:
            scored.append((best[0],)+best[1])
 
    # NMS (prefer higher score; suppress near-duplicates and nested same-size rings)
    scored.sort(key=lambda t: -t[0])
    kept = []
    for s, x, y, r in scored:
        dup = False
        for _, kx, ky, kr in kept:
            d = np.hypot(x-kx, y-ky); ratio = min(r, kr)/max(r, kr)
            if d < 0.5*max(r, kr) and ratio > 0.6: dup = True; break
            if d < 0.9*max(r, kr) and ratio > 0.85: dup = True; break
            if r < 0.5*kr and 0.5*kr < d < kr + 0.5*r: dup = True; break   # ring sitting on a bigger crater's rim
        if not dup: kept.append((s, x, y, r))
    return [{"cx": x/scale, "cy": y/scale, "r": r/scale, "conf": float(s)} for s, x, y, r in kept]
 
 
def detect_yolo(rgb, conf=0.25):
    """YOLO detection. Large scenes are scanned in overlapping tiles; the 'bg' class is ignored."""
    names = _yolo_model.names
    H, W = rgb.shape[:2]
    boxes, scores = [], []
 
    def run(img, ox, oy):
        res = _yolo_model.predict(img, conf=conf, verbose=False)[0]
        for bx in res.boxes:
            nm = str(names[int(bx.cls[0])]).lower()
            if nm in ("bg", "background"):
                continue
            x1, y1, x2, y2 = bx.xyxy[0].tolist()
            boxes.append([x1 + ox, y1 + oy, x2 - x1, y2 - y1])
            scores.append(float(bx.conf[0]))
 
    def starts(n, tile, step):
        if n <= tile:
            return [0]
        xs = list(range(0, n - tile + 1, step))
        if xs[-1] != n - tile:
            xs.append(n - tile)
        return xs
 
    if max(H, W) <= 800:
        run(rgb, 0, 0)
    else:
        tile, step = 640, 480
        for oy in starts(H, tile, step):
            for ox in starts(W, tile, step):
                run(np.ascontiguousarray(rgb[oy:oy + tile, ox:ox + tile]), ox, oy)
 
    out = []
    if boxes:
        keep = cv2.dnn.NMSBoxes(boxes, scores, 0.0, 0.4)
        for i in np.array(keep).flatten():
            x, y, w, h = boxes[i]
            out.append({"cx": x + w / 2, "cy": y + h / 2, "r": (w + h) / 4, "conf": scores[i]})
    return out
 
 
# ----------------------------------------------------------------------------
# Evaluation (precision / recall / F1 against YOLO-format ground-truth labels)
# ----------------------------------------------------------------------------
def box_iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0
 
 
def evaluate(dets, label_text, W, H, iou_thr=0.5):
    gts = []
    for line in label_text.strip().splitlines():
        p = line.split()
        if len(p) < 5:
            continue
        _, cx, cy, w, h = map(float, p[:5])
        gts.append([(cx - w / 2) * W, (cy - h / 2) * H, (cx + w / 2) * W, (cy + h / 2) * H])
    pred = [[d["cx"] - d["r"], d["cy"] - d["r"], d["cx"] + d["r"], d["cy"] + d["r"]]
            for d in sorted(dets, key=lambda d: -d["conf"])]
    matched, tp = set(), 0
    for p in pred:
        best, bi = 0, -1
        for i, g in enumerate(gts):
            if i in matched:
                continue
            v = box_iou(p, g)
            if v > best:
                best, bi = v, i
        if best >= iou_thr:
            matched.add(bi)
            tp += 1
    fp, fn = len(pred) - tp, len(gts) - tp
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
    return tp, fp, fn, prec, rec, f1
 
 
# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
st.title("🌙 Chandrayaan Autonomous Crater Hazard Mapping")
st.write("Real crater detection on any uploaded lunar image, with measured crater size, "
         "hazard scoring and an accuracy check against ground-truth labels.")
st.markdown("---")
 
up = st.file_uploader("Upload a lunar surface image (JPG/PNG)", type=["jpg", "jpeg", "png"])
 
if up is not None:
    img = Image.open(up).convert("RGB")
    rgb = np.array(img)
    H, W = rgb.shape[:2]
 
    with st.spinner("Detecting craters..."):
        if engine.startswith("YOLO"):
            dets = detect_yolo(rgb)
        else:
            dets = detect_classical(rgb, min_d, max_d, sens, min_score)
 
    dets.sort(key=lambda d: -d["r"])
    diam_m = [2 * d["r"] * gsd for d in dets]
    depth_m = [d * depth_ratio for d in diam_m]
 
    fig = px.imshow(rgb)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), hovermode="closest")
    t = np.linspace(0, 2 * np.pi, 60)
    for i, d in enumerate(dets):
        fig.add_trace(go.Scatter(
            x=d["cx"] + d["r"] * np.cos(t), y=d["cy"] + d["r"] * np.sin(t),
            mode="lines", line=dict(color="#FF4B4B", width=2),
            fill="toself", fillcolor="rgba(255,75,75,0.10)", showlegend=False,
            hoverinfo="text",
            text=f"<b>Crater #{i+1}</b><br>Diameter: {diam_m[i]:.1f} m<br>"
                 f"Est. depth: {depth_m[i]:.1f} m<br>Confidence: {d['conf']:.2f}",
        ))
 
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader(f"🛰️ Detected craters: {len(dets)}")
        st.plotly_chart(fig, use_container_width=True)
 
    with c2:
        st.subheader("📡 Hazard assessment")
        n = len(dets)
        max_depth = max(depth_m) if n else 0.0
        # hazard = fraction of image area covered by craters (physical, not arbitrary)
        covered = min(1.0, sum(np.pi * d["r"] ** 2 for d in dets) / (W * H))
        safety = max(0.0, 100.0 - covered * 250 - min(n, 40) * 0.8 - min(max_depth, 20) * 1.0)
        st.metric("Zonal Safety Index", f"{safety:.1f}%")
        m1, m2, m3 = st.columns(3)
        m1.metric("Craters", n)
        m2.metric("Area covered", f"{covered*100:.1f}%")
        m3.metric("Max diameter", f"{max(diam_m):.1f} m" if n else "-")
 
        if safety >= 75:
            st.success("**TOUCHDOWN APPROVED**: low crater density in this frame.")
        elif safety >= 40:
            st.warning("**CAUTION**: moderate crater density, use hazard avoidance.")
        else:
            st.error("**LANDING ABORT**: crater density / size exceeds safe limits.")
 
        if "Chandrayaan-4" in mission_mode:
            if covered > 0.12 or max_depth > 5:
                st.error("**Ascender liftoff risk:** large depressions near the site.")
            else:
                st.success("**Suitable for sample return** based on crater coverage.")
 
        if n:
            st.dataframe({
                "#": list(range(1, n + 1)),
                "x (px)": [round(d["cx"]) for d in dets],
                "y (px)": [round(d["cy"]) for d in dets],
                "diameter (m)": [round(v, 1) for v in diam_m],
                "depth (m)": [round(v, 1) for v in depth_m],
                "conf": [round(d["conf"], 2) for d in dets],
            }, hide_index=True)
 
    st.markdown("---")
    st.subheader("✅ Measure accuracy")
    st.caption("Upload the YOLO-format .txt label file for this image (from your dataset's valid/test split). "
               "Matching uses IoU ≥ 0.5.")
    lab = st.file_uploader("Ground-truth labels (.txt)", type=["txt"], key="gt")
    if lab is not None:
        tp, fp, fn, p, r, f1 = evaluate(dets, lab.read().decode(), W, H)
        a, b, c, d_ = st.columns(4)
        a.metric("Precision", f"{p*100:.1f}%")
        b.metric("Recall", f"{r*100:.1f}%")
        c.metric("F1", f"{f1*100:.1f}%")
        d_.metric("TP / FP / FN", f"{tp} / {fp} / {fn}")
 