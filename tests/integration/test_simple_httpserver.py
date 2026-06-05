"""简单的 httpserver 测试"""

from pytest_httpserver import HTTPServer


def test_httpserver_basic(httpserver: HTTPServer) -> None:
    """测试 httpserver 是否正常工作"""
    # 定义 mock 响应
    httpserver.expect_request("/test").respond_with_json({"status": "ok"})

    # 发送请求
    import requests

    response = requests.get(httpserver.url_for("/test"))

    # 验证响应
    assert response.json() == {"status": "ok"}


def test_httpserver_mock_path(httpserver: HTTPServer) -> None:
    """测试 httpserver 路径匹配"""
    httpserver.expect_request("/api/users/1").respond_with_json({"id": 1, "name": "Alice"})

    import requests

    response = requests.get(httpserver.url_for("/api/users/1"))

    assert response.json() == {"id": 1, "name": "Alice"}
