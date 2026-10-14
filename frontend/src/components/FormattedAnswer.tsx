'use client';

import React from 'react';

interface FormattedAnswerProps {
  content: string;
  isUser?: boolean;
}

type Block =
  | { type: 'heading'; level: number; text: string }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] }
  | { type: 'codeblock'; language: string; code: string }
  | { type: 'blockquote'; text: string }
  | { type: 'paragraph'; text: string };

/**
 * Parses inline Markdown formatting:
 * - **bold** or __bold__
 * - *italic* or _italic_
 * - `inline code`
 * - [link text](url)
 */
function renderInlineTokens(text: string, isUser = false): React.ReactNode[] {
  if (!text) return [];

  // Match: code, bold, italic, links
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\))/g;
  const parts = text.split(pattern);

  return parts.map((part, index) => {
    if (!part) return null;

    // Inline code: `code`
    if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
      const codeContent = part.slice(1, -1);
      return (
        <code
          key={index}
          style={{
            background: isUser ? 'rgba(255, 255, 255, 0.15)' : '#F3F4F6',
            color: isUser ? '#FCD34D' : '#7C3AED',
            padding: '2px 6px',
            borderRadius: '4px',
            fontFamily: 'var(--font-mono, monospace)',
            fontSize: '12px',
            fontWeight: 500,
          }}
        >
          {codeContent}
        </code>
      );
    }

    // Bold: **text** or __text__
    if (
      (part.startsWith('**') && part.endsWith('**') && part.length >= 4) ||
      (part.startsWith('__') && part.endsWith('__') && part.length >= 4)
    ) {
      const boldContent = part.slice(2, -2);
      return (
        <strong
          key={index}
          style={{
            fontWeight: 650,
            color: isUser ? '#FFFFFF' : '#111827',
          }}
        >
          {renderInlineTokens(boldContent, isUser)}
        </strong>
      );
    }

    // Italic: *text* or _text_
    if (
      (part.startsWith('*') && part.endsWith('*') && part.length >= 2) ||
      (part.startsWith('_') && part.endsWith('_') && part.length >= 2)
    ) {
      const italicContent = part.slice(1, -1);
      return (
        <em key={index} style={{ fontStyle: 'italic' }}>
          {italicContent}
        </em>
      );
    }

    // Link: [label](url)
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      const [, label, url] = linkMatch;
      return (
        <a
          key={index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: isUser ? '#DDD6FE' : '#7C3AED',
            textDecoration: 'underline',
            textUnderlineOffset: '2px',
          }}
        >
          {label}
        </a>
      );
    }

    // Plain text
    return <span key={index}>{part}</span>;
  });
}

/**
 * Tokenize raw markdown string into logical semantic blocks
 */
function parseMarkdownBlocks(rawText: string): Block[] {
  if (!rawText || !rawText.trim()) return [];

  const lines = rawText.replace(/\r\n/g, '\n').split('\n');
  const blocks: Block[] = [];

  let inCodeBlock = false;
  let codeBlockLang = '';
  let codeBlockLines: string[] = [];

  let currentListType: 'ul' | 'ol' | null = null;
  let currentListItems: string[] = [];

  let currentParagraphLines: string[] = [];

  const flushParagraph = () => {
    if (currentParagraphLines.length > 0) {
      const pText = currentParagraphLines.join(' ').trim();
      if (pText) {
        blocks.push({ type: 'paragraph', text: pText });
      }
      currentParagraphLines = [];
    }
  };

  const flushList = () => {
    if (currentListType && currentListItems.length > 0) {
      blocks.push({
        type: currentListType,
        items: [...currentListItems],
      });
      currentListType = null;
      currentListItems = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // 1. Code fence check: ```lang
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        // End code block
        blocks.push({
          type: 'codeblock',
          language: codeBlockLang,
          code: codeBlockLines.join('\n'),
        });
        inCodeBlock = false;
        codeBlockLang = '';
        codeBlockLines = [];
      } else {
        // Start code block
        flushParagraph();
        flushList();
        inCodeBlock = true;
        codeBlockLang = trimmed.slice(3).trim();
        codeBlockLines = [];
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockLines.push(rawLine);
      continue;
    }

    // 2. Empty line -> block separator
    if (!trimmed) {
      flushParagraph();
      flushList();
      continue;
    }

    // 3. Headings: #, ##, ###, ####
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.*)$/);
    if (headingMatch) {
      flushParagraph();
      flushList();
      const level = headingMatch[1].length;
      const text = headingMatch[2].trim();
      blocks.push({ type: 'heading', level, text });
      continue;
    }

    // 4. Standalone Bold Section Heading: e.g. **Projects Mentioned** or **Summary**
    const standaloneBoldMatch = trimmed.match(/^\*\*([^*]+)\*\*$/);
    if (standaloneBoldMatch) {
      flushParagraph();
      flushList();
      blocks.push({
        type: 'heading',
        level: 3,
        text: standaloneBoldMatch[1].trim(),
      });
      continue;
    }

    // 5. Unordered List Items: - item or * item
    const ulMatch = trimmed.match(/^[-*]\s+(.*)$/);
    if (ulMatch) {
      flushParagraph();
      if (currentListType && currentListType !== 'ul') {
        flushList();
      }
      currentListType = 'ul';
      currentListItems.push(ulMatch[1].trim());
      continue;
    }

    // 6. Ordered List Items: 1. item, 2. item
    const olMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (olMatch) {
      flushParagraph();
      if (currentListType && currentListType !== 'ol') {
        flushList();
      }
      currentListType = 'ol';
      currentListItems.push(olMatch[2].trim());
      continue;
    }

    // 7. Blockquote: > text
    if (trimmed.startsWith('>')) {
      flushParagraph();
      flushList();
      blocks.push({
        type: 'blockquote',
        text: trimmed.replace(/^>\s?/, '').trim(),
      });
      continue;
    }

    // 8. If we are currently in a list, a continuation line indented might be part of the list
    if (currentListType && (rawLine.startsWith('  ') || rawLine.startsWith('\t'))) {
      if (currentListItems.length > 0) {
        currentListItems[currentListItems.length - 1] += ' ' + trimmed;
        continue;
      }
    }

    // Otherwise, it's regular paragraph text
    flushList();
    currentParagraphLines.push(trimmed);
  }

  // Flush remaining buffers
  if (inCodeBlock) {
    blocks.push({
      type: 'codeblock',
      language: codeBlockLang,
      code: codeBlockLines.join('\n'),
    });
  }
  flushParagraph();
  flushList();

  return blocks;
}

/**
 * FormattedAnswer Component
 * Renders structured, readable assistant responses with headings, bullet points,
 * numbered steps, inline bold highlights, code blocks, and comfortable spacing.
 */
export const FormattedAnswer: React.FC<FormattedAnswerProps> = ({ content, isUser = false }) => {
  if (!content) return null;

  // For user messages, simple clean wrap preserving line breaks
  if (isUser) {
    return (
      <div
        style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          fontSize: '14px',
          lineHeight: '1.5',
          color: '#FFFFFF',
        }}
      >
        {content}
      </div>
    );
  }

  const blocks = parseMarkdownBlocks(content);

  // If no structured blocks (single simple plain line), render directly
  if (blocks.length === 0) {
    return (
      <div style={{ wordBreak: 'break-word', fontSize: '14px', lineHeight: '1.6', color: '#111827' }}>
        {content}
      </div>
    );
  }

  return (
    <div
      className="formatted-answer"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        wordBreak: 'break-word',
        overflowWrap: 'break-word',
        fontSize: '14px',
        lineHeight: 1.6,
        color: '#1F2937',
      }}
    >
      {blocks.map((block, idx) => {
        const isFirst = idx === 0;
        const isLast = idx === blocks.length - 1;

        switch (block.type) {
          case 'heading': {
            // Render subtle, proportional headings that don't overwhelm the bubble
            const isTopLevel = block.level <= 2;
            return (
              <div
                key={idx}
                style={{
                  fontSize: isTopLevel ? '15px' : '14px',
                  fontWeight: 700,
                  color: '#111827',
                  marginTop: isFirst ? '0px' : '8px',
                  marginBottom: '2px',
                  letterSpacing: '-0.01em',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>{renderInlineTokens(block.text, isUser)}</span>
              </div>
            );
          }

          case 'ul': {
            return (
              <ul
                key={idx}
                style={{
                  margin: '4px 0 6px 0',
                  paddingLeft: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '5px',
                  listStyleType: 'disc',
                }}
              >
                {block.items.map((item, itemIdx) => (
                  <li
                    key={itemIdx}
                    style={{
                      lineHeight: '1.55',
                      color: '#374151',
                      paddingLeft: '2px',
                    }}
                  >
                    {renderInlineTokens(item, isUser)}
                  </li>
                ))}
              </ul>
            );
          }

          case 'ol': {
            return (
              <ol
                key={idx}
                style={{
                  margin: '4px 0 6px 0',
                  paddingLeft: '22px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '5px',
                  listStyleType: 'decimal',
                }}
              >
                {block.items.map((item, itemIdx) => (
                  <li
                    key={itemIdx}
                    style={{
                      lineHeight: '1.55',
                      color: '#374151',
                      paddingLeft: '2px',
                    }}
                  >
                    {renderInlineTokens(item, isUser)}
                  </li>
                ))}
              </ol>
            );
          }

          case 'blockquote': {
            return (
              <blockquote
                key={idx}
                style={{
                  borderLeft: '3px solid #C4B5FD',
                  margin: '6px 0',
                  padding: '6px 12px',
                  background: '#F9FAFB',
                  color: '#4B5563',
                  borderRadius: '0 6px 6px 0',
                  fontStyle: 'italic',
                }}
              >
                {renderInlineTokens(block.text, isUser)}
              </blockquote>
            );
          }

          case 'codeblock': {
            return (
              <div
                key={idx}
                style={{
                  background: '#18181B',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  margin: '6px 0',
                  overflowX: 'auto',
                }}
              >
                {block.language && (
                  <div
                    style={{
                      fontSize: '11px',
                      color: '#9CA3AF',
                      textTransform: 'uppercase',
                      fontFamily: 'var(--font-mono, monospace)',
                      marginBottom: '4px',
                      borderBottom: '1px solid #27272A',
                      paddingBottom: '2px',
                    }}
                  >
                    {block.language}
                  </div>
                )}
                <pre
                  style={{
                    margin: 0,
                    fontFamily: 'var(--font-mono, monospace)',
                    fontSize: '12px',
                    lineHeight: '1.5',
                    color: '#F4F4F5',
                  }}
                >
                  <code>{block.code}</code>
                </pre>
              </div>
            );
          }

          case 'paragraph':
          default: {
            return (
              <p
                key={idx}
                style={{
                  margin: 0,
                  marginBottom: isLast ? 0 : '4px',
                  lineHeight: '1.6',
                  color: '#1F2937',
                }}
              >
                {renderInlineTokens(block.text, isUser)}
              </p>
            );
          }
        }
      })}
    </div>
  );
};
