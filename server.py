#!/usr/bin/env python3
"""Çıtır Pizza & Cafe order server. Stdlib only. Data stays outside the git repo."""
import hashlib
import json
import os
import re
import secrets
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DATA = ROOT / "data" / "store.json"
LOCK = threading.Lock()
LOGIN_HITS = {}
TZ = ZoneInfo("Europe/Istanbul")

def item(iid, cat, name, desc, price, name_en=None, desc_en=None, popular=False, options=None):
    return {
        "id": iid, "cat": cat, "name": name, "nameEn": name_en or name,
        "desc": desc, "descEn": desc_en or desc, "price": price,
        "available": True, "popular": popular, "options": options or [],
    }

SEED_ITEMS = [
    item("pizza-misto", "pizza", "Pizza Misto", "Pizza sosu, mozarella, sucuk, jambon, mantar, yeşil biber, zeytin, salam", 420, desc_en="Pizza sauce, mozzarella, sausage, ham, mushrooms, green pepper, olive, salami", popular=True),
    item("pizza-pargina", "pizza", "Pizza Pargina", "Pizza sosu, mozarella, jambon, mantar", 390, desc_en="Pizza sauce, mozzarella, ham, mushroom"),
    item("pizza-pepperoni", "pizza", "Pizza Pepperoni", "Pizza sosu, mozarella, sucuk", 360, desc_en="Pizza sauce, mozzarella, sausage", popular=True),
    item("pizza-pollo", "pizza", "Pizza Pollo", "Pizza sosu, mozarella, tavuk, jalapeno, yeşil biber", 390, desc_en="Pizza sauce, mozzarella, chicken, jalapeno, green pepper"),
    item("pizza-prociutto", "pizza", "Pizza Prociutto", "Pizza sosu, mozarella, jambon", 370, desc_en="Pizza sauce, mozzarella, ham"),
    item("pizza-quatro", "pizza", "Pizza Quatro", "Pizza sosu, mozarella, mantar, salam, jambon", 400, desc_en="Pizza sauce, mozzarella, mushroom, salami, ham"),
    item("pizza-salami", "pizza", "Pizza Salami", "Pizza sosu, mozarella, salam", 350, desc_en="Pizza sauce, mozzarella, salami"),
    item("pizza-tonno", "pizza", "Pizza Tonno", "Pizza sosu, mozarella, ton balığı, soğan, mısır, kapari", 390, desc_en="Pizza sauce, mozzarella, tuna, onion, corn, capers"),
    item("pizza-veggie", "pizza", "Pizza Veggie", "Pizza sosu, mozarella, yeşil biber, domates, kabak, patlıcan, kapya, soğan", 360, desc_en="Pizza sauce, mozzarella, green pepper, tomato, zucchini, aubergine, capia pepper, onion"),
    item("spagetti-bolonez", "makarna", "Spagetti Bolonez", "Kıymalı domates sos", 280, name_en="Spaghetti Bolognese", desc_en="Beef tomato sauce"),
    item("carbonara", "makarna", "Carbonara", "Kremalı, pastırma veya jambon", 290, desc_en="Cream sauce"),
    item("penne-arabiyatta", "makarna", "Penne Arabiyatta", "Acılı domates sos", 270, name_en="Penne Arrabbiata", desc_en="Spicy tomato sauce"),
    item("lazanya", "makarna", "Lazanya", "Fırın lazanya", 320, name_en="Lasagne", desc_en="Baked lasagne", popular=True),
    item("kori-tavuk", "tavuk", "Köri Soslu Tavuk", "Köri soslu tavuk", 340, name_en="Chicken with Curry", desc_en="Chicken with curry sauce"),
    item("peynirli-tavuk", "tavuk", "Peynirli Tavuk", "Peynirli tavuk", 340, name_en="Chicken with Cheese", desc_en="Chicken with cheese"),
    item("soya-tavuk", "tavuk", "Soya Soslu Tavuk", "Soya soslu tavuk", 330, name_en="Chicken with Soya", desc_en="Chicken with soya sauce"),
    item("tavuk-sis", "izgara", "Tavuk Şiş", "Izgara tavuk şiş", 360, name_en="Chicken Shish", desc_en="Grilled chicken shish"),
    item("et-sis", "izgara", "Et Şiş", "Izgara et şiş", 450, name_en="Meat Shish", desc_en="Grilled meat shish", popular=True),
    item("tavuk-izgara", "izgara", "Tavuk Izgara", "Izgara tavuk", 340, name_en="Grilled Chicken", desc_en="Grilled chicken"),
    item("izgara-kofte", "izgara", "Izgara Köfte", "Izgara köfte", 320, name_en="Grilled Meatballs", desc_en="Grilled meatballs"),
    item("hamburger", "burger", "Hamburger", "Klasik hamburger", 260, desc_en="Classic hamburger"),
    item("cheese-burger", "burger", "Cheese Burger", "Peynirli hamburger", 290, desc_en="Hamburger with cheese", popular=True),
    item("nugget", "cocuk", "Chicken Nugget", "Çocuk porsiyonu", 220, name_en="Chicken Nugget", desc_en="Kids portion"),
    item("cocuk-kofte", "cocuk", "Izgara Köfte", "Çocuk porsiyonu", 220, name_en="Grilled Meatballs", desc_en="Kids portion"),
    item("cocuk-margarita", "cocuk", "Pizza Margarita", "Çocuk porsiyonu", 240, name_en="Pizza Margherita", desc_en="Kids portion"),
    item("cocuk-pepperoni", "cocuk", "Pizza Pepperoni", "Çocuk porsiyonu", 250, desc_en="Kids portion"),
    item("cocuk-salami", "cocuk", "Pizza Salami", "Çocuk porsiyonu", 250, desc_en="Kids portion"),
    item("cheesecake-limon", "tatli", "Limonlu Cheesecake", "Limonlu cheesecake", 180, name_en="Lemon Cheesecake", desc_en="Lemon cheesecake"),
    item("cheesecake-frambuaz", "tatli", "Frambuazlı Cheesecake", "Frambuazlı cheesecake", 180, name_en="Raspberry Cheesecake", desc_en="Raspberry cheesecake"),
    item("tiramisu", "tatli", "Tiramisu", "Tiramisu", 190, desc_en="Tiramisu"),
    item("cola", "icecek", "Cola", "Soğuk içecek", 60, desc_en="Cold drink"),
    item("cola-light", "icecek", "Cola Light", "Soğuk içecek", 60, desc_en="Cold drink"),
    item("cola-zero", "icecek", "Cola Zero", "Soğuk içecek", 60, desc_en="Cold drink"),
    item("fanta", "icecek", "Fanta", "Soğuk içecek", 60, desc_en="Cold drink"),
    item("sprite", "icecek", "Sprite", "Soğuk içecek", 60, desc_en="Cold drink"),
    item("icetea", "icecek", "Icetea", "Soğuk içecek", 60, desc_en="Cold drink"),
    item("portakal", "icecek", "Portakal Suyu", "Taze veya şişe, mutfağa sorun", 70, name_en="Orange Juice", desc_en="Orange juice"),
    item("limonata", "icecek", "Limonata", "Limonata", 65, name_en="Lemonade", desc_en="Lemonade"),
    item("su", "icecek", "Su", "Su", 25, name_en="Water", desc_en="Water"),
    item("ayran", "icecek", "Ayran", "Ayran", 40, desc_en="Ayran"),
    item("soda", "icecek", "Soda", "Soda", 35, desc_en="Soda"),
    item("meyveli-soda", "icecek", "Meyveli Soda", "Meyveli soda", 45, name_en="Fruit Soda", desc_en="Fruit soda"),
    item("meyve-suyu", "icecek", "Meyve Suyu", "Şeftali, vişne veya karışık", 55, name_en="Fruit Juice", desc_en="Peach, sour cherry or mixed", options=["Şeftali", "Vişne", "Karışık"]),
    item("cay", "sicak", "Çay", "Çay", 30, name_en="Tea", desc_en="Tea"),
    item("turk-kahvesi", "sicak", "Türk Kahvesi", "Türk kahvesi", 60, name_en="Turkish Coffee", desc_en="Turkish coffee"),
    item("damla-sakizli", "sicak", "Damlasakızlı Türk Kahvesi", "Damla sakızlı", 70, name_en="Mastic Turkish Coffee", desc_en="Turkish coffee with mastic"),
    item("menengic", "sicak", "Menengiç", "Menengiç kahvesi", 65, name_en="Menengic Coffee", desc_en="Menengic coffee"),
    item("nescafe", "sicak", "Nescafe", "Hazır kahve", 55, desc_en="Instant coffee"),
    item("bitki-cay", "sicak", "Bitki Çayları", "Bitki çayı", 50, name_en="Herbal Tea", desc_en="Herbal tea"),
    item("sicak-cikolata", "sicak", "Sıcak Çikolata", "Sıcak çikolata", 70, name_en="Hot Chocolate", desc_en="Hot chocolate"),
]

CATEGORIES = [
    {"id": "pizza", "tr": "Pizzalar", "en": "Pizzas"},
    {"id": "makarna", "tr": "Makarnalar", "en": "Pasta"},
    {"id": "tavuk", "tr": "Soslu Tavuklar", "en": "Chicken"},
    {"id": "izgara", "tr": "Izgaralar", "en": "Grill"},
    {"id": "burger", "tr": "Burgerler", "en": "Burgers"},
    {"id": "cocuk", "tr": "Çocuk Menüsü", "en": "Kids"},
    {"id": "tatli", "tr": "Tatlılar", "en": "Desserts"},
    {"id": "icecek", "tr": "İçecekler", "en": "Drinks"},
    {"id": "sicak", "tr": "Sıcak İçecekler", "en": "Hot drinks"},
]

def default_store():
    return {
        "settings": {
            "name": "Çıtır Pizza & Cafe",
            "phone": "0242 538 86 84",
            "phoneTel": "+902425388684",
            "mobile": "0555 152 86 84",
            "mobileTel": "+905551528684",
            "address": "Karakuşlar Sokak A Blok No: 2, Ağız ve Diş Sağlığı Hastanesi karşısı, 07400 Oba, Alanya",
            "area": "Oba, Alanya",
            "lat": 36.540978,
            "lng": 32.047333,
            "openTime": "10:30",
            "closeTime": "22:00",
            "sundayClosed": True,
            "announcement": "Kapıda nakit veya kart. Oba ve yakınına teslimat.",
            "deliveryFee": 40,
            "minDelivery": 200,
            "deliveryZone": "Oba ve yakını",
            "orderingOpen": True,
            "forceOpen": False,
            "googleAdsId": "",
            "conversionLabel": "",
            "ga4Id": "",
            "siteUrl": "",
            "pricesAreDraft": True,
        },
        "categories": CATEGORIES,
        "items": SEED_ITEMS,
        "orders": [],
        "users": [],
        "sessions": [],
        "seq": 1000,
    }

def load():
    if not DATA.exists():
        store = default_store()
        save(store)
        return store
    return json.loads(DATA.read_text())

def save(store):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, ensure_ascii=False, indent=2))
    tmp.replace(DATA)

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return salt, digest

def ensure_admin(store):
    if store["users"]:
        return None
    password = os.environ.get("CITIR_ADMIN_PASSWORD") or secrets.token_urlsafe(9)
    salt, digest = hash_password(password)
    store["users"].append({
        "id": "u1", "username": "admin", "name": "Yönetici", "role": "admin",
        "salt": salt, "hash": digest, "active": True,
    })
    save(store)
    (ROOT / "ILK-GIRIS.txt").write_text("kullanici: admin\nsifre: %s\n" % password)
    print("Ilk giris: admin / %s" % password, flush=True)
    return password

def public_settings(s):
    closed, reason = is_closed(s)
    return {k: s[k] for k in s if k not in ("googleAdsId", "conversionLabel", "ga4Id")} | {
        "closed": closed, "closedReason": reason,
        "adsConfigured": bool(s.get("googleAdsId") or s.get("ga4Id")),
        "googleAdsId": s.get("googleAdsId") or "",
        "conversionLabel": s.get("conversionLabel") or "",
        "ga4Id": s.get("ga4Id") or "",
    }

def is_closed(s):
    if not s.get("orderingOpen", True):
        return True, "Sipariş geçici olarak kapalı."
    if s.get("forceOpen"):
        return False, ""
    now = datetime.now(TZ)
    if s.get("sundayClosed", True) and now.weekday() == 6:
        return True, "Pazar günleri kapalıyız."
    oh, om = [int(x) for x in s.get("openTime", "10:30").split(":")]
    ch, cm = [int(x) for x in s.get("closeTime", "22:00").split(":")]
    minutes = now.hour * 60 + now.minute
    if minutes < oh * 60 + om or minutes >= ch * 60 + cm:
        return True, "Şu an kapalıyız. Açılış %s, kapanış %s." % (s.get("openTime"), s.get("closeTime"))
    return False, ""

def user_public(u):
    return {"id": u["id"], "username": u["username"], "name": u["name"], "role": u["role"], "active": u.get("active", True)}

def session_user(store, token):
    if not token:
        return None
    digest = hashlib.sha256(token.encode()).hexdigest()
    now = time.time()
    for sess in store["sessions"]:
        if sess["hash"] == digest and sess["exp"] > now:
            for user in store["users"]:
                if user["id"] == sess["uid"] and user.get("active", True):
                    return user
    return None

def clean(text, limit):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit]

def money_total(store, lines, fulfillment):
    items = {i["id"]: i for i in store["items"]}
    resolved = []
    subtotal = 0
    for line in lines:
        src = items.get(line.get("id"))
        if not src or not src.get("available", True):
            raise ValueError("Menüde olmayan veya tükenen ürün: %s" % line.get("id"))
        qty = int(line.get("qty") or 0)
        if qty < 1 or qty > 20:
            raise ValueError("Adet 1 ile 20 arasında olmalı.")
        option = clean(line.get("option"), 40)
        if src.get("options") and option not in src["options"]:
            raise ValueError("%s için tat seçin." % src["name"])
        price = int(src["price"])
        subtotal += price * qty
        resolved.append({
            "id": src["id"], "name": src["name"], "qty": qty, "price": price,
            "option": option, "note": clean(line.get("note"), 140),
        })
    delivery = int(store["settings"]["deliveryFee"]) if fulfillment == "delivery" else 0
    return resolved, subtotal, delivery, subtotal + delivery

class Handler(BaseHTTPRequestHandler):
    server_version = "CitirOrder/1.0"

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args), flush=True)

    def send_json(self, code, payload, extra_headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, code, body, content_type, extra=None):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > 100_000:
            raise ValueError("İstek çok büyük.")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode() or "{}")

    def cookie(self, name):
        header = self.headers.get("Cookie") or ""
        for part in header.split(";"):
            if "=" in part:
                key, value = part.strip().split("=", 1)
                if key == name:
                    return value
        return ""

    def client_ip(self):
        return (self.headers.get("X-Forwarded-For") or self.client_address[0]).split(",")[0].strip()

    def require_same_origin(self):
        if self.command == "GET":
            return True
        if self.headers.get("X-Requested-With") != "citir":
            self.send_json(403, {"error": "İstek reddedildi."})
            return False
        return True

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/menu":
            with LOCK:
                store = load()
            settings = public_settings(store["settings"])
            self.send_json(200, {"settings": settings, "categories": store["categories"], "items": [
                {k: i[k] for k in ("id", "cat", "name", "nameEn", "desc", "descEn", "price", "available", "popular", "options")}
                for i in store["items"]
            ]})
            return
        if path == "/api/track":
            qs = parse_qs(parsed.query)
            code = clean((qs.get("code") or [""])[0], 20).upper()
            phone = re.sub(r"\D", "", (qs.get("phone") or [""])[0])
            with LOCK:
                store = load()
            order = next((o for o in store["orders"] if o["code"] == code), None)
            if not order or phone[-4:] != re.sub(r"\D", "", order["phone"])[-4:]:
                self.send_json(404, {"error": "Sipariş bulunamadı. Kod ve telefonun son 4 hanesini kontrol edin."})
                return
            self.send_json(200, {"order": public_order(order)})
            return
        if path == "/api/panel/state":
            self.panel_state()
            return
        if path == "/robots.txt":
            self.send_bytes(200, "User-agent: *\nAllow: /\nDisallow: /panel\nDisallow: /api/\nSitemap: /sitemap.xml\n", "text/plain; charset=utf-8")
            return
        if path == "/sitemap.xml":
            with LOCK:
                store = load()
            base = (store["settings"].get("siteUrl") or "").rstrip("/")
            loc = (base + "/") if base else "/"
            xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\"><url><loc>%s</loc></url></urlset>" % loc
            self.send_bytes(200, xml, "application/xml; charset=utf-8")
            return
        if path in ("/", "/index.html"):
            self.send_page("index.html")
            return
        if path in ("/panel", "/panel.html"):
            self.send_page("panel.html")
            return
        rel = path.lstrip("/")
        target = (STATIC / rel).resolve()
        if not str(target).startswith(str(STATIC)) or not target.is_file():
            self.send_json(404, {"error": "Yok"})
            return
        kind = "image/jpeg" if target.suffix == ".jpg" else "application/octet-stream"
        if target.suffix == ".css":
            kind = "text/css; charset=utf-8"
        if target.suffix == ".js":
            kind = "text/javascript; charset=utf-8"
        if target.suffix == ".svg":
            kind = "image/svg+xml"
        self.send_bytes(200, target.read_bytes(), kind, {"Cache-Control": "public, max-age=3600"})

    def send_page(self, name):
        html = (STATIC / name).read_text()
        if name == "index.html":
            with LOCK:
                store = load()
            html = html.replace("<!--SSR-->", ssr_menu(store))
            html = html.replace("<!--LD-->", json.dumps(json_ld(store), ensure_ascii=False))
        self.send_bytes(200, html, "text/html; charset=utf-8", {"Cache-Control": "no-store"})

    def do_POST(self):
        if not self.require_same_origin():
            return
        path = urlparse(self.path).path
        try:
            data = self.read_json()
        except Exception:
            self.send_json(400, {"error": "Geçersiz istek."})
            return
        if path == "/api/orders":
            self.create_order(data)
            return
        if path == "/api/login":
            self.login(data)
            return
        if path == "/api/logout":
            self.logout()
            return
        if path == "/api/panel/settings":
            self.save_settings(data)
            return
        if path == "/api/panel/item":
            self.save_item(data)
            return
        if path == "/api/panel/order":
            self.save_order(data)
            return
        if path == "/api/panel/user":
            self.save_user(data)
            return
        if path == "/api/panel/password":
            self.change_password(data)
            return
        self.send_json(404, {"error": "Yok"})

    def auth(self, role=None):
        with LOCK:
            store = load()
            user = session_user(store, self.cookie("citir_session"))
        if not user:
            self.send_json(401, {"error": "Giriş gerekli."})
            return None, None
        if role == "admin" and user["role"] != "admin":
            self.send_json(403, {"error": "Bu işlem için yönetici yetkisi gerekir."})
            return None, None
        return store, user

    def panel_state(self):
        with LOCK:
            store = load()
            user = session_user(store, self.cookie("citir_session"))
        if not user:
            self.send_json(401, {"error": "Giriş gerekli."})
            return
        payload = {
            "user": user_public(user),
            "orders": list(reversed(store["orders"]))[:200],
            "settings": store["settings"] if user["role"] == "admin" else public_settings(store["settings"]),
            "categories": store["categories"],
            "items": store["items"] if user["role"] == "admin" else [],
            "users": [user_public(u) for u in store["users"]] if user["role"] == "admin" else [],
        }
        self.send_json(200, payload)

    def login(self, data):
        ip = self.client_ip()
        now = time.time()
        hits = [t for t in LOGIN_HITS.get(ip, []) if now - t < 600]
        if len(hits) >= 8:
            self.send_json(429, {"error": "Çok fazla deneme. 10 dakika sonra tekrar dene."})
            return
        username = clean(data.get("username"), 40).lower()
        password = str(data.get("password") or "")
        with LOCK:
            store = load()
            user = next((u for u in store["users"] if u["username"] == username and u.get("active", True)), None)
            ok = False
            if user:
                salt, digest = hash_password(password, user["salt"])
                ok = secrets.compare_digest(digest, user["hash"])
            if not ok:
                hits.append(now)
                LOGIN_HITS[ip] = hits
                self.send_json(401, {"error": "Kullanıcı adı veya şifre hatalı."})
                return
            token = secrets.token_urlsafe(32)
            store["sessions"] = [s for s in store["sessions"] if s["exp"] > now][-40:]
            store["sessions"].append({
                "hash": hashlib.sha256(token.encode()).hexdigest(),
                "uid": user["id"],
                "exp": now + 60 * 60 * 14,
            })
            save(store)
        self.send_json(200, {"user": user_public(user)}, {
            "Set-Cookie": "citir_session=%s; HttpOnly; SameSite=Lax; Path=/; Max-Age=50400" % token,
        })

    def logout(self):
        token = self.cookie("citir_session")
        digest = hashlib.sha256(token.encode()).hexdigest() if token else ""
        with LOCK:
            store = load()
            store["sessions"] = [s for s in store["sessions"] if s["hash"] != digest]
            save(store)
        self.send_json(200, {"ok": True}, {"Set-Cookie": "citir_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"})

    def create_order(self, data):
        with LOCK:
            store = load()
            closed, reason = is_closed(store["settings"])
            if closed:
                self.send_json(409, {"error": reason})
                return
            name = clean(data.get("name"), 80)
            phone = re.sub(r"[^\d+]", "", str(data.get("phone") or ""))
            fulfillment = data.get("fulfillment")
            payment = data.get("payment")
            address = clean(data.get("address"), 180)
            note = clean(data.get("note"), 240)
            if len(name) < 2 or len(re.sub(r"\D", "", phone)) < 10:
                self.send_json(400, {"error": "Ad ve geçerli bir telefon gerekli."})
                return
            if fulfillment not in ("pickup", "delivery") or payment not in ("cash", "card"):
                self.send_json(400, {"error": "Teslimat ve ödeme seçin."})
                return
            if fulfillment == "delivery" and len(address) < 8:
                self.send_json(400, {"error": "Adrese teslim için açık adres yazın."})
                return
            try:
                lines, subtotal, delivery, total = money_total(store, data.get("items") or [], fulfillment)
            except ValueError as exc:
                self.send_json(400, {"error": str(exc)})
                return
            if not lines:
                self.send_json(400, {"error": "Sepet boş."})
                return
            if fulfillment == "delivery" and subtotal < int(store["settings"]["minDelivery"]):
                self.send_json(400, {"error": "Adrese teslim için minimum tutar %s TL." % store["settings"]["minDelivery"]})
                return
            store["seq"] += 1
            order = {
                "id": "o%s" % store["seq"],
                "code": "CP-%s" % store["seq"],
                "createdAt": datetime.now(TZ).isoformat(timespec="minutes"),
                "status": "new",
                "name": name, "phone": phone, "fulfillment": fulfillment,
                "payment": payment, "address": address if fulfillment == "delivery" else "",
                "note": note, "items": lines, "subtotal": subtotal,
                "deliveryFee": delivery, "total": total,
            }
            store["orders"].append(order)
            save(store)
        self.send_json(201, {"order": public_order(order)})

    def save_settings(self, data):
        store, user = self.auth("admin")
        if not user:
            return
        allowed = ["phone", "phoneTel", "mobile", "mobileTel", "address", "announcement", "openTime", "closeTime", "deliveryZone", "googleAdsId", "conversionLabel", "ga4Id", "siteUrl"]
        with LOCK:
            store = load()
            for key in allowed:
                if key in data:
                    store["settings"][key] = clean(data[key], 240)
            for key in ("deliveryFee", "minDelivery"):
                if key in data:
                    store["settings"][key] = max(0, int(data[key]))
            for key in ("orderingOpen", "forceOpen", "sundayClosed", "pricesAreDraft"):
                if key in data:
                    store["settings"][key] = bool(data[key])
            save(store)
            settings = store["settings"]
        self.send_json(200, {"settings": settings})

    def save_item(self, data):
        store, user = self.auth("admin")
        if not user:
            return
        with LOCK:
            store = load()
            iid = clean(data.get("id"), 40)
            found = next((i for i in store["items"] if i["id"] == iid), None)
            if data.get("create"):
                if found or not iid:
                    self.send_json(400, {"error": "Yeni ürün için benzersiz kısa kod yaz."})
                    return
                found = item(iid, clean(data.get("cat") or "pizza", 20), "Yeni ürün", "", 0)
                store["items"].append(found)
            if not found:
                self.send_json(404, {"error": "Ürün yok."})
                return
            if "name" in data:
                found["name"] = clean(data["name"], 80)
            if "nameEn" in data:
                found["nameEn"] = clean(data["nameEn"], 80)
            if "desc" in data:
                found["desc"] = clean(data["desc"], 220)
            if "descEn" in data:
                found["descEn"] = clean(data["descEn"], 220)
            if "price" in data:
                found["price"] = max(0, int(data["price"]))
            if "available" in data:
                found["available"] = bool(data["available"])
            if "cat" in data:
                found["cat"] = clean(data["cat"], 20)
            if "popular" in data:
                found["popular"] = bool(data["popular"])
            save(store)
        self.send_json(200, {"item": found})

    def save_order(self, data):
        store, user = self.auth()
        if not user:
            return
        status = data.get("status")
        if status not in ("new", "preparing", "ready", "on_the_way", "delivered", "cancelled"):
            self.send_json(400, {"error": "Geçersiz durum."})
            return
        with LOCK:
            store = load()
            order = next((o for o in store["orders"] if o["id"] == data.get("id")), None)
            if not order:
                self.send_json(404, {"error": "Sipariş yok."})
                return
            order["status"] = status
            save(store)
        self.send_json(200, {"order": order})

    def save_user(self, data):
        store, user = self.auth("admin")
        if not user:
            return
        username = clean(data.get("username"), 40).lower()
        if not re.fullmatch(r"[a-z0-9._-]{3,40}", username):
            self.send_json(400, {"error": "Kullanıcı adı 3-40 karakter, harf ve rakam olmalı."})
            return
        role = data.get("role") if data.get("role") in ("admin", "staff") else "staff"
        with LOCK:
            store = load()
            found = next((u for u in store["users"] if u["username"] == username), None)
            if data.get("create"):
                if found:
                    self.send_json(400, {"error": "Bu kullanıcı adı var."})
                    return
                password = str(data.get("password") or "")
                if len(password) < 8:
                    self.send_json(400, {"error": "Şifre en az 8 karakter."})
                    return
                salt, digest = hash_password(password)
                found = {"id": "u" + secrets.token_hex(4), "username": username, "name": clean(data.get("name") or username, 60), "role": role, "salt": salt, "hash": digest, "active": True}
                store["users"].append(found)
            elif not found:
                self.send_json(404, {"error": "Kullanıcı yok."})
                return
            else:
                if "name" in data:
                    found["name"] = clean(data["name"], 60)
                if "role" in data and not (found["id"] == user["id"] and role != "admin"):
                    found["role"] = role
                if "active" in data and found["id"] != user["id"]:
                    found["active"] = bool(data["active"])
                if data.get("password"):
                    if len(str(data["password"])) < 8:
                        self.send_json(400, {"error": "Şifre en az 8 karakter."})
                        return
                    salt, digest = hash_password(str(data["password"]))
                    found["salt"], found["hash"] = salt, digest
            if not any(u["role"] == "admin" and u.get("active", True) for u in store["users"]):
                self.send_json(400, {"error": "Son yönetici kapatılamaz."})
                return
            save(store)
        self.send_json(200, {"user": user_public(found)})

    def change_password(self, data):
        store, user = self.auth()
        if not user:
            return
        current = str(data.get("current") or "")
        nxt = str(data.get("next") or "")
        if len(nxt) < 8:
            self.send_json(400, {"error": "Yeni şifre en az 8 karakter."})
            return
        with LOCK:
            store = load()
            found = next(u for u in store["users"] if u["id"] == user["id"])
            _, digest = hash_password(current, found["salt"])
            if not secrets.compare_digest(digest, found["hash"]):
                self.send_json(400, {"error": "Mevcut şifre hatalı."})
                return
            salt, digest = hash_password(nxt)
            found["salt"], found["hash"] = salt, digest
            save(store)
        self.send_json(200, {"ok": True})

def public_order(order):
    return {k: order[k] for k in ("code", "createdAt", "status", "fulfillment", "payment", "items", "subtotal", "deliveryFee", "total", "name")}

def ssr_menu(store):
    parts = []
    for cat in store["categories"]:
        rows = [i for i in store["items"] if i["cat"] == cat["id"]]
        if not rows:
            continue
        lis = "".join("<li><strong>%s</strong> — %s <span>%s TL</span></li>" % (i["name"], i["desc"], i["price"]) for i in rows)
        parts.append("<section><h2>%s</h2><ul>%s</ul></section>" % (cat["tr"], lis))
    return "".join(parts)

def json_ld(store):
    s = store["settings"]
    return {
        "@context": "https://schema.org",
        "@type": "Restaurant",
        "name": s["name"],
        "servesCuisine": ["Pizza", "Italian", "Turkish"],
        "telephone": s["phoneTel"],
        "address": {"@type": "PostalAddress", "streetAddress": "Karakuşlar Sokak A Blok No: 2", "addressLocality": "Alanya", "addressRegion": "Antalya", "postalCode": "07400", "addressCountry": "TR"},
        "geo": {"@type": "GeoCoordinates", "latitude": s["lat"], "longitude": s["lng"]},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], "opens": s["openTime"], "closes": s["closeTime"]}],
        "url": s.get("siteUrl") or None,
        "hasMenu": {"@type": "Menu", "hasMenuSection": [
            {"@type": "MenuSection", "name": c["tr"], "hasMenuItem": [
                {"@type": "MenuItem", "name": i["name"], "description": i["desc"], "offers": {"@type": "Offer", "price": i["price"], "priceCurrency": "TRY"}}
                for i in store["items"] if i["cat"] == c["id"] and i.get("available", True)
            ]} for c in store["categories"]
        ]},
        "potentialAction": {"@type": "OrderAction", "target": (s.get("siteUrl") or "") + "/"},
    }

def main():
    with LOCK:
        store = load()
        ensure_admin(store)
    port = int(os.environ.get("PORT", "4173"))
    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print("listening %s" % port, flush=True)
    httpd.serve_forever()

if __name__ == "__main__":
    main()
