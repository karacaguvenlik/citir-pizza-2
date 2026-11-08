const I18N = {
  tr: {
    hero: "Sıcak pizza,<br><em>kapına kadar.</em>",
    lead: "Çıtır Pizza ve Cafe menüsünden gel-al veya adrese teslim sipariş ver. Kapıda nakit veya kart.",
    call: "Ara", cart: "Sepet", empty: "Sepetin boş.", add: "Ekle", sold: "Tükendi",
    pickup: "Gel-al", delivery: "Adrese teslim", name: "Adın", phone: "Telefon",
    address: "Açık adres", pay: "Ödeme", cash: "Kapıda nakit", card: "Kapıda kart",
    note: "Sipariş notu", place: "Siparişi gönder", sub: "Ara toplam", fee: "Teslimat",
    total: "Toplam", min: "Adrese teslim minimum", zone: "Bölge", popular: "Çok istenen",
    flavor: "Tat", closed: "Şu an sipariş kapalı.", thanks: "Siparişin mutfağa düştü.",
    code: "Kodun", track: "Bu kodla durumunu sorabilirsin."
  },
  en: {
    hero: "Hot pizza,<br><em>to your door.</em>",
    lead: "Order from Çıtır Pizza and Cafe in Oba, Alanya. Pickup or delivery. Cash or card at the door.",
    call: "Call", cart: "Cart", empty: "Your cart is empty.", add: "Add", sold: "Sold out",
    pickup: "Pickup", delivery: "Delivery", name: "Name", phone: "Phone",
    address: "Address", pay: "Payment", cash: "Cash at door", card: "Card at door",
    note: "Order note", place: "Place order", sub: "Subtotal", fee: "Delivery",
    total: "Total", min: "Delivery minimum", zone: "Area", popular: "Popular",
    flavor: "Flavour", closed: "Ordering is closed right now.", thanks: "The kitchen has your order.",
    code: "Your code", track: "Use this code to check status."
  }
};
const state = { menu: null, lang: localStorage.getItem("citir-lang") || "tr", cart: loadCart(), fulfillment: "pickup", payment: "cash", busy: false, done: null };
function loadCart() { try { return JSON.parse(localStorage.getItem("citir-cart") || "[]"); } catch (e) { return []; } }
function saveCart() { localStorage.setItem("citir-cart", JSON.stringify(state.cart)); }
function t(key) { return I18N[state.lang][key]; }
function money(n) { return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY", maximumFractionDigits: 0 }).format(n); }
function itemById(id) { return state.menu.items.find(function (item) { return item.id === id; }); }
function nameOf(item) { return state.lang === "en" ? item.nameEn : item.name; }
function descOf(item) { return state.lang === "en" ? item.descEn : item.desc; }
function cartCount() { return state.cart.reduce(function (sum, line) { return sum + line.qty; }, 0); }
function cartMoney() {
  var sub = 0;
  state.cart.forEach(function (line) { var item = itemById(line.id); if (item) sub += item.price * line.qty; });
  var fee = state.fulfillment === "delivery" ? state.menu.settings.deliveryFee : 0;
  return { sub: sub, fee: fee, total: sub + fee };
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, function (ch) {
    return { "&": "&", "<": "<", ">": ">", '"': "&quot;", "'": "&#39;" }[ch];
  });
}
function card(item) {
  var flavor = "";
  if (item.options.length) {
    var opts = item.options.map(function (opt) { return "<option>" + escapeHtml(opt) + "</option>"; }).join("");
    flavor = "<label>" + t("flavor") + " <select data-flavor='" + item.id + "'>" + opts + "</select></label>";
  }
  var action = item.available ? "<button class='add' type='button' data-add='" + item.id + "'>" + t("add") + "</button>" : "<span class='sold'>" + t("sold") + "</span>";
  var popular = item.popular ? " <span class='popular'>" + t("popular") + "</span>" : "";
  return "<article class='card'><div><h3>" + escapeHtml(nameOf(item)) + popular + "</h3><p>" + escapeHtml(descOf(item)) + "</p>" + flavor + "</div><div><div class='price'>" + money(item.price) + "</div>" + action + "</div></article>";
}
function renderCart() {
  var box = document.getElementById("cart");
  var s = state.menu.settings;
  var totals = cartMoney();
  if (state.done) {
    box.innerHTML = "<div class='okbox'><strong>" + t("thanks") + "</strong><p>" + t("code") + ": " + state.done.code + "</p><p>" + t("total") + ": " + money(state.done.total) + "</p><p>" + t("track") + "</p></div>";
    return;
  }
  var lines = state.cart.map(function (line, index) {
    var item = itemById(line.id);
    if (!item) return "";
    var option = line.option ? "<div>" + escapeHtml(line.option) + "</div>" : "";
    return "<div class='line'><div><strong>" + line.qty + " x " + escapeHtml(nameOf(item)) + "</strong>" + option + "<div class='qty'><button type='button' data-dec='" + index + "'>-</button><span>" + line.qty + "</span><button type='button' data-inc='" + index + "'>+</button></div></div><div>" + money(item.price * line.qty) + "</div></div>";
  }).join("");
  var belowMin = state.fulfillment === "delivery" && totals.sub < s.minDelivery;
  var address = "";
  if (state.fulfillment === "delivery") {
    address = "<label>" + t("address") + "<textarea id='cust-address'></textarea></label><p class='note'>" + t("zone") + ": " + escapeHtml(s.deliveryZone) + ". " + t("min") + ": " + money(s.minDelivery) + "</p>";
  }
  var disabled = (!state.cart.length || s.closed || belowMin || state.busy) ? " disabled" : "";
  box.innerHTML = "<h2>" + t("cart") + "</h2>" + (lines || ("<p>" + t("empty") + "</p>")) +
    "<div class='seg'><button type='button' data-ful='pickup' class='" + (state.fulfillment === "pickup" ? "on" : "") + "'>" + t("pickup") + "</button><button type='button' data-ful='delivery' class='" + (state.fulfillment === "delivery" ? "on" : "") + "'>" + t("delivery") + "</button></div>" +
    "<label>" + t("name") + "<input id='cust-name' autocomplete='name'></label>" +
    "<label>" + t("phone") + "<input id='cust-phone' autocomplete='tel' inputmode='tel'></label>" + address +
    "<div class='seg'><button type='button' data-pay='cash' class='" + (state.payment === "cash" ? "on" : "") + "'>" + t("cash") + "</button><button type='button' data-pay='card' class='" + (state.payment === "card" ? "on" : "") + "'>" + t("card") + "</button></div>" +
    "<label>" + t("note") + "<textarea id='cust-note'></textarea></label>" +
    "<div class='totals'><div>" + t("sub") + " <strong>" + money(totals.sub) + "</strong></div><div>" + t("fee") + " <strong>" + money(totals.fee) + "</strong></div><div>" + t("total") + " <strong>" + money(totals.total) + "</strong></div></div>" +
    "<p class='error' id='form-error'></p><button class='solid' id='place' type='button'" + disabled + ">" + t("place") + "</button>";
}
function render() {
  var s = state.menu.settings;
  document.documentElement.lang = state.lang;
  document.getElementById("lang-tr").setAttribute("aria-pressed", String(state.lang === "tr"));
  document.getElementById("lang-en").setAttribute("aria-pressed", String(state.lang === "en"));
  document.getElementById("hero-title").innerHTML = t("hero");
  document.getElementById("hero-lead").textContent = t("lead");
  document.getElementById("call-link").textContent = t("call");
  document.getElementById("call-link").href = "tel:" + s.phoneTel;
  document.getElementById("topbar").textContent = s.announcement || (s.area + " · " + s.openTime + "-" + s.closeTime);
  document.getElementById("open-state").textContent = s.closed ? (s.closedReason || t("closed")) : (state.lang === "tr" ? "Sipariş açık." : "Ordering is open.");
  document.getElementById("chips").innerHTML = state.menu.categories.map(function (cat) {
    return "<a href='#cat-" + cat.id + "'>" + (state.lang === "en" ? cat.en : cat.tr) + "</a>";
  }).join("");
  document.getElementById("list").innerHTML = state.menu.categories.map(function (cat) {
    var rows = state.menu.items.filter(function (item) { return item.cat === cat.id; });
    if (!rows.length) return "";
    return "<section class='cat' id='cat-" + cat.id + "'><h2>" + (state.lang === "en" ? cat.en : cat.tr) + "</h2>" + rows.map(card).join("") + "</section>";
  }).join("");
  renderCart();
  var dock = document.getElementById("dock");
  dock.textContent = t("cart") + " · " + cartCount() + " · " + money(cartMoney().total);
  dock.hidden = cartCount() === 0;
}
document.addEventListener("click", function (event) {
  var add = event.target.closest("[data-add]");
  if (add && state.menu) {
    var item = itemById(add.dataset.add);
    var select = document.querySelector("[data-flavor='" + item.id + "']");
    var option = select ? select.value : "";
    var existing = state.cart.find(function (line) { return line.id === item.id && line.option === option; });
    if (existing) existing.qty += 1; else state.cart.push({ id: item.id, qty: 1, option: option });
    saveCart();
    if (window.citirTrack) window.citirTrack("add_to_cart", { currency: "TRY", value: item.price, items: [{ item_id: item.id, item_name: item.name, price: item.price, quantity: 1 }] });
    render();
    return;
  }
  var dec = event.target.closest("[data-dec]");
  var inc = event.target.closest("[data-inc]");
  if (dec || inc) {
    var index = Number((dec || inc).dataset.dec || (dec || inc).dataset.inc);
    state.cart[index].qty += inc ? 1 : -1;
    if (state.cart[index].qty < 1) state.cart.splice(index, 1);
    saveCart(); render(); return;
  }
  if (event.target.dataset.ful) { state.fulfillment = event.target.dataset.ful; renderCart(); return; }
  if (event.target.dataset.pay) { state.payment = event.target.dataset.pay; renderCart(); return; }
  if (event.target.id === "place") placeOrder();
  if (event.target.id === "lang-tr" || event.target.id === "lang-en") {
    state.lang = event.target.id === "lang-en" ? "en" : "tr";
    localStorage.setItem("citir-lang", state.lang);
    render();
  }
});
async function placeOrder() {
  state.busy = true;
  renderCart();
  if (window.citirTrack) window.citirTrack("begin_checkout", { currency: "TRY", value: cartMoney().total });
  var addressEl = document.getElementById("cust-address");
  var res = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Requested-With": "citir" },
    body: JSON.stringify({
      name: document.getElementById("cust-name").value,
      phone: document.getElementById("cust-phone").value,
      address: addressEl ? addressEl.value : "",
      note: document.getElementById("cust-note").value,
      fulfillment: state.fulfillment,
      payment: state.payment,
      items: state.cart
    })
  });
  var data = await res.json();
  state.busy = false;
  if (!res.ok) {
    renderCart();
    var err = document.getElementById("form-error");
    if (err) err.textContent = data.error || "Hata";
    return;
  }
  if (window.citirTrack) window.citirTrack("purchase", { transaction_id: data.order.code, value: data.order.total, currency: "TRY" });
  state.done = data.order;
  state.cart = [];
  saveCart();
  render();
}
document.getElementById("track-form").addEventListener("submit", async function (event) {
  event.preventDefault();
  var form = new FormData(event.target);
  var res = await fetch("/api/track?code=" + encodeURIComponent(form.get("code")) + "&phone=" + encodeURIComponent(form.get("phone")));
  var data = await res.json();
  document.getElementById("track-out").textContent = res.ok ? data.order.code + " · " + data.order.status + " · " + money(data.order.total) : data.error;
});
async function boot() {
  var res = await fetch("/api/menu");
  state.menu = await res.json();
  if (!localStorage.getItem("citir-consent")) document.getElementById("consent").hidden = false;
  document.getElementById("consent-yes").onclick = function () {
    localStorage.setItem("citir-consent", "yes");
    document.getElementById("consent").hidden = true;
    if (window.citirLoadAds) window.citirLoadAds(state.menu.settings);
  };
  if (window.citirLoadAds) window.citirLoadAds(state.menu.settings);
  render();
}
boot();
