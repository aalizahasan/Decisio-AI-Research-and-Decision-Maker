import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  if (!content) return null;

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let currentList: { type: 'ul' | 'ol'; items: React.ReactNode[] } | null = null;

  const parseInline = (text: str): React.ReactNode[] => {
    // Regex to capture **bold text**
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
        const inner = part.slice(2, -2);
        return <strong key={index} style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{inner}</strong>;
      }
      return part;
    });
  };

  const flushList = () => {
    if (!currentList) return;
    const ListTag = currentList.type;
    const key = `list-${elements.length}`;
    elements.push(
      <ListTag key={key} style={{ paddingLeft: '1.25rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
        {currentList.items}
      </ListTag>
    );
    currentList = null;
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    if (!trimmed) {
      flushList();
      return;
    }

    // Horizontal Rule
    if (trimmed === '---' || trimmed === '***' || trimmed === '___') {
      flushList();
      elements.push(<hr key={index} style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: '1.25rem 0' }} />);
      return;
    }

    // Headings
    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h3 key={index} style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '1.25rem', marginBottom: '0.5rem' }}>
          {parseInline(trimmed.slice(4))}
        </h3>
      );
      return;
    }

    if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h2 key={index} style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '1.5rem', marginBottom: '0.65rem' }}>
          {parseInline(trimmed.slice(3))}
        </h2>
      );
      return;
    }

    if (trimmed.startsWith('# ')) {
      flushList();
      elements.push(
        <h1 key={index} style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '1.5rem', marginBottom: '0.75rem' }}>
          {parseInline(trimmed.slice(2))}
        </h1>
      );
      return;
    }

    // Bullet Lists (* item, - item, • item)
    const bulletMatch = trimmed.match(/^[\*\-•]\s+(.+)/);
    if (bulletMatch) {
      if (!currentList || currentList.type !== 'ul') {
        flushList();
        currentList = { type: 'ul', items: [] };
      }
      currentList.items.push(
        <li key={index} style={{ marginBottom: '0.35rem', lineHeight: '1.6' }}>
          {parseInline(bulletMatch[1])}
        </li>
      );
      return;
    }

    // Numbered Lists (1. item)
    const numberMatch = trimmed.match(/^\d+\.\s+(.+)/);
    if (numberMatch) {
      if (!currentList || currentList.type !== 'ol') {
        flushList();
        currentList = { type: 'ol', items: [] };
      }
      currentList.items.push(
        <li key={index} style={{ marginBottom: '0.35rem', lineHeight: '1.6' }}>
          {parseInline(numberMatch[1])}
        </li>
      );
      return;
    }

    // Regular Paragraph
    flushList();
    elements.push(
      <p key={index} style={{ marginBottom: '0.75rem', lineHeight: '1.65', color: 'var(--text-primary)' }}>
        {parseInline(trimmed)}
      </p>
    );
  });

  flushList();

  return <div className="markdown-content">{elements}</div>;
};
