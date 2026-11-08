window.citirLoadAds = function (settings) {
  if (!settings || !settings.adsConfigured) return;
  if (localStorage.getItem("citir-consent") !== "yes" || window.__ads) return;
  window.__ads = true;
  window.dataLayer = window.dataLayer || [];
  function g(){ window.dataLayer.push(arguments); }
  window.gtag = g;
  g("js", new Date());
  if (settings.ga4Id) g("config", settings.ga4Id);
  if (settings.googleAdsId) g("config", settings.googleAdsId);
  var el = document.createElement("script");
  el.async = true;
  el.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(settings.ga4Id || settings.googleAdsId);
  document.head.appendChild(el);
};
window.citirTrack = function (event, params) {
  if (localStorage.getItem("citir-consent") !== "yes" || !window.gtag) return;
  window.gtag("event", event, params || {});
};
