// ── Nagarawa Main JS ──

// Vote handler
function handleVote(complaintId, value) {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
    || getCookie('csrftoken');

  fetch(`/complaints/${complaintId}/vote/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-CSRFToken': csrfToken,
    },
    body: `value=${value}`,
  })
  .then(r => r.json())
  .then(data => {
    const card = document.querySelector(`[data-complaint="${complaintId}"]`);
    if (!card) return;

    const scoreEl = card.querySelector('.vote-score');
    const upBtn = card.querySelector('.vote-up');
    const downBtn = card.querySelector('.vote-down');

    if (scoreEl) scoreEl.textContent = data.score;

    upBtn?.classList.remove('active-up');
    downBtn?.classList.remove('active-down');

    if (data.user_vote === 1) upBtn?.classList.add('active-up');
    if (data.user_vote === -1) downBtn?.classList.add('active-down');
  })
  .catch(err => console.error('Vote error:', err));
}

function getCookie(name) {
  let v = null;
  document.cookie.split(';').forEach(c => {
    const [k, val] = c.trim().split('=');
    if (k === name) v = decodeURIComponent(val);
  });
  return v;
}

// Reply toggle
function toggleReply(commentId) {
  const form = document.getElementById(`reply-form-${commentId}`);
  if (form) form.classList.toggle('open');
}

// Auto-dismiss messages
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.message').forEach(el => {
    setTimeout(() => el.remove(), 5000);
  });
});

// ── Location Map Picker (complaint create form) ──
let pickerMap = null;
let pickerMarker = null;

function initLocationPicker() {
  const mapEl = document.getElementById('pick-map');
  if (!mapEl || typeof L === 'undefined') return;

  // Default center: Kathmandu
  pickerMap = L.map('pick-map').setView([27.7172, 85.3240], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(pickerMap);

  // Try browser geolocation
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(pos => {
      pickerMap.setView([pos.coords.latitude, pos.coords.longitude], 15);
    }, () => {});
  }

  pickerMap.on('click', function(e) {
    const { lat, lng } = e.latlng;
    if (pickerMarker) pickerMarker.remove();
    pickerMarker = L.marker([lat, lng]).addTo(pickerMap);

    document.getElementById('id_latitude').value = lat.toFixed(6);
    document.getElementById('id_longitude').value = lng.toFixed(6);

    // Reverse geocode with Nominatim
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
      .then(r => r.json())
      .then(data => {
        const locInput = document.getElementById('id_location_name');
        if (locInput && !locInput.value && data.display_name) {
          locInput.value = data.display_name.split(',').slice(0, 3).join(',').trim();
        }
      })
      .catch(() => {});
  });

  // If values already set (edit mode), place marker
  const lat = parseFloat(document.getElementById('id_latitude')?.value);
  const lng = parseFloat(document.getElementById('id_longitude')?.value);
  if (!isNaN(lat) && !isNaN(lng)) {
    pickerMarker = L.marker([lat, lng]).addTo(pickerMap);
    pickerMap.setView([lat, lng], 15);
  }
}

// ── Detail view map ──
function initDetailMap(lat, lng, locationName) {
  const mapEl = document.getElementById('complaint-map');
  if (!mapEl || typeof L === 'undefined') return;

  const map = L.map('complaint-map').setView([lat, lng], 15);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map);

  L.marker([lat, lng])
    .addTo(map)
    .bindPopup(locationName || 'Complaint location')
    .openPopup();
}

document.addEventListener('DOMContentLoaded', () => {
  initLocationPicker();
});
