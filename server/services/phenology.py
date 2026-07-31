"""物候匹配服务 — 从 main_tianyan.py 提取的可复用逻辑"""
from __future__ import annotations

import numpy as np
from typing import List, Dict, Any, Optional

try:
    from scipy.signal import savgol_filter, find_peaks
except ImportError:
    savgol_filter = None
    find_peaks = None

try:
    from scipy.interpolate import interp1d
except ImportError:
    interp1d = None

try:
    from scipy.interpolate import PchipInterpolator
except ImportError:
    PchipInterpolator = None


def _clean_curve(arr: np.ndarray) -> np.ndarray:
    arr = np.array(arr, dtype=float)
    valid = ~np.isnan(arr)
    if valid.sum() < 3:
        return arr
    x = np.arange(arr.size)
    arr[~valid] = np.interp(x[~valid], x[valid], arr[valid])
    return arr


def _extract_landmarks(curve: np.ndarray, threshold: float = 0.0001) -> Dict[str, int]:
    arr = _clean_curve(curve)
    smoothed = savgol_filter(arr, window_length=31, polyorder=3) if savgol_filter is not None else arr
    d1 = np.gradient(smoothed)
    d2 = np.gradient(d1)
    d3 = np.gradient(d2)

    if find_peaks is not None:
        up, _ = find_peaks(d3[:180], height=threshold, distance=20)
        down, _ = find_peaks(-d3[180:], height=threshold, distance=20)
        down = down + 180
    else:
        up, down = np.array([]), np.array([])

    if len(up) > 0 and len(down) > 0:
        marks = {"Greenup": int(up[0]), "Maturity": int(up[-1]),
                 "Senescence": int(down[0]), "Dormancy": int(down[-1])}
    else:
        marks = {"Greenup": 100, "Maturity": 150, "Senescence": 260, "Dormancy": 300}

    marks["Greenup"] = max(1, min(364, marks["Greenup"]))
    marks["Maturity"] = max(marks["Greenup"] + 1, min(364, marks["Maturity"]))
    marks["Senescence"] = max(marks["Maturity"] + 1, min(364, marks["Senescence"]))
    marks["Dormancy"] = max(marks["Senescence"] + 1, min(364, marks["Dormancy"]))
    return marks


def _mica_align(ref_curve: np.ndarray, tgt_curve: np.ndarray):
    """MICA: landmark-aware monotonic warp alignment"""
    ref = _clean_curve(ref_curve)
    tgt = _clean_curve(tgt_curve)
    if ref.size != tgt.size or ref.size < 10:
        return tgt, ref, False, {}, {}

    ref_marks = _extract_landmarks(ref)
    tgt_marks = _extract_landmarks(tgt)

    n = ref.size
    x_ref = np.array([0, ref_marks["Greenup"], ref_marks["Maturity"],
                      ref_marks["Senescence"], ref_marks["Dormancy"], n - 1], dtype=float)
    x_tgt = np.array([0, tgt_marks["Greenup"], tgt_marks["Maturity"],
                      tgt_marks["Senescence"], tgt_marks["Dormancy"], n - 1], dtype=float)
    x_ref = np.maximum.accumulate(x_ref)
    x_tgt = np.maximum.accumulate(x_tgt)
    for i in range(1, len(x_ref)):
        if x_ref[i] <= x_ref[i - 1]:
            x_ref[i] = x_ref[i - 1] + 1
        if x_tgt[i] <= x_tgt[i - 1]:
            x_tgt[i] = x_tgt[i - 1] + 1

    if PchipInterpolator is not None:
        inverse_warp = PchipInterpolator(np.clip(x_ref, 0, n - 1), np.clip(x_tgt, 0, n - 1))
    elif interp1d is not None:
        inverse_warp = interp1d(np.clip(x_ref, 0, n - 1), np.clip(x_tgt, 0, n - 1),
                                kind='linear', fill_value='extrapolate')
    else:
        return tgt, ref, False, ref_marks, tgt_marks

    mapped = np.clip(inverse_warp(np.arange(n)), 0, n - 1)
    if interp1d is not None:
        aligned = interp1d(np.arange(n), tgt, kind='linear', fill_value='extrapolate')(mapped)
    else:
        aligned = np.interp(mapped, np.arange(n), tgt)

    return aligned, ref, True, ref_marks, tgt_marks


def calculate_similarity(
    local_ndvi: List[float], local_lst: List[float],
    golden_ndvi: List[float], golden_lst: List[float],
) -> Dict[str, Any]:
    """计算物候相似度，返回 0-100 综合评分及各子项"""
    local_ndvi = np.array(local_ndvi, dtype=float)
    local_lst = np.array(local_lst, dtype=float)
    golden_ndvi = np.array(golden_ndvi, dtype=float)
    golden_lst = np.array(golden_lst, dtype=float)

    raw_local = local_ndvi.copy()
    raw_golden = golden_ndvi.copy()

    # MICA alignment
    try:
        aligned, aligned_ref, mica_ok, meta_ref, meta_tgt = _mica_align(golden_ndvi, local_ndvi)
        if mica_ok:
            local_ndvi, golden_ndvi = aligned, aligned_ref
    except Exception:
        mica_ok = False

    # Pearson
    try:
        ndvi_corr = float(np.corrcoef(local_ndvi, golden_ndvi)[0, 1])
        ndvi_corr = 0.0 if np.isnan(ndvi_corr) else ndvi_corr
    except Exception:
        ndvi_corr = 0.0

    try:
        lst_corr = float(np.corrcoef(local_lst, golden_lst)[0, 1])
        lst_corr = 0.0 if np.isnan(lst_corr) else lst_corr
    except Exception:
        lst_corr = 0.0

    # Milestones
    try:
        if find_peaks:
            lp, _ = find_peaks(raw_local, height=np.max(raw_local) * 0.5, distance=50)
            gp, _ = find_peaks(raw_golden, height=np.max(raw_golden) * 0.5, distance=50)
            lv, _ = find_peaks(-raw_local, distance=50)
            gv, _ = find_peaks(-raw_golden, distance=50)
        else:
            lp = gp = lv = gv = np.array([])

        lp_day = int(lp[0]) if len(lp) > 0 else int(np.argmax(raw_local))
        gp_day = int(gp[0]) if len(gp) > 0 else int(np.argmax(raw_golden))
        lv_day = int(lv[0]) if len(lv) > 0 else int(np.argmin(raw_local))
        gv_day = int(gv[0]) if len(gv) > 0 else int(np.argmin(raw_golden))

        peak_match = max(0, 100 - abs(lp_day - gp_day) * 0.5)
        valley_match = max(0, 100 - abs(lv_day - gv_day) * 0.5)
    except Exception:
        peak_match = valley_match = 0
        lp_day = gp_day = lv_day = gv_day = None

    # Slope similarity
    try:
        slope_dist = float(np.mean(np.abs(np.gradient(local_ndvi) - np.gradient(golden_ndvi))))
        slope_sim = float(100 * np.exp(-100 * slope_dist))
    except Exception:
        slope_sim = 0.0

    # Weighted overall (NDVI 30%, LST 20%, Milestones 20%, Slope 30%)
    overall = (0.30 * max(0, ndvi_corr) * 100
               + 0.20 * max(0, lst_corr) * 100
               + 0.20 * (peak_match + valley_match) / 2
               + 0.30 * slope_sim)
    overall = min(100, max(0, overall))

    return {
        "similarity_score": round(overall, 2),
        "ndvi_correlation": round(ndvi_corr, 3),
        "lst_correlation": round(lst_corr, 3),
        "slope_similarity": round(slope_sim, 2),
        "milestones_match": {
            "local_peak_day": lp_day, "golden_peak_day": gp_day,
            "peak_match_score": peak_match,
            "local_valley_day": lv_day, "golden_valley_day": gv_day,
            "valley_match_score": valley_match,
            "mica_applied": mica_ok,
        },
    }
