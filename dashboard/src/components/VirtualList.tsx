import React, { useRef, useState, useEffect, UIEvent } from 'react';

interface VirtualListProps<T> {
  items: T[];
  rowHeight?: number;
  overscan?: number;
  renderItem: (item: T, index: number) => React.ReactNode;
}

function VirtualList<T>({ items, rowHeight = 36, overscan = 5, renderItem }: VirtualListProps<T>) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const height = (containerRef.current?.clientHeight) || 300;
  const totalHeight = items.length * rowHeight;

  const startIndex = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const endIndex = Math.min(items.length - 1, Math.ceil((scrollTop + height) / rowHeight) + overscan);
  const visibleItems = items.slice(startIndex, endIndex + 1);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onScroll = (e: Event) => setScrollTop((e.target as HTMLElement).scrollTop);
    el.addEventListener('scroll', onScroll);
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  const paddingTop = startIndex * rowHeight;
  const paddingBottom = Math.max(0, totalHeight - paddingTop - visibleItems.length * rowHeight);

  return (
    <div ref={containerRef} style={{ overflowY: 'auto', height: '100%' }}>
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${paddingTop}px)` }}>
          {visibleItems.map((it, idx) => (
            <div key={startIndex + idx} style={{ height: rowHeight, boxSizing: 'border-box' }}>
              {renderItem(it, startIndex + idx)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default VirtualList;
