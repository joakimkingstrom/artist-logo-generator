/* Preview/mask logic (moved from editor.js) */
function updateCSS() {
  const img = document.getElementById("preview-img");
  const z = document.getElementById("zoom").value;
  const c = document.getElementById("contrast").value;

  const inv = document.getElementById("btn-invert").classList.contains("active")
    ? "invert(1)"
    : "";
  const mono = document.getElementById("btn-monochrome").classList.contains("active")
    ? "grayscale(1)"
    : "";
  img.style.transform = `scale(${z})`;

  // Special-case white swatch: make the logo itself white using filters
  const overlay = document.getElementById('preview-overlay');
  const previewContainer = document.getElementById('preview-container');
  const sel = (selectedImageColor || '').toLowerCase();

  if (sel === '#ffffff' || sel === 'rgb(255, 255, 255)') {
    img.style.filter = 'brightness(0) saturate(100%) invert(1)';
    img.style.mixBlendMode = 'normal';
    if (overlay) {
      overlay.style.opacity = '0';
      overlay.style.webkitMaskImage = '';
      overlay.style.maskImage = '';
    }
    if (previewContainer) previewContainer.style.background = '#000000';
  } else if (!sel) {
    img.style.mixBlendMode = 'normal';
    img.style.filter = `contrast(${c}) ${inv} ${mono}`;
    if (overlay) {
      overlay.style.opacity = '0';
      overlay.style.webkitMaskImage = '';
      overlay.style.maskImage = '';
    }
    if (previewContainer) previewContainer.style.background = '#000000';
  } else {
    img.style.mixBlendMode = 'normal';
    img.style.filter = `contrast(${c}) ${inv} ${mono}`;
    if (overlay) {
      overlay.style.backgroundColor = selectedImageColor || '#000000';
      const applyMask = () => {
        try {
          const quoted = 'url("' + (img.src || '') + '")';
          overlay.style.webkitMaskImage = quoted;
          overlay.style.maskImage = quoted;
          overlay.style.webkitMaskRepeat = 'no-repeat';
          overlay.style.maskRepeat = 'no-repeat';

          const containerRect = previewContainer.getBoundingClientRect();
          const imgRect = img.getBoundingClientRect();
          const offsetX = Math.max(0, imgRect.left - containerRect.left);
          const offsetY = Math.max(0, imgRect.top - containerRect.top);
          const widthPx = Math.max(0, imgRect.width);
          const heightPx = Math.max(0, imgRect.height);

          overlay.style.webkitMaskSize = `${widthPx}px ${heightPx}px`;
          overlay.style.maskSize = `${widthPx}px ${heightPx}px`;
          overlay.style.webkitMaskPosition = `${offsetX}px ${offsetY}px`;
          overlay.style.maskPosition = `${offsetX}px ${offsetY}px`;

          overlay.style.mixBlendMode = 'normal';
          overlay.style.opacity = '0.9';
        } catch (e) {
          overlay.style.webkitMaskImage = '';
          overlay.style.maskImage = '';
          overlay.style.mixBlendMode = 'screen';
          overlay.style.opacity = '0.6';
        }
        if (previewContainer) previewContainer.style.background = '#000000';
      };

      if (img && img.src && img.complete) {
        applyMask();
      } else if (img) {
        img.addEventListener('load', applyMask, { once: true });
      } else {
        overlay.style.webkitMaskImage = '';
        overlay.style.maskImage = '';
        overlay.style.mixBlendMode = 'screen';
        overlay.style.opacity = '0.6';
      }
    }
  }
}

function resetFilters() {
  document.getElementById("zoom").value = 1.0;
  document.getElementById("contrast").value = 1.0;
  document.getElementById('btn-invert').classList.remove('active');
  document.getElementById('btn-monochrome').classList.remove('active');
  
  const applyDefaultSizeCheckbox = document.getElementById("apply-default-size");
  applyDefaultSizeCheckbox.checked = true;
  toggleZoom(applyDefaultSizeCheckbox);

  // reset image color to default (no tint)
  selectedImageColor = null;
  const imgGrid = document.getElementById('image-color-picker');
  if (imgGrid) imgGrid.querySelectorAll('.color-swatch').forEach(el => el.classList.remove('active'));
  if (imgGrid) imgGrid.querySelectorAll('.color-swatch').forEach(el => el.classList.remove('active'));
  const overlay = document.getElementById('preview-overlay');
  if (overlay) overlay.style.opacity = '0';
  updateCSS();
}

function handleUpload(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = (e) => {
      selectedUrl = e.target.result;
      document.getElementById("preview-img").src = selectedUrl;
      resetFilters();
    };
    reader.readAsDataURL(input.files[0]);
  }
}
