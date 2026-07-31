"""自动化测试所有重构后的 API"""
import requests
import json
import sys
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# 设置输出编码
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors='replace')

def print_section(title):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_result(test_name, success, details=""):
    """打印测试结果"""
    status = "[OK]" if success else "[FAIL]"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")

def main():
    print_section("API 自动化测试脚本")
    print(f"服务器地址: {BASE_URL}\n")

    # 存储测试数据
    test_data = {
        "token": None,
        "project_id": None,
        "dataset_id": None,
        "standard_id": None,
    }

    # ==================== 测试 1: 用户认证 ====================
    print_section("测试 1: 用户认证")

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )

        if response.status_code == 200:
            data = response.json()
            test_data["token"] = data.get("access_token")
            print_result("登录", True, f"Token: {test_data['token'][:50]}...")
        else:
            print_result("登录", False, f"状态码: {response.status_code}")
            return
    except Exception as e:
        print_result("登录", False, str(e))
        return

    # 设置认证头
    headers = {"Authorization": f"Bearer {test_data['token']}"}

    # ==================== 测试 2: 获取用户信息 ====================
    print_section("测试 2: 获取用户信息")

    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_result("获取用户信息", True, f"用户: {data['username']} ({data['role']})")
        else:
            print_result("获取用户信息", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取用户信息", False, str(e))

    # ==================== 测试 3: 项目管理 ====================
    print_section("测试 3: 项目管理")

    # 3.1 创建项目
    try:
        response = requests.post(
            f"{BASE_URL}/api/projects",
            headers=headers,
            json={
                "name": "自动化测试项目",
                "description": "API 自动化测试创建的项目",
                "region": {
                    "type": "Polygon",
                    "coordinates": [[[109.0, 33.0], [110.0, 33.0], [110.0, 34.0], [109.0, 34.0], [109.0, 33.0]]]
                }
            }
        )

        if response.status_code == 201:
            data = response.json()
            test_data["project_id"] = data["id"]
            print_result("创建项目", True, f"项目ID: {test_data['project_id']}")
        else:
            print_result("创建项目", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("创建项目", False, str(e))

    # 3.2 列出项目
    try:
        response = requests.get(f"{BASE_URL}/api/projects", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_result("列出项目", True, f"项目数量: {data['total']}")
        else:
            print_result("列出项目", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("列出项目", False, str(e))

    # ==================== 测试 4: 数据集管理 ====================
    print_section("测试 4: 数据集管理")

    # 4.1 创建测试 GeoJSON 文件
    test_geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [110.15, 34.09]
            },
            "properties": {"name": "测试点"}
        }]
    }

    test_file_path = Path("test_data.geojson")
    with open(test_file_path, "w", encoding="utf-8") as f:
        json.dump(test_geojson, f)

    # 4.2 上传数据集
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_data.geojson", f, "application/json")}
            data = {"name": "自动化测试数据集", "description": "测试上传"}
            response = requests.post(
                f"{BASE_URL}/api/datasets/upload",
                headers=headers,
                files=files,
                data=data
            )

        if response.status_code == 201:
            data = response.json()
            test_data["dataset_id"] = data["id"]
            print_result("上传数据集", True, f"数据集ID: {test_data['dataset_id']}")
        else:
            print_result("上传数据集", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("上传数据集", False, str(e))
    finally:
        # 清理测试文件
        if test_file_path.exists():
            test_file_path.unlink()

    # 4.3 列出数据集
    try:
        response = requests.get(f"{BASE_URL}/api/datasets", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_result("列出数据集", True, f"数据集数量: {data['total']}")
        else:
            print_result("列出数据集", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("列出数据集", False, str(e))

    # ==================== 测试 5: 金标准管理 ====================
    print_section("测试 5: 金标准管理")

    # 5.1 创建金标准
    try:
        response = requests.post(
            f"{BASE_URL}/api/golden-standards",
            headers=headers,
            json={
                "model_name": "自动化测试金标准",
                "crop_type": "核桃",
                "latitude": 34.09,
                "longitude": 110.15,
                "location_description": "洛南县古城镇",
                "suitability_params": {
                    "slope": {"min": 0, "max": 25},
                    "elevation": {"min": 800, "max": 1500}
                },
                "phenology_params": {
                    "ndvi_curve": [0.2 + 0.6 * ((i - 180) ** 2 / -2000) for i in range(365)],
                    "lst_curve": [20 + 15 * (i / 365) for i in range(365)]
                },
                "tags": ["测试", "自动化"]
            }
        )

        if response.status_code == 201:
            data = response.json()
            test_data["standard_id"] = data["id"]
            print_result("创建金标准", True, f"金标准ID: {test_data['standard_id']}")
        else:
            print_result("创建金标准", False, f"状态码: {response.status_code}, {response.text}")
    except Exception as e:
        print_result("创建金标准", False, str(e))

    # 5.2 列出金标准
    try:
        response = requests.get(f"{BASE_URL}/api/golden-standards", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print_result("列出金标准", True, f"金标准数量: {data['total']}")
        else:
            print_result("列出金标准", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("列出金标准", False, str(e))

    # 5.3 获取金标准详情
    if test_data["standard_id"]:
        try:
            response = requests.get(
                f"{BASE_URL}/api/golden-standards/{test_data['standard_id']}",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print_result("获取金标准详情", True, f"名称: {data['model_name']}")
            else:
                print_result("获取金标准详情", False, f"状态码: {response.status_code}")
        except Exception as e:
            print_result("获取金标准详情", False, str(e))

    # ==================== 测试 6: 物候匹配 ====================
    print_section("测试 6: 物候匹配")

    if test_data["standard_id"]:
        try:
            response = requests.post(
                f"{BASE_URL}/api/phenology/match",
                headers=headers,
                json={
                    "lat": 34.09,
                    "lon": 110.15,
                    "golden_standard_id": test_data["standard_id"],
                    "top_n": 3
                }
            )

            if response.status_code == 200:
                data = response.json()
                print_result("物候匹配", True, f"匹配数量: {len(data.get('matches', []))}")
            else:
                print_result("物候匹配", False, f"状态码: {response.status_code}, {response.text}")
        except Exception as e:
            print_result("物候匹配", False, str(e))
    else:
        print_result("物候匹配", False, "没有可用的金标准ID")

    # ==================== 测试 7: 区域筛选 ====================
    print_section("测试 7: 区域筛选")

    if test_data["standard_id"]:
        try:
            response = requests.post(
                f"{BASE_URL}/api/screening/runs",
                headers=headers,
                json={
                    "golden_standard_id": test_data["standard_id"],
                    "county": "洛南县",
                    "top_n": 5
                }
            )

            if response.status_code == 200:
                data = response.json()
                print_result("区域筛选", True, f"状态: {data.get('status', 'unknown')}")
            else:
                print_result("区域筛选", False, f"状态码: {response.status_code}, {response.text}")
        except Exception as e:
            print_result("区域筛选", False, str(e))
    else:
        print_result("区域筛选", False, "没有可用的金标准ID")

    # ==================== 测试 8: 地块精评 ====================
    print_section("测试 8: 地块精评")

    if test_data["standard_id"]:
        try:
            response = requests.post(
                f"{BASE_URL}/api/parcels/evaluate",
                headers=headers,
                json={
                    "town_code": "610000",
                    "parcel_geojson": {
                        "type": "Polygon",
                        "coordinates": [[[110.0, 34.0], [110.1, 34.0], [110.1, 34.1], [110.0, 34.1], [110.0, 34.0]]]
                    },
                    "golden_standard_id": test_data["standard_id"]
                }
            )

            if response.status_code == 200:
                data = response.json()
                print_result("地块精评", True, f"状态: {data.get('status', 'unknown')}")
            else:
                print_result("地块精评", False, f"状态码: {response.status_code}, {response.text}")
        except Exception as e:
            print_result("地块精评", False, str(e))
    else:
        print_result("地块精评", False, "没有可用的金标准ID")

    # ==================== 测试总结 ====================
    print_section("测试总结")
    print("\n测试数据ID:")
    print(f"  - 项目ID: {test_data['project_id']}")
    print(f"  - 数据集ID: {test_data['dataset_id']}")
    print(f"  - 金标准ID: {test_data['standard_id']}")
    print("\n所有测试完成！")
    print("\n你可以访问 http://localhost:8000/docs 查看 API 文档")
    print("或在 Swagger UI 中手动测试其他功能\n")

if __name__ == "__main__":
    main()
