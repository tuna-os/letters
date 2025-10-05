/* -------------------- Formatting Commands -------------------- */
const formatting = {
  bold:   () => document.execCommand('bold'),
  italic: () => document.execCommand('italic'),
  underline: () => document.execCommand('underline'),
  strikethrough: () => document.execCommand('strikeThrough'),
  indent: () => document.execCommand('indent'),
  outdent: () => document.execCommand('outdent'),
  highlight: () => {
    const isHighlighted = document.queryCommandValue('backColor') === 'rgb(255, 255, 0)' || document.queryCommandValue('backColor') === '#ffff00';

    if (isHighlighted) {
      document.execCommand('backColor', false, 'transparent');
    } else {
      const color = 'yellow';
      document.execCommand('backColor', false, color);
    }
  },
  createLink: () => {
    const url = prompt('Enter link URL');
    if (url) document.execCommand('createLink', false, url);
  }
};

/* -------------------- Dynamic CSS Loader -------------------- */
function loadCSS(filename) {
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = filename;
  document.head.appendChild(link);
}

/* -------------------- Editor Reference -------------------- */
const editor = document.querySelector('[contenteditable="true"]');

/* -------------------- Apply Styles -------------------- */
function applyStyle(style) {
  if (!editor) return;

  const selection = window.getSelection();
  if (!selection.rangeCount) return;

  let node = selection.anchorNode;
  if (!node) return;

  if (node.nodeType === Node.TEXT_NODE) {
    node = node.parentNode;
  }

  let block = node;
  while (block && block !== editor && !isBlockElement(block)) {
    block = block.parentNode;
  }

  if (!block || block === editor) return;

  if (block.tagName.toLowerCase() === style.toLowerCase()) {
    return;
  }

  /* We are completely fucked when WebKit removes support for document.execCommand :D */
  /* DOM manipulation doesn't affect the undo stack*/
  /* Maybe a custom undo redo stack can be made. Will be bad for memory though.*/
  document.execCommand('formatBlock', false, style);

  notifyGTKStyleChange();
}


function isBlockElement(elem) {
  const blockTags = ['P','H1','H2','H3','H4','H5','H6','PRE','BLOCKQUOTE','DIV'];
  return blockTags.includes(elem.tagName);
}

/* -------------------- Report Current Style to GTK -------------------- */
function getCurrentStyle() {
  const selection = window.getSelection();
  if (!selection.rangeCount) return null;

  let node = selection.anchorNode;
  if (!node) return null;

  while (node && (node.nodeType !== Node.ELEMENT_NODE || !isBlockElement(node))) {
    node = node.parentNode;
  }
  if (!node || node.nodeType !== Node.ELEMENT_NODE) return null;

  return node.tagName.toLowerCase();
}

function getInlineStyles() {
  const selection = window.getSelection();
  if (!selection.rangeCount) return null;

  let node = selection.anchorNode;
  if (!node) return null;

  if (node.nodeType === Node.TEXT_NODE) {
    node = node.parentNode;
  }

  const styles = {
    italic: false,
    bold: false,
    underline: false,
    strikeout: false, // New property
    list: false
    // Highlight state is omitted due to the complexity of tracking style="background-color:..."
  };

  while (node && node !== editor) {
    const tag = node.tagName ? node.tagName.toLowerCase() : '';

    if (!styles.italic && (tag === 'i' || tag === 'em')) {
      styles.italic = true;
    }

    if (!styles.bold && (tag === 'b' || tag === 'strong')) {
      styles.bold = true;
    }

    if (!styles.underline && tag === 'u') {
      styles.underline = true;
    }

    // Check for strikeout tags (<s> or <del>)
    if (!styles.strikeout && (tag === 's' || tag === 'del')) {
      styles.strikeout = true;
    }

    if (!styles.list && (tag === 'ul' || tag === 'ol')) {
      styles.list = true;
    }

    node = node.parentNode;
  }

  return styles;
}
/* -------------------- Notify GTK -------------------- */
function notifyGTKStyleChange() {
  const style = getCurrentStyle();
  if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.styleChange) {
    window.webkit.messageHandlers.styleChange.postMessage(style);
  } else if (window.external && window.external.invoke) {
    window.external.invoke(JSON.stringify({type: 'styleChange', style}));
  }
}

function notifyGTKInlineStyles() {
  const styles = getInlineStyles();
  if (!styles) return;

  if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.inlineStyleChange) {
    window.webkit.messageHandlers.inlineStyleChange.postMessage(styles);
  } else if (window.external && window.external.invoke) {
    window.external.invoke(JSON.stringify({ type: 'inlineStyleChange', styles }));
  }
}

function applyStyleFromGTK(style) {
  applyStyle(style);
  notifyGTKStyleChange();
}

(function setupContentObserver() {
  if (!(window.webkit && window.webkit.messageHandlers)) return;

  let timeout;
  const observer = new MutationObserver(() => {
    // debounce so we don’t spam GTK while typing
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      if (window.webkit.messageHandlers.contentChanged) {
        window.webkit.messageHandlers.contentChanged.postMessage({});
      }
    }, 10);
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true
  });
})();

/* -------------------- Track Cursor Movement -------------------- */
editor.addEventListener('keyup', () => {
  notifyGTKStyleChange();
  notifyGTKInlineStyles();
});

editor.addEventListener('click', () => {
  notifyGTKStyleChange();
  notifyGTKInlineStyles();
});

editor.addEventListener('mouseup', () => {
  notifyGTKStyleChange();
  notifyGTKInlineStyles();
});

editor.addEventListener('focus', () => {
  notifyGTKStyleChange();
  notifyGTKInlineStyles();
});

/* -------------------- Image Handling -------------------- */
function insertImage() {
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'image/*';
  fileInput.style.display = 'none';

  fileInput.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64Data = event.target.result;
      const imgId = 'img-' + Date.now() + '-' + Math.floor(Math.random() * 1000);

      const imgHTML = `<img src="${base64Data}" data-img-id="${imgId}">`;
      document.execCommand('insertHTML', false, imgHTML);

      setTimeout(() => {
        const img = document.querySelector(`img[data-img-id="${imgId}"]`);
        if (!img) return;

        resizeImageIfTooTall(img);
      }, 0);
    };
    reader.readAsDataURL(file);
  };

  document.body.appendChild(fileInput);
  fileInput.click();
}

function resizeImageIfTooTall(img) {
  const maxHeight = window.innerHeight * 0.5;

  if (!img.complete) {
    img.onload = () => resizeImageIfTooTall(img);
    return;
  }

  if (img.naturalHeight > maxHeight) {
    const scale = maxHeight / img.naturalHeight;
    img.style.height = maxHeight + 'px';
    img.style.width = img.naturalWidth * scale + 'px';
  }
}

function resizeImg(img) {
  if (!img || img.tagName !== 'IMG') {
    alert("No image found.");
    return;
  }

  const input = prompt("Enter new height in pixels:");
  if (!input) return;

  const newHeight = parseInt(input);
  if (isNaN(newHeight) || newHeight <= 0) {
    alert("Invalid height.");
    return;
  }

  const scale = newHeight / img.naturalHeight;
  img.style.height = newHeight + "px";
  img.style.width = img.naturalWidth * scale + "px";
}

/* -------------------- Bootstrap Existing Images -------------------- */
function bootstrapExistingImages() {
  editor.querySelectorAll('img').forEach(resizeImageIfTooTall);
}

bootstrapExistingImages();

/* -------------------- Page Printing --------------------*/
function printPage() {
  if (!editor) {
    window.print();
    return;
  }

  // 1. Disable editing to hide the caret and focus styles
  editor.setAttribute('contenteditable', 'false');

  // 2. Trigger the print dialog
  window.print();

  // 3. Use a timeout to wait a very short period, then re-enable editing
  // This allows the browser time to queue the print job before changing the DOM.
  setTimeout(() => {
    editor.setAttribute('contenteditable', 'true');
  }, 500); // 500ms should be safe
}
