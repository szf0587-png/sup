"""Tests for the iServer terrain diagnostics contract."""

import asyncio

from server.api import scene_3d


class DummyUser:
    id = "user_test"
    role = "user"


def test_terrain_data_url_uses_terrain_layer_data_name():
    layers = [{"layer3DType": "TerrainFileLayer", "dataName": "GridToDEMCache"}]

    assert scene_3d._terrain_data_url("3D-luonan", layers) == (
        "http://127.0.0.1:8090/iserver/services/3D-luonan/rest/realspace/"
        "datas/GridToDEMCache"
    )


def test_terrain_diagnostics_reports_available_sct(monkeypatch):
    layer = {
        "layer3DType": "TerrainFileLayer",
        "dataName": "GridToDEMCache",
        "bounds": {"left": 110.0, "bottom": 34.0, "right": 110.3, "top": 34.3},
    }
    monkeypatch.setattr(scene_3d, "_resolve_service", lambda _session, _name: ("3D-luonan", "luonan"))
    monkeypatch.setattr(scene_3d, "_scene_catalog", lambda _session, _service: [{"name": "LuonanScene"}])
    monkeypatch.setattr(scene_3d, "_scene_url", lambda service, scene: f"/{service}/{scene}")
    monkeypatch.setattr(scene_3d, "_json_get", lambda _session, _url, timeout=8: {"layers": [layer]})
    monkeypatch.setattr(scene_3d.iserver_client, "_get_session", lambda: object())

    result = asyncio.run(scene_3d.get_terrain_diagnostics("luonan", DummyUser()))

    assert result["available"] is True
    assert result["provider_type"] == "sct"
    assert result["layer_name"] == "GridToDEMCache"
    assert result["bounds"] == {"west": 110.0, "south": 34.0, "east": 110.3, "north": 34.3}


def test_terrain_diagnostics_explains_missing_layer(monkeypatch):
    monkeypatch.setattr(scene_3d, "_resolve_service", lambda _session, _name: ("3D-luonan", "luonan"))
    monkeypatch.setattr(scene_3d, "_scene_catalog", lambda _session, _service: [{"name": "LuonanScene"}])
    monkeypatch.setattr(scene_3d, "_scene_url", lambda service, scene: f"/{service}/{scene}")
    monkeypatch.setattr(scene_3d, "_json_get", lambda _session, _url, timeout=8: {"layers": []})
    monkeypatch.setattr(scene_3d.iserver_client, "_get_session", lambda: object())

    result = asyncio.run(scene_3d.get_terrain_diagnostics("luonan", DummyUser()))

    assert result["available"] is False
    assert result["provider_type"] == "ellipsoid"
    assert "TerrainFileLayer" in result["reason"]
