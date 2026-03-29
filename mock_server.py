#!/usr/bin/env python3
"""mock_server - In-memory mock HTTP server for testing."""
import sys, re, json

class MockRequest:
    def __init__(self, method, path, headers=None, body=None, query=None):
        self.method = method.upper()
        self.path = path
        self.headers = headers or {}
        self.body = body
        self.query = query or {}

class MockResponse:
    def __init__(self, status=200, body=None, headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {"Content-Type": "application/json"}

class MockServer:
    def __init__(self):
        self.routes = []
        self.requests = []
        self.default_response = MockResponse(404, {"error": "Not Found"})
    def when(self, method, path_pattern):
        route = {"method": method.upper(), "pattern": re.compile(f"^{path_pattern}$"), "response": None, "count": 0}
        self.routes.append(route)
        return RouteBuilder(route)
    def handle(self, request):
        self.requests.append(request)
        for route in self.routes:
            if route["method"] == request.method and route["pattern"].match(request.path):
                route["count"] += 1
                resp = route["response"]
                if callable(resp):
                    return resp(request)
                return resp
        return self.default_response
    def verify(self, method, path, times=None):
        count = sum(1 for r in self.requests if r.method == method.upper() and r.path == path)
        if times is not None:
            return count == times
        return count > 0
    def reset(self):
        self.requests.clear()
        for r in self.routes:
            r["count"] = 0

class RouteBuilder:
    def __init__(self, route):
        self.route = route
    def respond(self, status=200, body=None):
        self.route["response"] = MockResponse(status, body)
        return self
    def respond_with(self, handler):
        self.route["response"] = handler
        return self

def test():
    server = MockServer()
    server.when("GET", "/users").respond(200, [{"id": 1, "name": "Alice"}])
    server.when("POST", "/users").respond(201, {"id": 2})
    server.when("GET", "/users/\d+").respond_with(
        lambda req: MockResponse(200, {"id": req.path.split("/")[-1]})
    )
    r1 = server.handle(MockRequest("GET", "/users"))
    assert r1.status == 200
    assert len(r1.body) == 1
    r2 = server.handle(MockRequest("POST", "/users", body={"name": "Bob"}))
    assert r2.status == 201
    r3 = server.handle(MockRequest("GET", "/users/42"))
    assert r3.status == 200 and r3.body["id"] == "42"
    r4 = server.handle(MockRequest("DELETE", "/nope"))
    assert r4.status == 404
    assert server.verify("GET", "/users", times=1)
    assert server.verify("POST", "/users")
    assert not server.verify("PUT", "/users")
    print("OK: mock_server")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: mock_server.py test")
