/* ==================== Custom Undo/Redo Stack ==================== */
const undoStack = [];
const redoStack = [];
const MAX_UNDO = 50;
let undoCooldown = false;

function saveUndoState() {
  if (undoCooldown) return;
  undoStack.push(editor.innerHTML);
  if (undoStack.length > MAX_UNDO) undoStack.shift();
  redoStack.length = 0;
}

function undo() {
  if (undoStack.length === 0) return;
  redoStack.push(editor.innerHTML);
  const state = undoStack.pop();
  undoCooldown = true;
  editor.innerHTML = state;
  // Restore cursor
  const sel = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(editor);
  range.collapse(false);
  sel.removeAllRanges();
  sel.addRange(range);
  setTimeout(() => { undoCooldown = false; }, 50);
}

function redo() {
  if (redoStack.length === 0) return;
  undoStack.push(editor.innerHTML);
  const state = redoStack.pop();
  undoCooldown = true;
  editor.innerHTML = state;
  const sel = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(editor);
  range.collapse(false);
  sel.removeAllRanges();
  sel.addRange(range);
  setTimeout(() => { undoCooldown = false; }, 50);
}

/* ==================== DOM-based Inline Formatting ==================== */

function toggleInlineFormat(tagName) {
  if (!editor) return;

  const sel = window.getSelection();
  if (!sel.rangeCount || sel.isCollapsed) {
    // No selection — insert empty formatting toggles (like execCommand does)
    document.execCommand(tagName === 'STRONG' ? 'bold' :
                         tagName === 'EM' ? 'italic' :
                         tagName === 'U' ? 'underline' :
                         tagName === 'S' ? 'strikeThrough' : '', false, null);
    return;
  }

  saveUndoState();
  const range = sel.getRangeAt(0);

  // Check if selection is already wrapped in this tag
  let node = range.commonAncestorContainer;
  if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;

  let found = false;
  let check = node;
  while (check && check !== editor) {
    if (check.tagName === tagName) {
      found = true;
      break;
    }
    check = check.parentElement;
  }

  if (found) {
    // Unwrap: move children up and remove the wrapper
    const parent = check.parentElement;
    while (check.firstChild) {
      parent.insertBefore(check.firstChild, check);
    }
    parent.removeChild(check);
  } else {
    // Wrap selection in the tag
    const wrapper = document.createElement(tagName);
    try {
      range.surroundContents(wrapper);
    } catch (e) {
      // surroundContents fails if the range spans multiple elements
      // Fall back to execCommand
      const cmd = tagName === 'STRONG' ? 'bold' :
                  tagName === 'EM' ? 'italic' :
                  tagName === 'U' ? 'underline' : 'strikeThrough';
      document.execCommand(cmd, false, null);
    }
  }

  sel.removeAllRanges();
  sel.addRange(range);
}

/* ==================== Formatting Commands ==================== */
const formatting = {
  bold:   () => { toggleInlineFormat('STRONG'); notifyGTKInlineStyles(); },
  italic: () => { toggleInlineFormat('EM'); notifyGTKInlineStyles(); },
  underline: () => { toggleInlineFormat('U'); notifyGTKInlineStyles(); },
  strikethrough: () => { toggleInlineFormat('S'); notifyGTKInlineStyles(); },
  indent: () => { document.execCommand('indent'); },
  outdent: () => { document.execCommand('outdent'); },

  // ── Font size ─────────────────────────────────────────────────
  increaseFontSize: () => {
    saveUndoState();
    document.execCommand('fontSize', false, '5');  // bumps relative
  },
  decreaseFontSize: () => {
    saveUndoState();
    document.execCommand('fontSize', false, '1');  // decreases relative
  },

  // ── Text alignment ────────────────────────────────────────────
  alignLeft: () => { saveUndoState(); document.execCommand('justifyLeft'); },
  alignCenter: () => { saveUndoState(); document.execCommand('justifyCenter'); },
  alignRight: () => { saveUndoState(); document.execCommand('justifyRight'); },
  alignJustify: () => { saveUndoState(); document.execCommand('justifyFull'); },

  // ── Word count ────────────────────────────────────────────────
  wordCount: () => {
    const text = editor ? editor.innerText || '' : '';
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    return { words: words, chars: text.length };
  },

  highlight: () => {
    saveUndoState();
    const sel = window.getSelection();
    if (!sel.rangeCount || sel.isCollapsed) return;
    const range = sel.getRangeAt(0);

    // Check if selection already has yellow background
    let parent = range.commonAncestorContainer;
    if (parent.nodeType === Node.TEXT_NODE) parent = parent.parentElement;
    let isHighlighted = false;
    let hlNode = parent;
    while (hlNode && hlNode !== editor) {
      if (hlNode.style && hlNode.style.backgroundColor === 'yellow') {
        isHighlighted = true;
        break;
      }
      hlNode = hlNode.parentElement;
    }

    if (isHighlighted) {
      hlNode.style.backgroundColor = 'transparent';
    } else {
      const span = document.createElement('span');
      span.style.backgroundColor = 'yellow';
      try {
        range.surroundContents(span);
      } catch (e) {
        document.execCommand('backColor', false, 'yellow');
      }
    }
  },
  createLink: () => {
    const url = prompt('Enter link URL');
    if (!url) return;
    saveUndoState();
    const sel = window.getSelection();
    if (!sel.rangeCount || sel.isCollapsed) {
      // No selection, insert a named link
      const text = prompt('Enter link text:');
      if (!text) return;
      const a = document.createElement('a');
      a.href = url;
      a.textContent = text;
      a.target = '_blank';
      const range = sel.getRangeAt(0);
      range.insertNode(a);
      range.setStartAfter(a);
      range.collapse(true);
      sel.removeAllRanges();
      sel.addRange(range);
    } else {
      const range = sel.getRangeAt(0);
      const a = document.createElement('a');
      a.href = url;
      a.target = '_blank';
      try {
        range.surroundContents(a);
      } catch (e) {
        document.execCommand('createLink', false, url);
      }
    }
  }
};

/* ==================== Undo/Redo exposed for GTK ==================== */
/* main.py calls: document.execCommand('undo') and document.execCommand('redo') */
/* We override those by mapping undo/redo actions in main.py to window.undo()/window.redo() */

/* ==================== Dynamic CSS Loader ==================== */
function loadCSS(filename) {
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = filename;
  document.head.appendChild(link);
}

/* ==================== Editor Reference ==================== */
const editor = document.querySelector('[contenteditable="true"]');

/* ==================== Apply Styles (DOM-based) ==================== */
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

  saveUndoState();

  // DOM-based formatBlock replacement
  const newBlock = document.createElement(style);
  while (block.firstChild) {
    newBlock.appendChild(block.firstChild);
  }
  block.parentNode.replaceChild(newBlock, block);

  // Place cursor inside the new block
  const sel = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(newBlock);
  range.collapse(false);
  sel.removeAllRanges();
  sel.addRange(range);

  notifyGTKStyleChange();
}


function isBlockElement(elem) {
  const blockTags = ['P','H1','H2','H3','H4','H5','H6','PRE','BLOCKQUOTE','DIV'];
  return blockTags.includes(elem.tagName);
}

/* ==================== Report Current Style to GTK ==================== */
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
    strikeout: false,
    list: false
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

/* ==================== Notify GTK ==================== */
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

/* ==================== Markdown Shortcuts ==================== */

function makeLink(text, url) {
  const a = document.createElement('a');
  a.href = url;
  a.textContent = text;
  a.target = '_blank';
  return a;
}

function handleInlineMarkdown() {
  const sel = window.getSelection();
  if (!sel.rangeCount) return;
  const range = sel.getRangeAt(0);
  const node = range.startContainer;
  if (node.nodeType !== Node.TEXT_NODE || !node.textContent) return;

  const text = node.textContent;
  const pos = range.startOffset;

  const beforeCursor = text.substring(0, pos);
  const trimmed = beforeCursor.replace(/ $/, '');

  const inlinePatterns = [
    { regex: /\[([^\]]+)\]\(([^)]+)\)$/g, handler: makeLink },
    { regex: /\*\*(.+?)\*\*$/g,   tag: 'strong' },
    { regex: /__(.+?)__$/g,         tag: 'strong' },
    { regex: /\*(.+?)\*$/g,        tag: 'em' },
    { regex: /_(.+?)_$/g,           tag: 'em' },
    { regex: /~~(.+?)~~$/g,         tag: 's' },
    { regex: /`(.+?)`$/g,           tag: 'code' },
  ];

  for (const pattern of inlinePatterns) {
    const match = trimmed.match(pattern.regex);
    if (!match) continue;

    const fullMatch = match[0];
    const innerText = match[1];

    let parent = node.parentElement;
    while (parent && parent !== editor) {
      const tag = parent.tagName.toLowerCase();
      if (tag === 'code' || tag === 'a' || tag === 'pre') return;
      parent = parent.parentElement;
    }

    saveUndoState();

    const before = text.substring(0, pos - fullMatch.length - 1);
    const after = text.substring(pos);

    let replacementNode;
    if (pattern.handler) {
      const url = match[2];
      replacementNode = pattern.handler(innerText, url);
    } else {
      const wrapper = document.createElement(pattern.tag);
      wrapper.textContent = innerText;
      replacementNode = wrapper;
    }

    const space = document.createTextNode(' ');

    node.textContent = before;
    node.parentNode.insertBefore(replacementNode, node.nextSibling);
    node.parentNode.insertBefore(space, node.nextSibling);

    const newRange = document.createRange();
    newRange.setStartAfter(space);
    newRange.collapse(true);
    sel.removeAllRanges();
    sel.addRange(newRange);

    notifyGTKInlineStyles();
    return;
  }
}

function handleBlockMarkdown() {
  const sel = window.getSelection();
  if (!sel.rangeCount) return;

  let node = sel.anchorNode;
  if (!node) return;

  if (node.nodeType === Node.TEXT_NODE) {
    node = node.parentNode;
  }

  let block = node;
  while (block && block !== editor && !isBlockElement(block)) {
    block = block.parentNode;
  }
  if (!block || block === editor) return;

  const text = block.textContent || '';

  const headingMatch = text.match(/^(#{1,6})\s+(.+)/);
  if (headingMatch) {
    const level = headingMatch[1].length;
    const content = headingMatch[2];
    saveUndoState();
    const newBlock = document.createElement(`h${level}`);
    newBlock.textContent = content;
    block.parentNode.replaceChild(newBlock, block);
    placeCursorAtEnd(newBlock);
    notifyGTKStyleChange();
    return;
  }

  if (/^>\s+(.+)/.test(text)) {
    const content = text.replace(/^>\s+/, '');
    saveUndoState();
    const newBlock = document.createElement('blockquote');
    newBlock.textContent = content;
    block.parentNode.replaceChild(newBlock, block);
    placeCursorAtEnd(newBlock);
    notifyGTKStyleChange();
    return;
  }

  if (/^[-*]\s+(.+)/.test(text)) {
    block.innerHTML = text.replace(/^[-*]\s+/, '');
    document.execCommand('insertUnorderedList');
    notifyGTKStyleChange();
    return;
  }

  if (/^\d+\.\s+(.+)/.test(text)) {
    block.innerHTML = text.replace(/^\d+\.\s+/, '');
    document.execCommand('insertOrderedList');
    notifyGTKStyleChange();
    return;
  }
}

function placeCursorAtEnd(el) {
  const sel = window.getSelection();
  const range = document.createRange();
  if (el.childNodes.length) {
    range.setStartAfter(el.lastChild);
  } else {
    range.selectNodeContents(el);
  }
  range.collapse(false);
  sel.removeAllRanges();
  sel.addRange(range);
}

/* ==================== Track Cursor Movement ==================== */
editor.addEventListener('keyup', (e) => {
  if (e.key === ' ') {
    handleInlineMarkdown();
  }
  if (e.key === 'Enter') {
    handleBlockMarkdown();
  }
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

/* ==================== Image Handling ==================== */
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

      const img = document.createElement('img');
      img.src = base64Data;
      img.dataset.imgId = imgId;

      saveUndoState();

      const sel = window.getSelection();
      if (sel.rangeCount) {
        const range = sel.getRangeAt(0);
        range.deleteContents();
        range.insertNode(img);
        range.setStartAfter(img);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
      } else {
        editor.appendChild(img);
      }

      setTimeout(() => {
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

function bootstrapExistingImages() {
  editor.querySelectorAll('img').forEach(resizeImageIfTooTall);
}

bootstrapExistingImages();

/* ==================== Page Printing ====================*/
function printPage() {
  if (!editor) {
    window.print();
    return;
  }

  editor.setAttribute('contenteditable', 'false');

  window.print();

  setTimeout(() => {
    editor.setAttribute('contenteditable', 'true');
  }, 500);
}

function insertTable(rows, cols) {
    saveUndoState();
    rows = rows || 3; cols = cols || 3;
    let html = '<table style="border-collapse:collapse;width:100%">';
    for (let r = 0; r < rows; r++) {
      html += '<tr>';
      for (let c = 0; c < cols; c++) {
        html += '<td style="border:1px solid #ccc;padding:4px 8px">&nbsp;</td>';
      }
      html += '</tr>';
    }
    html += '</table><p>&nbsp;</p>';
    document.execCommand('insertHTML', false, html);
  }

  // ── Find & Replace ────────────────────────────────────────────
  function findText(query) {
    if (!editor || !query) return { found: 0 };
    // Clear previous highlights
    const marks = editor.querySelectorAll('mark.search-highlight');
    marks.forEach(m => { const parent = m.parentNode; parent.replaceChild(document.createTextNode(m.textContent), m); });
    if (!query.trim()) return { found: 0 };
    // Highlight matches
    const regex = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
    let count = 0;
    const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (node.parentElement && node.parentElement.closest('mark')) continue;
      const text = node.textContent;
      const match = text.match(regex);
      if (match) {
        count += match.length;
        const span = document.createElement('mark');
        span.className = 'search-highlight';
        span.style.backgroundColor = '#ffeb3b';
        span.textContent = text;
        node.parentNode.replaceChild(span, node);
      }
    }
    return { found: count };
  }

  function replaceText(query, replacement, replaceAll) {
    if (!editor || !query) return { count: 0 };
    saveUndoState();
    let count = 0;
    const regex = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), replaceAll ? 'gi' : 'i');
    editor.innerHTML = editor.innerHTML.replace(regex, () => { count++; return replacement || ''; });
    // Reselect editor
    editor.focus();
    return { count: count };
  }
