/* Lightbox helpers (moved from editor.js) */
function populateLightbox(imgs, startIndex = 0, preferSrc) {
  lightboxImages = imgs.slice();
  const thumbs = document.getElementById('lightbox-thumbs');
  const lbImg = document.getElementById('lightbox-img');
  if (!thumbs || !lbImg) return;
  thumbs.innerHTML = '';
  let idx = startIndex;
  if (preferSrc) {
    const found = lightboxImages.indexOf(preferSrc);
    if (found !== -1) idx = found;
  }
  lightboxImages.forEach((u, i) => {
    const t = document.createElement('img');
    const proxy = `/proxy_image?url=${encodeURIComponent(u)}`;
    t.src = proxy;
    t.setAttribute('data-src', u);
    t.onclick = (e) => { updateLightbox(i); };
    if (i === idx) t.classList.add('active');
    thumbs.appendChild(t);
  });
  updateLightbox(idx);
}

function updateLightbox(i) {
  if (!lightboxImages || lightboxImages.length === 0) return;
  if (i < 0) i = lightboxImages.length - 1;
  if (i >= lightboxImages.length) i = 0;
  lightboxIndex = i;
  const lbImg = document.getElementById('lightbox-img');
  const thumbs = document.getElementById('lightbox-thumbs');
  if (lbImg) lbImg.src = `/proxy_image?url=${encodeURIComponent(lightboxImages[lightboxIndex])}`;
  if (thumbs) {
    Array.from(thumbs.children).forEach((n, idx) => {
      if (idx === lightboxIndex) n.classList.add('active'); else n.classList.remove('active');
    });
    // ensure the active thumb is visible
    const active = thumbs.children[lightboxIndex];
    if (active && active.scrollIntoView) {
      try { active.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' }); } catch (e) { /* noop */ }
    }
  }
}

function lightboxPrev(e) { if (e && e.stopPropagation) e.stopPropagation(); updateLightbox(lightboxIndex - 1); }
function lightboxNext(e) { if (e && e.stopPropagation) e.stopPropagation(); updateLightbox(lightboxIndex + 1); }

async function saveFromLightbox() {
  if (!lightboxImages || !lightboxImages.length) return showToast('No image to save', 'error');
  const url = lightboxImages[lightboxIndex];
  try {
    const res = await fetch('/set_poster', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating_key: currentKey, url })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast('Poster set in Plex');
      document.getElementById('plex-img').src = `/plex_proxy/${currentKey}?t=${Date.now()}`;
      closeLightbox();
    } else {
      showToast('Failed to set poster: ' + (data.message || 'unknown'), 'error');
    }
  } catch (e) {
    console.error(e);
    showToast('Error setting poster', 'error');
  }
}

function closeLightbox(e) {
  if (e && e.stopPropagation) e.stopPropagation();
  const lb = document.getElementById('lightbox');
  const lbImg = document.getElementById('lightbox-img');
  if (lb) lb.classList.add('hidden');
  if (lbImg) lbImg.src = '';
}

// Initialize lightbox navigation (buttons + swipe) and attach handlers
(function initLightboxNavigation() {
  function attachHandlers() {
    const prevBtn = document.getElementById('lb-prev');
    const nextBtn = document.getElementById('lb-next');
    const lbView = document.querySelector('.lightbox-view');
    const thumbs = document.getElementById('lightbox-thumbs');

    if (prevBtn) {
      prevBtn.removeEventListener('click', lightboxPrev);
      prevBtn.addEventListener('click', (e) => { e.stopPropagation(); lightboxPrev(e); });
    }
    if (nextBtn) {
      nextBtn.removeEventListener('click', lightboxNext);
      nextBtn.addEventListener('click', (e) => { e.stopPropagation(); lightboxNext(e); });
    }

    // Swipe support on the main view
    if (lbView) {
      let touchStartX = null;
      const threshold = 40;
      lbView.addEventListener('touchstart', (e) => { if (e.changedTouches && e.changedTouches[0]) touchStartX = e.changedTouches[0].clientX; });
      lbView.addEventListener('touchend', (e) => {
        if (touchStartX === null) return;
        const touchEndX = e.changedTouches[0].clientX;
        const diff = touchEndX - touchStartX;
        if (diff > threshold) { lightboxPrev(); }
        else if (diff < -threshold) { lightboxNext(); }
        touchStartX = null;
      });
    }

    // Allow clicking a thumb (in case populateLightbox was not wired for some reason)
    if (thumbs) {
      thumbs.removeEventListener('click', thumbs._lb_click_handler);
      const handler = (e) => {
        const img = e.target.closest('img');
        if (!img) return;
        const nodes = Array.from(thumbs.children);
        const idx = nodes.indexOf(img);
        if (idx !== -1) updateLightbox(idx);
      };
      thumbs.addEventListener('click', handler);
      thumbs._lb_click_handler = handler;
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', attachHandlers);
  else attachHandlers();
})();
