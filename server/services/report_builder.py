"""报告生成器 — 固定模板 HTML/PDF 报告"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime as dt

from server.config import DATA_DIR


def build_report(
    run_id: str,
    screening_result: dict,
    parcel_result: dict | None = None,
) -> str:
    """
    基于固定模板生成决策报告 HTML。

    Returns:
        完整 HTML 字符串
    """
    now = dt.now().strftime("%Y-%m-%d %H:%M")
    county = screening_result.get("county", "洛南县")
    towns = screening_result.get("towns", [])
    gs_name = screening_result.get("golden_standard_name", "未指定")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>天眼寻珍·苍穹 — 决策报告</title>
<style>
body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; color: #333; }}
h1 {{ border-bottom: 3px solid #2c7a4b; padding-bottom: 10px; }}
h2 {{ color: #2c7a4b; margin-top: 30px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
th {{ background: #2c7a4b; color: white; }}
.grade-s {{ background: #e8f5e9; font-weight: bold; }}
.grade-a {{ background: #c8e6c9; }}
.bar {{ display: inline-block; height: 20px; border-radius: 3px; background: #4caf50; }}
.footer {{ margin-top: 40px; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
</style>
</head>
<body>
<h1>天眼寻珍·苍穹 — 特色农业适生区决策报告</h1>
<p><strong>分析任务:</strong> {run_id} | <strong>生成时间:</strong> {now}</p>
<p><strong>研究区:</strong> 陕西省商洛市{county}</p>
<p><strong>金标准:</strong> {gs_name}</p>

<h2>一、区域筛选结果 — Top 5 候选乡镇</h2>
<table>
<tr><th>排名</th><th>乡镇</th><th>综合评分</th><th>适宜性</th><th>物候匹配</th><th>数据覆盖率</th></tr>
"""
    for i, t in enumerate(towns, 1):
        overall = t.get("overall_score", 0)
        suit = t.get("suitability_score", 0)
        phen = t.get("phenology_score", 0)
        cov = t.get("data_coverage", 0)
        grade = "S" if overall >= 85 else "A" if overall >= 75 else "B" if overall >= 65 else "C"
        row_class = f"grade-{grade.lower()}" if grade in ("S", "A") else ""
        html += f"""<tr class="{row_class}">
<td>{i}</td><td>{t.get('town_name', '-')}</td>
<td>{overall} <span class="bar" style="width:{overall}px"></span></td>
<td>{suit}</td><td>{phen}</td><td>{cov:.0%}</td>
</tr>"""

    html += "</table>"

    # 地块精评（如果有）
    if parcel_result:
        ahp = parcel_result.get("ahp", {})
        phen = parcel_result.get("phenology", {})
        spatial = parcel_result.get("spatial", {})
        fac = parcel_result.get("facilities", {})
        overall = parcel_result.get("overall_score", 0)
        grade = parcel_result.get("grade", "C")

        html += f"""
<h2>二、地块精评 — {parcel_result.get('town_code', '-')}</h2>
<p>综合评分: <strong>{overall}</strong> (等级: {grade})</p>

<h3>2.1 AHP 适宜性</h3>
<table><tr><th>因子</th><th>评分</th><th>权重</th></tr>"""
        for name, f in ahp.get("factors", {}).items():
            html += f"<tr><td>{name}</td><td>{f['score']}</td><td>{f['weight']:.0%}</td></tr>"
        html += "</table>"

        html += f"""
<h3>2.2 物候匹配</h3>
<p>综合相似度: {phen.get('similarity_score', '-')} | NDVI 相关: {phen.get('ndvi_correlation', '-')} | LST 相关: {phen.get('lst_correlation', '-')}</p>

<h3>2.3 空间约束</h3>
<p>可用面积: {spatial.get('buffer', {}).get('available_area_km2', '-')} km² | 约束占比: {spatial.get('buffer', {}).get('constraint_ratio', 0):.0%}</p>

<h3>2.4 设施证据</h3>
<p>大棚数量: {fac.get('greenhouse_count', '-')} | 面积: {fac.get('greenhouse_area_ha', '-')} ha | 密度评分: {fac.get('density_score', '-')}</p>
"""

    html += f"""
<div class="footer">
<p>天眼寻珍·苍穹 v2.0 | SuperMap AI GIS 农业遥感智能监测与决策平台</p>
<p>数据来源: GEE MODIS/006, SRTM GL1, 金标准库 | 本报告基于固定案例生成，仅供决策参考</p>
</div>
</body>
</html>"""
    return html


def export_report(
    run_id: str,
    screening_result: dict,
    parcel_result: dict | None = None,
    output_dir: Path | None = None,
) -> Path:
    """生成报告并保存为 HTML 文件"""
    if output_dir is None:
        output_dir = DATA_DIR / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    html = build_report(run_id, screening_result, parcel_result)
    path = output_dir / f"report_{run_id}.html"
    path.write_text(html, encoding="utf-8")
    return path
