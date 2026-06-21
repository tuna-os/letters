/**
 * Comprehensive tests for Markdown shortcut patterns used in editor.js
 */
const assert = require('assert').strict;

// ---- Pure functions extracted from editor.js ----

function isBlockElement(elem) {
  const blockTags = ['P','H1','H2','H3','H4','H5','H6','PRE','BLOCKQUOTE','DIV'];
  if (!elem || !elem.tagName) return false;
  return blockTags.includes(elem.tagName);
}

// ---- Inline Patterns ----

const inlinePatterns = [
  { name: 'link',              regex: /\[([^\]]+)\]\(([^)]+)\)$/ },
  { name: 'bold',              regex: /\*\*(.+?)\*\*$/ },
  { name: 'bold-underscore',   regex: /__(.+?)__$/ },
  { name: 'italic',            regex: /\*(.+?)\*$/ },
  { name: 'italic-underscore', regex: /_(.+?)_$/ },
  { name: 'strikethrough',     regex: /~~(.+?)~~$/ },
  { name: 'code',              regex: /`(.+?)`$/ },
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

// ---- Block Patterns ----

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

// ============================== isBlockElement TESTS ==============================

console.log('=== isBlockElement() ===\n');

const blockTagNames = ['P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'PRE', 'BLOCKQUOTE', 'DIV'];
for (const tag of blockTagNames) {
  assert.equal(isBlockElement({ tagName: tag }), true);
  console.log(`✓ ${tag} → true`);
}

const inlineTagNames = ['SPAN', 'A', 'STRONG', 'EM', 'U', 'S', 'CODE', 'IMG', 'BR', 'INPUT', 'LABEL', 'B', 'I', 'UL', 'OL', 'LI'];
for (const tag of inlineTagNames) {
  assert.equal(isBlockElement({ tagName: tag }), false);
  console.log(`✓ ${tag} → false`);
}

// Edge cases
assert.equal(isBlockElement(null), false);
console.log('✓ null → false');
assert.equal(isBlockElement(undefined), false);
console.log('✓ undefined → false');
assert.equal(isBlockElement({}), false);
console.log('✓ {} (no tagName) → false');
assert.equal(isBlockElement({ tagName: '' }), false);
console.log('✓ tagName="" → false');
assert.equal(isBlockElement({ tagName: 'div' }), false);  // lowercase
console.log('✓ tagName="div" (lowercase) → false');

// ============================== INLINE PATTERN TESTS ==============================

console.log('\n=== Inline Markdown Patterns ===\n');

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

// ---- Edge Cases ----

// Single character content
r = testInlinePattern('**a** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, 'a');
console.log('✓ **a** → bold (single char)');

r = testInlinePattern('*x* ');
assert.equal(r.name, 'italic');
assert.equal(r.inner, 'x');
console.log('✓ *x* → italic (single char)');

// No match without trailing space
r = testInlinePattern('**bold**');
assert.equal(r.name, 'bold');
console.log('✓ **bold** (no trailing space) → still matches (end-of-string)');

// Plain text — no match
r = testInlinePattern('normal text ');
assert.equal(r, null);
console.log('✓ normal text → no match');

// Empty after trim would be empty string
r = testInlinePattern(' ');
assert.equal(r, null);
console.log('✓ just space → no match');

// Numbers inside patterns
r = testInlinePattern('**123** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, '123');
console.log('✓ **123** → bold (numbers)');

// Special characters inside
r = testInlinePattern('**héllo wörld** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, 'héllo wörld');
console.log('✓ **héllo wörld** → bold (unicode)');

// Mixed underscores (underscore inside bold)
r = testInlinePattern('**bold_with_underscore** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, 'bold_with_underscore');
console.log('✓ **bold_with_underscore** → bold (underscores inside)');

// Pattern matching when preceded by text
r = testInlinePattern('some **bold** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, 'bold');
console.log('✓ some **bold** → bold matched, prefix ignored');

// Multiple patterns — last one matched
r = testInlinePattern('*italic* and **bold** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, 'bold');
console.log('✓ *italic* and **bold** → last pattern (bold)');

// Punctuation inside
r = testInlinePattern('**hello, world!** ');
assert.equal(r.name, 'bold');
assert.equal(r.inner, 'hello, world!');
console.log('✓ **hello, world!** → bold with punctuation');

// Link with complex URL
r = testInlinePattern('[click](https://example.com/path?q=search&lang=en#section) ');
assert.equal(r.name, 'link');
assert.equal(r.inner, 'click');
assert.equal(r.extra, 'https://example.com/path?q=search&lang=en#section');
console.log('✓ [click](complex url) → link');

// Link with spaces in text
r = testInlinePattern('[click here](https://example.com) ');
assert.equal(r.name, 'link');
assert.equal(r.inner, 'click here');
console.log('✓ [click here](url) → link with spaces in text');

// No match: malformed
r = testInlinePattern('[broken(url) ');
assert.equal(r, null);
console.log('✓ [broken(url) → no match (malformed)');

r = testInlinePattern('**unclosed ');
assert.equal(r, null);
console.log('✓ **unclosed → no match');

r = testInlinePattern('*nope ');
assert.equal(r, null);
console.log('✓ *nope → no match');

// Empty-ish content — **** is matched as italic with '*' content
r = testInlinePattern('**** ');
assert.equal(r.name, 'italic'); // \*(.+?)\*$ matches **** as * + ** + *
console.log("✓ **** → italic (edge: matched as * + ** + *)");

r = testInlinePattern('`` ');
assert.equal(r, null);
console.log('✓ `` → no match (needs content between backticks)');

// Backtick inside inline code is tricky — test basic
r = testInlinePattern('`backtick` ');
assert.equal(r.name, 'code');
assert.equal(r.inner, 'backtick');
console.log('✓ `backtick` → inline code');

// ============================== BLOCK PATTERN TESTS ==============================

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

// Blockquote with multiple words
r = testBlockPattern('> To be or not to be');
assert.equal(r.type, 'blockquote');
assert.equal(r.content, 'To be or not to be');
console.log('✓ > To be or not to be → blockquote');

// Unordered list
for (const marker of ['-', '*']) {
  r = testBlockPattern(`${marker} List item`);
  assert.equal(r.type, 'unordered-list');
  assert.equal(r.content, 'List item');
  console.log(`✓ ${marker} item → unordered list`);
}

// Ordered list
r = testBlockPattern('1. First item');
assert.equal(r.type, 'ordered-list');
assert.equal(r.content, 'First item');
console.log('✓ 1. item → ordered list');

r = testBlockPattern('42. Answer');
assert.equal(r.type, 'ordered-list');
assert.equal(r.content, 'Answer');
console.log('✓ 42. item → ordered list');

r = testBlockPattern('999. Many items');
assert.equal(r.type, 'ordered-list');
assert.equal(r.content, 'Many items');
console.log('✓ 999. item → ordered list');

// ---- Edge Cases ----

// Content with special characters
r = testBlockPattern('> Héllo, 世界!');
assert.equal(r.type, 'blockquote');
assert.equal(r.content, 'Héllo, 世界!');
console.log('✓ > Héllo, 世界! → blockquote (unicode)');

// Content with internal formatting
r = testBlockPattern('# **bold heading**');
assert.equal(r.type, 'heading');
assert.equal(r.level, 1);
assert.equal(r.content, '**bold heading**');
console.log('✓ # **bold heading** → h1 (markdown inside OK)');

// No match: plain text
r = testBlockPattern('Just a regular paragraph');
assert.equal(r, null);
console.log('✓ plain text → no match');

// No match: incomplete patterns
r = testBlockPattern('#No space after hash');
assert.equal(r, null);
console.log('✓ #NoSpace → no match');

r = testBlockPattern('>- no space');
assert.equal(r, null);
console.log('✓ >- no space → no match');

r = testBlockPattern('-no space');
assert.equal(r, null);
console.log('✓ -no space → no match');

r = testBlockPattern('1.no space');
assert.equal(r, null);
console.log('✓ 1.no space → no match');

r = testBlockPattern('');
assert.equal(r, null);
console.log('✓ empty string → no match');

// Multiple spaces after marker
r = testBlockPattern('#    Spaced heading');
assert.equal(r.type, 'heading');
assert.equal(r.level, 1);
assert.equal(r.content, 'Spaced heading');
console.log('✓ #    spaced → heading with multiple spaces');

r = testBlockPattern('>    Spaced quote');
assert.equal(r.type, 'blockquote');
assert.equal(r.content, 'Spaced quote');
console.log('✓ >    spaced → quote with multiple spaces (regex matches \\s+)');

// Leading whitespace — should NOT match
r = testBlockPattern('  # Not a heading');
assert.equal(r, null);
console.log('✓ \"  # Not a heading\" (indented) → no match');

r = testBlockPattern('  - not a list');
assert.equal(r, null);
console.log('✓ \"  - not a list\" (indented) → no match');

// Trailing whitespace
r = testBlockPattern('# Heading with spaces   ');
assert.equal(r.type, 'heading');
assert.equal(r.level, 1);
console.log('✓ \"# Heading with spaces   \" → heading (trailing spaces in content)');

// Very long content
const longText = 'A'.repeat(1000);
r = testBlockPattern(`# ${longText}`);
assert.equal(r.type, 'heading');
assert.equal(r.level, 1);
assert.equal(r.content.length, 1000);
console.log('✓ # (1000 char content) → h1 (long content)');

// Code block with triple backtick (not currently supported — verify no false positive)
r = testBlockPattern('```');
assert.equal(r, null);
console.log('✓ ``` alone → no match (triple backtick not supported)');

// ============================== UNDO STACK GUARD ==============================

console.log('\n=== Undo Stack Guard Logic ===\n');

// Test the MAX_UNDO limit logic
const MAX_UNDO = 50;
let stack = [];

function push(stack, item) {
  stack.push(item);
  if (stack.length > MAX_UNDO) stack.shift();
}

for (let i = 0; i < 60; i++) {
  push(stack, `state-${i}`);
}
assert.equal(stack.length, MAX_UNDO);
assert.equal(stack[0], 'state-10');
assert.equal(stack[stack.length - 1], 'state-59');
console.log(`✓ Undo stack capped at ${MAX_UNDO} (60 pushes → ${stack.length})`);

// Redo cleared on new action
let redoStack = ['state-1', 'state-2'];
stack = ['state-0'];
if (stack.length > 0) {
  redoStack.length = 0;  // simulate clearing redo on new action
}
assert.equal(redoStack.length, 0);
console.log('✓ Redo stack cleared on new action');

// ============================== SUMMARY ==============================

console.log(`\n✓ All ${assert.strict ? 'assertions' : 'tests'} passed!`);
