#!/usr/bin/env python3
"""Mock HTTP server for testing."""
import sys,socket,json,threading,time
class MockServer:
    def __init__(self,port=0):
        self.routes={};self.requests=[];self.sock=socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind(('127.0.0.1',port));self.sock.listen(5)
        self.port=self.sock.getsockname()[1];self._running=True
        self._thread=threading.Thread(target=self._serve,daemon=True);self._thread.start()
    def route(self,method,path,status=200,body="",headers=None):
        self.routes[(method.upper(),path)]=(status,body,headers or {})
    def _serve(self):
        while self._running:
            try:
                self.sock.settimeout(0.5);conn,_=self.sock.accept()
                data=conn.recv(4096).decode();lines=data.split('\r\n')
                method,path,_=lines[0].split(' ',2)
                self.requests.append({"method":method,"path":path,"raw":data})
                key=(method,path)
                if key in self.routes:
                    status,body,hdrs=self.routes[key]
                else: status,body,hdrs=404,"Not Found",{}
                if isinstance(body,dict): body=json.dumps(body);hdrs["Content-Type"]="application/json"
                resp=f"HTTP/1.1 {status} OK\r\nContent-Length: {len(body)}\r\n"
                for k,v in hdrs.items(): resp+=f"{k}: {v}\r\n"
                resp+=f"\r\n{body}"
                conn.sendall(resp.encode());conn.close()
            except socket.timeout: pass
    def stop(self): self._running=False;self.sock.close()
    @property
    def url(self): return f"http://127.0.0.1:{self.port}"
def main():
    server=MockServer()
    server.route("GET","/api/users",200,{"users":[{"id":1,"name":"Alice"}]})
    server.route("POST","/api/users",201,{"id":2,"name":"Bob"})
    server.route("GET","/health",200,"OK")
    print(f"Mock server at {server.url}")
    # Test with socket
    import urllib.request
    for path in ["/api/users","/health","/missing"]:
        try:
            resp=urllib.request.urlopen(f"{server.url}{path}")
            print(f"  GET {path}: {resp.status} {resp.read().decode()}")
        except Exception as e: print(f"  GET {path}: {e}")
    print(f"\nRequests logged: {len(server.requests)}")
    server.stop()
if __name__=="__main__": main()
