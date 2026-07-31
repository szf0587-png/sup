from pathlib import Path

from server.services import town_ranking


def test_rank_towns_returns_positioned_demo_results_when_gis_data_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Given no GIS files, the screening surface still receives ranked map data."""
    monkeypatch.setattr(town_ranking, "DATA_DIR", tmp_path)

    result = town_ranking.rank_towns("golden-standard", top_n=5, county="洛南县")

    assert result["status"] == "mock"
    assert result["data_mode"] == "mock"
    assert result["county"] == "洛南县"
    assert len(result["towns"]) == 5
    assert all("latitude" in town and "longitude" in town for town in result["towns"])
    assert [town["overall_score"] for town in result["towns"]] == sorted(
        (town["overall_score"] for town in result["towns"]),
        reverse=True,
    )
