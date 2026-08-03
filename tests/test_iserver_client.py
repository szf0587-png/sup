import asyncio

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
