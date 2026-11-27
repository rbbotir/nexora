from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import json, sqlite3, os, secrets
from pathlib import Path

ROOT = Path(__file__).parent
DB = ROOT / "nexora.db"
ADMIN_PIN = os.environ.get("NEXORA_ADMIN_PIN", "2468")  # Change before sharing/deploying.

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, category TEXT NOT NULL,
            price REAL NOT NULL, image TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT ''
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL, phone TEXT NOT NULL,
            address TEXT NOT NULL, items TEXT NOT NULL,
            total REAL NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        if con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            sample = [
                ("Orbit Wireless Headphones","Tech",39.99,"https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80","Comfortable everyday wireless headphones."),
                ("Glow Desk Light","Home",24.50,"https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=800&q=80","A clean light for your desk setup."),
                ("Magnetic Car Holder","Auto",14.99,"https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80","A handy phone holder for your car.")
            ]
            con.executemany("INSERT INTO products(name,category,price,image,description) VALUES(?,?,?,?,?)", sample)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, data, status=200):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def read_json(self):
        n = int(self.headers.get("Content-Length", "0"))
        if n > 100_000:
            raise ValueError("Request too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/products":
            with db() as con:
                rows = con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
            return self.send_json([dict(r) for r in rows])
        if path == "/api/orders":
            if self.headers.get("X-Admin-Pin") != ADMIN_PIN:
                return self.send_json({"error":"Admin PIN required"}, 401)
            with db() as con:
                rows = con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
            return self.send_json([dict(r) for r in rows])
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self.read_json()
            if path == "/api/orders":
                customer = str(data.get("customer","")).strip()[:100]
                phone = str(data.get("phone","")).strip()[:40]
                address = str(data.get("address","")).strip()[:300]
                items = data.get("items", [])
                if not customer or not phone or not address or not isinstance(items, list) or not items:
                    return self.send_json({"error":"Please complete all fields and add an item."}, 400)
                clean, total = [], 0
                with db() as con:
                    for item in items[:30]:
                        pid, qty = int(item["id"]), max(1, min(20, int(item["qty"])))
                        product = con.execute("SELECT id,name,price FROM products WHERE id=?", (pid,)).fetchone()
                        if not product: continue
                        clean.append({"id":product["id"],"name":product["name"],"price":product["price"],"qty":qty})
                        total += product["price"] * qty
                    if not clean: return self.send_json({"error":"No valid products in cart."}, 400)
                    cur = con.execute("INSERT INTO orders(customer,phone,address,items,total) VALUES(?,?,?,?,?)",
                                      (customer,phone,address,json.dumps(clean),round(total,2)))
                    oid = cur.lastrowid
                return self.send_json({"ok":True,"order_id":oid,"total":round(total,2)}, 201)
            if path == "/api/products":
                if self.headers.get("X-Admin-Pin") != ADMIN_PIN:
                    return self.send_json({"error":"Wrong admin PIN"}, 401)
                name = str(data.get("name","")).strip()[:100]
                category = str(data.get("category","Other")).strip()[:40]
                description = str(data.get("description","")).strip()[:500]
                image = str(data.get("image","")).strip()[:1000]
                price = float(data.get("price",0))
                if not name or price <= 0 or price > 100000:
                    return self.send_json({"error":"Enter a name and a valid price."}, 400)
                with db() as con:
                    cur = con.execute("INSERT INTO products(name,category,price,image,description) VALUES(?,?,?,?,?)",
                                      (name,category,price,image,description))
                return self.send_json({"ok":True,"id":cur.lastrowid}, 201)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return self.send_json({"error":"Invalid request data."}, 400)
        return self.send_json({"error":"Not found"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith("/api/products/"):
            if self.headers.get("X-Admin-Pin") != ADMIN_PIN:
                return self.send_json({"error":"Wrong admin PIN"}, 401)
            try: pid = int(path.rsplit("/",1)[1])
            except ValueError: return self.send_json({"error":"Invalid product"}, 400)
            with db() as con: con.execute("DELETE FROM products WHERE id=?", (pid,))
            return self.send_json({"ok":True})
        return self.send_json({"error":"Not found"}, 404)

if __name__ == "__main__":
    init_db()
    print("NEXORA running at http://localhost:8000")
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
