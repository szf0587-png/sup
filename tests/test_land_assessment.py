from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SRC_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SRC_ROOT.parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fastapi import HTTPException

from server.api import land_assessment as land_api
from server.integrations import iserver_client
from server.schemas.land_assessment import LandAssessmentRequest
from server.services import land_assessment as land_service
from server.services import spatial_analysis


BOUNDARY = {
    "type": "Polygon",
    "coordinates": [[[110.0, 34.0], [110.1, 34.0], [110.1, 34.1], [110.0, 34.1], [110.0, 34.0]]],
}


class FakeQuery:
    def __init__(self, project):
        self.project = project

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.project


class FakeDB:
    def __init__(self, project=None):
        self.project = project

    def query(self, model):
        return FakeQuery(self.project)


def feature_collection():
    return {"type": "FeatureCollection", "features": []}


class LandAssessmentTests(unittest.TestCase):
    def test_administrative_context_returns_name_and_map_property(self):
        query = {
            "feature_count": 1,
            "source": "iserver:data-China100",
            "resource_url": "http://example.test/result",
            "features": [{
                "fieldNames": ["NAME", "PAC"],
                "fieldValues": ["内蒙古自治区", "150000"],
                "geometry": BOUNDARY,
            }],
        }
        with patch.object(spatial_analysis.iserver_client, "query_features_by_geometry", return_value=query):
            result = spatial_analysis.administrative_context(BOUNDARY)

        self.assertEqual(result["administrative_names"], ["内蒙古自治区"])
        self.assertEqual(result["visualization"]["features"][0]["properties"]["NAME"], "内蒙古自治区")

    def test_water_constraints_include_polygon_and_line_water_layers(self):
        datasets = {layer["dataset"] for layer in spatial_analysis.DEFAULT_CONSTRAINT_LAYERS}
        self.assertTrue({"Water_R", "Lake_R", "MainRiver_R", "MainRiver_L", "River_L"}.issubset(datasets))

    def test_multisegment_road_is_returned_as_multilinestring(self):
        geometry = {
            "type": "LINE",
            "parts": [2, 2],
            "points": [
                {"x": 107.58027108, "y": 42.39801112},
                {"x": 107.58053765, "y": 42.3980417},
                {"x": 107.581, "y": 42.399},
                {"x": 107.582, "y": 42.4},
            ],
        }

        converted = iserver_client.supermap_to_geojson_geometry(geometry)

        self.assertEqual(converted["type"], "MultiLineString")
        self.assertEqual(converted["coordinates"][0][0], [107.58027108, 42.39801112])
        self.assertEqual(converted["coordinates"][1][1], [107.582, 42.4])

    def test_capabilities_only_expose_real_components(self):
        with patch.object(land_service.iserver_client, "check_iserver", return_value=True), patch.object(
            land_service.iserver_client, "list_basemap_services", return_value=[]
        ), patch.object(land_service.iserver_client, "list_data_datasets", return_value=["Water_R", "NationalRd_L"]):
            caps = land_service.list_land_assessment_capabilities()

        self.assertTrue(caps["iServer"])
        self.assertIn("water_constraint", caps["components"])
        self.assertFalse(caps["dem_available"])
        self.assertFalse(caps["realspace_available"])

    def test_diagnostic_returns_map_ready_feature_collection(self):
        water = {"feature_count": 2, "source": "iserver:data-China100", "visualization": feature_collection()}
        with patch.object(land_service, "overlay_constraint_stats", return_value=water):
            result = land_service.diagnose_land_component("water_constraint", BOUNDARY)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["source"], "iserver:data-China100")
        self.assertEqual(result["visualization"]["type"], "FeatureCollection")
        self.assertEqual(result["result"]["water_constraint"]["feature_count"], 2)

    def test_evaluation_writes_real_evidence_snapshot(self):
        tmp_path = WORKSPACE_ROOT / ".tmp_land_assessment_test"
        tmp_path.mkdir(exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(tmp_path, ignore_errors=True))
        buffer = {"source": "iserver:spatialAnalysis", "visualization": feature_collection()}
        water = {"source": "iserver:data-China100", "visualization": feature_collection()}
        roads = {"source": "iserver:data-China100", "visualization": feature_collection()}
        admin = {"source": "iserver:data-China100", "visualization": feature_collection()}
        with patch.object(land_service, "DATA_DIR", tmp_path), patch.object(
            land_service, "compute_buffer_stats", return_value=buffer
        ), patch.object(land_service, "overlay_constraint_stats", return_value=water), patch.object(
            land_service, "road_accessibility", return_value=roads
        ), patch.object(land_service, "administrative_context", return_value=admin):
            result = land_service.evaluate_land_resource(BOUNDARY, user_id="user-1")

        self.assertEqual(result["data_mode"], "iserver")
        self.assertEqual(result["grade"], "N/A")
        saved = json.loads(Path(result["snapshot_path"]).read_text(encoding="utf-8"))
        self.assertEqual(saved["user_id"], "user-1")
        self.assertEqual(saved["spatial"]["buffer"]["source"], "iserver:spatialAnalysis")

    def test_route_rejects_foreign_project(self):
        project = SimpleNamespace(id="proj-1", user_id="user-2", is_deleted=False)
        with self.assertRaises(HTTPException) as ctx:
            land_api.evaluate(
                req=LandAssessmentRequest(boundary=BOUNDARY, project_id="proj-1"),
                current_user=SimpleNamespace(id="user-1", role="user"),
                db=FakeDB(project),
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_diagnostic_route_accepts_real_buffer_component(self):
        captured = {}

        def fake_diagnose(**kwargs):
            captured.update(kwargs)
            return {"component": "buffer", "status": "completed"}

        with patch.object(land_api, "diagnose_land_component", side_effect=fake_diagnose):
            result = land_api.diagnose(
                component="buffer",
                req=LandAssessmentRequest(boundary=BOUNDARY, buffer_distance_m=800),
                current_user=SimpleNamespace(id="user-1", role="user"),
                db=FakeDB(),
            )
        self.assertEqual(result["component"], "buffer")
        self.assertEqual(captured["buffer_distance_m"], 800)

    def test_diagnostic_route_maps_iserver_failure_to_503(self):
        with patch.object(land_api, "diagnose_land_component", side_effect=RuntimeError("iServer unavailable")):
            with self.assertRaises(HTTPException) as ctx:
                land_api.diagnose(
                    component="buffer",
                    req=LandAssessmentRequest(boundary=BOUNDARY),
                    current_user=SimpleNamespace(id="user-1", role="user"),
                    db=FakeDB(),
                )
        self.assertEqual(ctx.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
