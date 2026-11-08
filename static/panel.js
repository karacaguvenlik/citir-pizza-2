var panel = { user: null, tab: "orders", data: null, seen: 0, sound: false };
var STATUS = { new: "Yeni", preparing: "Hazırlanıyor", ready: "Hazır", on_the_way: "Yolda", delivered: "Teslim", cancelled: "İptal" };
function esc(value) { return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) { return { "&": "&", "<": "<", ">": ">", '"': "&quot;", "'": "&#39;" }[ch]; }); }
function money(n) { return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY", maximumFractionDigits: 0 }).format(n); }
async function api(path, body) {
  var opts = { method: body ? "POST" : "GET", headers: { "Content-Type": "application/json", "X-Requested-With": "citir" } };
  if (body) opts.body = JSON.stringify(body);
  var res = await fetch(path, opts);
  var data = await res.json();
  if (!res.ok) throw new Error(data.error || "Hata");
  return data;
}
function showLogin(message) {
  document.getElementById("login").hidden = false;
  document.getElementById("app").hidden = true;
  document.getElementById("login-error").textContent = message || "";
}
function showApp() {
  document.getElementById("login").hidden = true;
  document.getElementById("app").hidden = false;
  document.getElementById("who").textContent = panel.user.name + " · " + panel.user.role;
  document.getElementById("draft-warn").hidden = !(panel.data.settings && panel.data.settings.pricesAreDraft);
  document.querySelectorAll("[data-tab]").forEach(function (btn) {
    btn.hidden = panel.user.role !== "admin" && btn.dataset.tab !== "orders";
    btn.classList.toggle("on", btn.dataset.tab === panel.tab);
  });
  draw();
}
function draw() {
  var view = document.getElementById("view");
  if (panel.tab === "orders") view.innerHTML = drawOrders();
  if (panel.tab === "menu") view.innerHTML = drawMenu();
  if (panel.tab === "settings") view.innerHTML = drawSettings();
  if (panel.tab === "users") view.innerHTML = drawUsers();
}
function drawOrders() {
  var orders = panel.data.orders || [];
  if (!orders.length) return "<p>Henüz sipariş yok.</p>";
  return orders.map(function (order) {
    var items = order.items.map(function (line) {
      return "<li>" + line.qty + " x " + esc(line.name) + (line.option ? " (" + esc(line.option) + ")" : "") + " · " + money(line.price * line.qty) + "</li>";
    }).join("");
    var buttons = ["preparing", "ready", "on_the_way", "delivered", "cancelled"].map(function (status) {
      return "<button type='button' data-status='" + status + "' data-id='" + order.id + "'>" + STATUS[status] + "</button>";
    }).join(" ");
    return "<article class='order " + order.status + "'><div class='row'><strong>" + esc(order.code) + "</strong><span class='tag'>" + (STATUS[order.status] || order.status) + "</span><span>" + esc(order.createdAt) + "</span></div><p>" + esc(order.name) + " · <a href='tel:" + esc(order.phone) + "'>" + esc(order.phone) + "</a> · " + (order.fulfillment === "delivery" ? "Teslimat" : "Gel-al") + " · " + (order.payment === "card" ? "Kapıda kart" : "Kapıda nakit") + "</p><p>" + esc(order.address) + "</p><ul>" + items + "</ul><p>Not: " + esc(order.note || "-") + "</p><p><strong>" + money(order.total) + "</strong></p><div class='row'>" + buttons + "</div></article>";
  }).join("");
}
function drawMenu() {
  var rows = (panel.data.items || []).map(function (item) {
    return "<tr><td>" + esc(item.name) + "<br><small>" + esc(item.desc) + "</small></td><td><input data-price='" + item.id + "' type='number' min='0' value='" + item.price + "'></td><td><input data-avail='" + item.id + "' type='checkbox'" + (item.available ? " checked" : "") + "></td><td><button type='button' data-save-item='" + item.id + "'>Kaydet</button></td></tr>";
  }).join("");
  return "<h2>Menü fiyatları</h2><p>Müşteri kaydettiğin fiyatı görür. 0 yazarsan bedava sipariş oluşur.</p><table><tr><th>Ürün</th><th>Fiyat TL</th><th>Satışta</th><th></th></tr>" + rows + "</table><h3>Yeni ürün</h3><form id='new-item'><input name='id' placeholder='kisa-kod' required> <input name='name' placeholder='Ad' required> <input name='price' type='number' placeholder='Fiyat' required> <select name='cat'>" + panel.data.categories.map(function (cat) { return "<option value='" + cat.id + "'>" + cat.tr + "</option>"; }).join("") + "</select> <button class='solid' type='submit'>Ekle</button></form>";
}
function drawSettings() {
  var s = panel.data.settings;
  return "<h2>Site ayarları</h2><form id='settings'><label>Duyuru<input name='announcement' value='" + esc(s.announcement) + "'></label><label>Telefon<input name='phone' value='" + esc(s.phone) + "'></label><label>Cep<input name='mobile' value='" + esc(s.mobile) + "'></label><label>Adres<textarea name='address'>" + esc(s.address) + "</textarea></label><label>Açılış<input name='openTime' value='" + esc(s.openTime) + "'></label><label>Kapanış<input name='closeTime' value='" + esc(s.closeTime) + "'></label><label>Teslimat bölgesi<input name='deliveryZone' value='" + esc(s.deliveryZone) + "'></label><label>Teslimat ücreti<input name='deliveryFee' type='number' value='" + s.deliveryFee + "'></label><label>Minimum teslimat<input name='minDelivery' type='number' value='" + s.minDelivery + "'></label><label>Google Ads kimliği<input name='googleAdsId' placeholder='AW-...' value='" + esc(s.googleAdsId) + "'></label><label>Dönüşüm etiketi<input name='conversionLabel' value='" + esc(s.conversionLabel) + "'></label><label>GA4 kimliği<input name='ga4Id' placeholder='G-...' value='" + esc(s.ga4Id) + "'></label><label>Site adresi<input name='siteUrl' placeholder='https://...' value='" + esc(s.siteUrl) + "'></label><label><input name='orderingOpen' type='checkbox'" + (s.orderingOpen ? " checked" : "") + "> Sipariş açık</label><label><input name='forceOpen' type='checkbox'" + (s.forceOpen ? " checked" : "") + "> Saat dışı da sipariş al</label><label><input name='sundayClosed' type='checkbox'" + (s.sundayClosed ? " checked" : "") + "> Pazar kapalı</label><label><input name='pricesAreDraft' type='checkbox'" + (s.pricesAreDraft ? " checked" : "") + "> Fiyatlar hâlâ taslak</label><button class='solid' type='submit'>Kaydet</button></form>";
}
function drawUsers() {
  var rows = (panel.data.users || []).map(function (user) {
    return "<tr><td>" + esc(user.username) + "</td><td>" + esc(user.name) + "</td><td>" + esc(user.role) + "</td><td>" + (user.active ? "açık" : "kapalı") + "</td></tr>";
  }).join("");
  return "<h2>Kullanıcılar</h2><table><tr><th>Ad</th><th>İsim</th><th>Rol</th><th>Durum</th></tr>" + rows + "</table><h3>Yeni kullanıcı</h3><form id='new-user'><input name='username' placeholder='kullanici' required><input name='name' placeholder='İsim' required><select name='role'><option value='staff'>Personel, sadece sipariş</option><option value='admin'>Yönetici</option></select><input name='password' type='password' placeholder='Şifre, en az 8' required><button class='solid' type='submit'>Oluştur</button></form><h3>Şifremi değiştir</h3><form id='pass'><input name='current' type='password' placeholder='Mevcut' required><input name='next' type='password' placeholder='Yeni' required><button class='solid' type='submit'>Değiştir</button></form><p id='user-msg'></p>";
}
async function refresh() {
  try {
    var data = await api("/api/panel/state");
    var fresh = (data.orders || []).filter(function (order) { return order.status === "new"; }).length;
    if (panel.seen && fresh > panel.seen) document.title = "(" + fresh + ") Yeni sipariş";
    panel.seen = fresh;
    panel.user = data.user;
    panel.data = data;
    if (panel.tab === "orders" || !document.getElementById("view").innerHTML) showApp();
  } catch (err) {
    if (!panel.user) showLogin();
  }
}
document.getElementById("login-form").addEventListener("submit", async function (event) {
  event.preventDefault();
  var form = new FormData(event.target);
  try {
    await api("/api/login", { username: form.get("username"), password: form.get("password") });
    await refresh();
  } catch (err) { document.getElementById("login-error").textContent = err.message; }
});
document.getElementById("logout").addEventListener("click", async function () {
  await api("/api/logout", {});
  panel.user = null;
  showLogin();
});
document.getElementById("sound").addEventListener("click", function () {
  panel.sound = !panel.sound;
  document.getElementById("sound").textContent = panel.sound ? "Ses açık" : "Sesi aç";
});
document.querySelector(".side").addEventListener("click", function (event) {
  if (!event.target.dataset.tab) return;
  panel.tab = event.target.dataset.tab;
  showApp();
});
document.getElementById("view").addEventListener("click", async function (event) {
  var statusBtn = event.target.closest("[data-status]");
  if (statusBtn) {
    await api("/api/panel/order", { id: statusBtn.dataset.id, status: statusBtn.dataset.status });
    await refresh();
    return;
  }
  var saveBtn = event.target.closest("[data-save-item]");
  if (saveBtn) {
    var id = saveBtn.dataset.saveItem;
    var price = document.querySelector("[data-price='" + id + "']").value;
    var available = document.querySelector("[data-avail='" + id + "']").checked;
    await api("/api/panel/item", { id: id, price: Number(price), available: available });
    await refresh();
  }
});
document.getElementById("view").addEventListener("submit", async function (event) {
  event.preventDefault();
  var form = new FormData(event.target);
  try {
    if (event.target.id === "settings") {
      await api("/api/panel/settings", {
        announcement: form.get("announcement"), phone: form.get("phone"), mobile: form.get("mobile"),
        address: form.get("address"), openTime: form.get("openTime"), closeTime: form.get("closeTime"),
        deliveryZone: form.get("deliveryZone"), deliveryFee: Number(form.get("deliveryFee")),
        minDelivery: Number(form.get("minDelivery")), googleAdsId: form.get("googleAdsId"),
        conversionLabel: form.get("conversionLabel"), ga4Id: form.get("ga4Id"), siteUrl: form.get("siteUrl"),
        orderingOpen: form.get("orderingOpen") === "on", forceOpen: form.get("forceOpen") === "on",
        sundayClosed: form.get("sundayClosed") === "on", pricesAreDraft: form.get("pricesAreDraft") === "on"
      });
    }
    if (event.target.id === "new-item") {
      await api("/api/panel/item", { create: true, id: form.get("id"), name: form.get("name"), price: Number(form.get("price")), cat: form.get("cat") });
    }
    if (event.target.id === "new-user") {
      await api("/api/panel/user", { create: true, username: form.get("username"), name: form.get("name"), role: form.get("role"), password: form.get("password") });
    }
    if (event.target.id === "pass") {
      await api("/api/panel/password", { current: form.get("current"), next: form.get("next") });
      alert("Şifre değişti.");
    }
    await refresh();
  } catch (err) { alert(err.message); }
});
refresh();
setInterval(refresh, 4000);
