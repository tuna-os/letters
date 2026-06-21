/**
 * Tests for Markdown shortcut patterns used in editor.js
 * Tests the regex matching logic without requiring a DOM.
 */
const assert = require('assert').strict;

// ---- Inline Patterns (replicated from editor.js handleInlineMarkdown) ----

const inlinePatterns = [
  { name: 'link',          regex: /\[([^\]]+)\]\(([^)]+)\)$/ },
  { name: 'bold',          regex: /\*\*(.+?)\*\*$/ },
  { name: 'bold-underscore', regex: /__(.+?)__$/ },
  { name: 'italic',        regex: /\*(.+?)\*$/ },
  { name: 'italic-underscore', regex: /_(.+?)_$/ },
  { name: 'strikethrough', regex: /~~(.+?)~~$/ },
  { name: 'code',          regex: /`(.+?)`$/ },
];

function testInlinePattern(text) {
  const trimmed = text.replace(/ $/, '');
  for (const pattern of inlinePatterns) {
    const match = trimmed.match(pattern.regex);
    if (match) {
      return { name: pattern.name, inner: match[1], full: match[0], extra: match[2] };
    }
  }
  return null;
}

// ---- Block Patterns (replicated from editor.js handleBlockMarkdown) ----

function testBlockPattern(text) {
  const headingMatch = text.match(/^(#{1,6})\s+(.+)/);
  if (headingMatch) {
    return { type: 'heading', level: headingMatch[1].length, content: headingMatch[2] };
  }

  if (/^>\s+(.+)/.test(text)) {
    return { type: 'blockquote', content: text.replace(/^>\s+/, '') };
  }

  if (/^[-*]\s+(.+)/.test(text)) {
    return { type: 'unordered-list', content: text.replace(/^[-*]\s+/, '') };
  }

  if (/^\d+\.\s+(.+)/.test(text)) {
    return { type: 'ordered-list', content: text.replace(/^\d+\.\s+/, '') };
  }

  return null;
}

// ============================== TESTS ==============================

// ---- Inline Pattern Tests ----

console.log('=== Inline Markdown Patterns ===\n');

// Bold
let r = testInlinePattern('**bold** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, 'bold');
console.log('✓ **bold** → bold');

r = testInlinePattern('__bold__ ');
assert.equal(r.name, 'bold-underscore');
assert.equal(r.inner, 'bold');
console.log('✓ __bold__ → bold');

// Italic
r = testInlinePattern('*italic* ');
assert.equal(r.name, 'italic');
assert.equal(r.inner, 'italic');
console.log('✓ *italic* → italic');

r = testInlinePattern('_italic_ ');
assert.equal(r.name, 'italic-underscore');
assert.equal(r.inner, 'italic');
console.log('✓ _italic_ → italic');

// Strikethrough
r = testInlinePattern('~~strike~~ ');
assert.equal(r.name, 'strikethrough');
assert.equal(r.inner, 'strike');
console.log('✓ ~~strike~~ → strikethrough');

// Inline code
r = testInlinePattern('`code` ');
assert.equal(r.name, 'code');
assert.equal(r.inner, 'code');
console.log('✓ `code` → inline code');

// Link
r = testInlinePattern('[text](https://example.com) ');
assert.equal(r.name, 'link');
assert.equal(r.inner, 'text');
assert.equal(r.extra, 'https://example.com');
console.log('✓ [text](url) → link');

// No match when not ending with pattern
r = testInlinePattern('normal text ');
assert.equal(r, null);
console.log('✓ normal text → no match');

// Pattern still matches without trailing space (it's the end of string)
r = testInlinePattern('**bold**');
assert.equal(r.name, 'bold');
console.log('✓ **bold** (no trailing space) → still matches (end-of-string anchor)');

// Nested patterns - bold inside a sentence
r = testInlinePattern('some **bold** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, 'bold');
console.log('✓ some **bold** → bold matched, prefix preserved');

// Multiple patterns - match last
r = testInlinePattern('*italic* and **bold** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, 'bold');
console.log('✓ *italic* and **bold** → last pattern (bold) matched');

// ---- Block Pattern Tests ----

console.log('\n=== Block Markdown Patterns ===\n');

// Heading levels 1-6
for (let level = 1; level <= 6; level++) {
  const hashes = '#'.repeat(level);
  r = testBlockPattern(`${hashes} Heading ${level}`);
  assert.equal(r.type, 'heading');
  assert.equal(r.level, level);
  assert.equal(r.content, `Heading ${level}`);
  console.log(`✓ ${hashes} Heading ${level} → h${level}`);
}

// Blockquote
r = testBlockPattern('> A famous quote');
assert.equal(r.type, 'blockquote');
assert.equal(r.content, 'A famous quote');
console.log('✓ > quote → blockquote');

// Unordered list (hyphen)
r = testBlockPattern('- List item');
assert.equal(r.type, 'unordered-list');
assert.equal(r.content, 'List item');
console.log('✓ - item → unordered list');

// Unordered list (asterisk)
r = testBlockPattern('* List item');
assert.equal(r.type, 'unordered-list');
assert.equal(r.content, 'List item');
console.log('✓ * item → unordered list');

// Ordered list
r = testBlockPattern('1. First item');
assert.equal(r.type, 'ordered-list');
assert.equal(r.content, 'First item');
console.log('✓ 1. item → ordered list');

r = testBlockPattern('42. Answer');
assert.equal(r.type, 'ordered-list');
assert.equal(r.content, 'Answer');
console.log('✓ 42. item → ordered list');

// No match for plain text
r = testBlockPattern('Just a regular paragraph');
assert.equal(r, null);
console.log('✓ plain text → no match');

// No match for incomplete patterns
r = testBlockPattern('#No space after hash');
assert.equal(r, null);
console.log('✓ #NoSpace → no match');

r = testBlockPattern('>- no space');
assert.equal(r, null);
console.log('✓ >- no space → no match');

console.log('\n=== All tests passed! ===');
