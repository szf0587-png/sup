from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from server.integrations import iserver_client
from server.api import map_services


class MapTileTests(unittest.TestCase):
    def test_leaflet_tile_url_uses_iserver_zxy_cache_endpoint(self):
        with patch.object(iserver_client, "get_map_service", return_value={
            "maps": [{"name": "China100_2021_Light"}],
        }):
            url = iserver_client.get_map_tile_url("China100", "China100_2021_Light")

        self.assertIn("/zxyTileImage.png", url)
        self.assertIn("z={z}&x={x}&y={y}", url)
        self.assertIn("width=256&height=256", url)
        self.assertNotIn("/tileImage.png", url)

    def test_tile_config_limits_leaflet_to_available_china100_levels(self):
        map_info = {"maps": [{"name": "China100_2021_Light"}]}
        with patch.object(iserver_client, "get_map_service", return_value=map_info), patch.object(
            iserver_client,
            "get_map_tile_url",
            return_value="http://iserver/maps/China100_2021_Light/zxyTileImage.png?z={z}&x={x}&y={y}",
        ):
            config = asyncio.run(map_services.get_tile_layer_config(
                "China100",
                "China100_2021_Light",
                SimpleNamespace(id="test-user"),
            ))

        self.assertEqual(config["min_zoom"], 3)
        self.assertEqual(config["max_zoom"], 11)


if __name__ == "__main__":
    unittest.main()
