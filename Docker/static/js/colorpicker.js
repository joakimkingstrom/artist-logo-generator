/* Color picker and image swatches (moved from editor.js) */
const colors = [
    "#FFFFFF", "#9E9E9E", "#18FFFF", "#64FFDA", "#FFD740", 
    "#FFAB40", "#FF6E40", "#B2FF59", "#EEFF41", "#2979FF", 
    "#D500F9", "#F50057" 
];

function initColorPicker() {
  const grid = document.getElementById("color-picker");
  if (!grid) return;
  grid.innerHTML = "";
  colors.forEach((c) => {
    const s = document.createElement("div");
    s.className = "color-swatch";
    s.style.backgroundColor = c;
    if (c === selectedColor) s.classList.add("active");
    s.onclick = () => {
      selectedColor = c;
      grid
        .querySelectorAll(".color-swatch")
        .forEach((el) => el.classList.remove("active"));
      s.classList.add("active");
      previewCustom();
    };
    grid.appendChild(s);
  });
}

function initImageColorPicker() {
  const grid = document.getElementById("image-color-picker");
  if (!grid) return;
  grid.innerHTML = "";
  // Add colour swatches; clicking toggles selection (only one active at a time)
  colors.forEach((c) => {
    const s = document.createElement("div");
    s.className = "color-swatch";
    s.style.backgroundColor = c;
    if (c === selectedImageColor) s.classList.add("active");
    s.onclick = () => {
      const wasActive = s.classList.contains('active');
      grid.querySelectorAll('.color-swatch').forEach(el => el.classList.remove('active'));
      if (wasActive) {
        // toggle off
        selectedImageColor = null;
        if (document.getElementById('preview-overlay')) document.getElementById('preview-overlay').style.opacity = '0';
      } else {
        // activate this swatch
        s.classList.add('active');
        selectedImageColor = c;
      }
      // always keep preview canvas black
      const previewContainer = document.getElementById('preview-container');
      if (previewContainer) previewContainer.style.background = '#000000';
      updateCSS();
    };
    grid.appendChild(s);
  });
}
