/* LibraryGIS — map.js  |  Leaflet utilities */
const DARK_TILE = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const TILE_ATTR = '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a>';

function initMap(id, lat=10.8231, lng=106.6297, zoom=12) {
  const map = L.map(id, { center: [lat, lng], zoom, zoomControl: true });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; CARTO', maxZoom: 19,
  }).addTo(map);
  return map;
}

function branchIcon() {
  return L.divIcon({
    html: `<div style="width:36px;height:36px;background:linear-gradient(135deg,#1e6fbf,#155a9e);border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:3px solid #fff;box-shadow:0 3px 10px rgba(30,111,191,.5);display:flex;align-items:center;justify-content:center"><span style="transform:rotate(45deg);font-size:14px">📚</span></div>`,
    className: '', iconSize: [36,36], iconAnchor: [18,36], popupAnchor: [0,-38],
  });
}

function addBranchMarkers(map, geojson) {
  const markers = [];
  geojson.features.forEach(f => {
    const [lng, lat] = f.geometry.coordinates;
    const p = f.properties;
    const m = L.marker([lat, lng], { icon: branchIcon() })
      .bindPopup(`<div style="min-width:200px">
        <div class="popup-title">📚 ${p.name}</div>
        <div class="popup-row"><i class="ph ph-map-pin"></i> ${p.address}</div>
        <div class="popup-row"><i class="ph ph-phone"></i> ${p.phone || 'Chưa cập nhật'}</div>
        <div class="popup-row"><i class="ph ph-clock"></i> ${p.hours}</div>
        <div class="popup-row"><i class="ph ph-books"></i> <strong>${p.book_count}</strong> đầu sách</div>
        ${p.url ? `<a href="${p.url}" class="popup-link">Xem chi tiết →</a>` : ''}
      </div>`, { maxWidth: 280 })
      .addTo(map);
    markers.push(m);
  });
  return markers;
}

function fitMarkers(map, markers) {
  if (!markers.length) return;
  map.fitBounds(L.featureGroup(markers).getBounds().pad(0.2));
}

function addReaderLayer(map, geojson) {
  const pts = [];
  geojson.features.forEach(f => {
    const [lng, lat] = f.geometry.coordinates;
    const p = f.properties;
    pts.push([lat, lng, 1]);
    const color = p.status === 'active' ? '#16a34a' : p.status === 'suspended' ? '#dc2626' : '#94a3b8';
    L.circleMarker([lat, lng], { radius: 7, color, fillColor: color, fillOpacity: .7, weight: 2 })
      .bindPopup(`<div class="popup-title">👤 ${p.name}</div><div class="popup-row">🪪 ${p.card}</div><div class="popup-row">📍 ${p.district || 'N/A'}</div>`)
      .addTo(map);
  });
  if (pts.length && L.heatLayer)
    L.heatLayer(pts, { radius: 30, blur: 20, gradient: { .4:'#3b82f6', .65:'#1e6fbf', 1:'#1e40af' } }).addTo(map);
}

function findNearestBranch(map, onResults) {
  if (!navigator.geolocation) { alert('Trình duyệt không hỗ trợ GPS.'); return; }
  navigator.geolocation.getCurrentPosition(pos => {
    const { latitude: lat, longitude: lng } = pos.coords;
    const userIcon = L.divIcon({
      html: `<div style="width:14px;height:14px;background:#1e6fbf;border-radius:50%;border:3px solid #fff;box-shadow:0 0 0 5px rgba(30,111,191,.25)"></div>`,
      className: '', iconSize: [14,14], iconAnchor: [7,7],
    });
    L.marker([lat, lng], { icon: userIcon }).bindPopup('<div class="popup-title">📌 Vị trí của bạn</div>').addTo(map).openPopup();
    map.setView([lat, lng], 13, { animate: true });
    fetch(`/api/branches/nearest/?lat=${lat}&lng=${lng}`)
      .then(r => r.json())
      .then(d => onResults && onResults(d.branches || []))
      .catch(() => alert('Không thể lấy danh sách chi nhánh.'));
  }, () => alert('Không thể lấy vị trí. Hãy cho phép truy cập GPS.'));
}
