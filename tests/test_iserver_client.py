import asyncio

import pytest
import requests

from server.api import scene_3d
from server.integrations import iserver_client


def test_iserver_session_does_not_parse_broken_user_netrc(monkeypatch):
    iserver_client.reset_session()
    monkeypatch.setattr(iserver_client, "_refresh_token", lambda: None)

    session = iserver_client._get_session()

    assert session.trust_env is False
    iserver_client.reset_session()


def test_scene_list_returns_degraded_state_when_iserver_is_offline(monkeypatch):
    class OfflineSession:
        def get(self, *args, **kwargs):
            raise requests.ConnectionError("iServer offline")

    monkeypatch.setattr(iserver_client, "_get_session", lambda: OfflineSession())

    result = asyncio.run(scene_3d.list_3d_scenes(scene_3d.User(id="user_test", role="user")))

    assert result["status"] == "degraded"
    assert result["count"] == 0
    assert result["scenes"] == []
    assert "iServer" in result["reason"]


def test_unpublish_treats_missing_remote_service_as_idempotent_success(monkeypatch):
    class Response:
        status_code = 404

    class Session:
        def delete(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(iserver_client, "_get_session", lambda: Session())

    assert iserver_client.delete_service("missing-service") is True
    assert iserver_client.unpublish_service("missing-service") == {"status": "unpublished"}


@pytest.mark.parametrize("status_code", [200, 201])
def test_data_preview_converts_feature_resource_to_geojson_feature_collection(monkeypatch, status_code):
    class Response:
        text = ""

        def __init__(self, payload, response_status=status_code):
            self._payload = payload
            self.status_code = response_status

        def json(self):
            return self._payload

    class Session:
        def post(self, url, **kwargs):
            calls.append((url, kwargs["json"]))
            return Response({"featureUriList": ["http://iserver/features/1"], "totalCount": 1})

        def get(self, url, **kwargs):
            assert url.endswith(".json")
            return Response({
                "ID": 7,
                "fieldNames": ["name"],
                "fieldValues": ["Boundary"],
                "geometry": {
                    "type": "REGION", "parts": [5],
                    "points": [{"x": 100, "y": 20}, {"x": 101, "y": 20}, {"x": 101, "y": 21}, {"x": 100, "y": 20}, {"x": 100, "y": 20}],
                },
            }, 200)

    calls = []
    monkeypatch.setattr(iserver_client, "_get_session", lambda: Session())

    preview = iserver_client.get_data_service("owner_ds", "boundary_R", max_features=10)

    assert preview["type"] == "FeatureCollection"
    assert preview["features"] == [{
        "type": "Feature", "id": 7, "properties": {"name": "Boundary"},
        "geometry": {"type": "Polygon", "coordinates": [[[100, 20], [101, 20], [101, 21], [100, 20], [100, 20]]]},
    }]
    assert calls[0][1]["datasetNames"] == ["owner_ds:boundary_R"]
