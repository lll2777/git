"use client";

import type { KeyboardEvent, PointerEvent, ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

const storageKey = "ai-data-analysis.workspace.right-panel-width.v2";
const defaultRightPanelWidth = 60;
const minRightPanelWidth = 42;
const maxRightPanelWidth = 78;

type ResizableWorkspaceLayoutProps = {
  left: ReactNode;
  right: ReactNode;
};

export function ResizableWorkspaceLayout({
  left,
  right,
}: ResizableWorkspaceLayoutProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rightPanelWidth, setRightPanelWidth] = useState(
    defaultRightPanelWidth,
  );
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      const storedWidth = window.localStorage.getItem(storageKey);
      if (!storedWidth) {
        return;
      }

      const parsedWidth = Number(storedWidth);
      if (Number.isFinite(parsedWidth)) {
        setRightPanelWidth(clampRightPanelWidth(parsedWidth));
      }
    });

    return () => window.cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(storageKey, String(rightPanelWidth));
  }, [rightPanelWidth]);

  function updateWidth(clientX: number) {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const bounds = container.getBoundingClientRect();
    const pointerOffset = clientX - bounds.left;
    const leftPercent = (pointerOffset / bounds.width) * 100;
    setRightPanelWidth(clampRightPanelWidth(100 - leftPercent));
  }

  function handlePointerDown(event: PointerEvent<HTMLDivElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    setIsDragging(true);
    updateWidth(event.clientX);
  }

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    if (!isDragging) {
      return;
    }

    updateWidth(event.clientX);
  }

  function stopDragging(event: PointerEvent<HTMLDivElement>) {
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    setIsDragging(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      setRightPanelWidth((width) => clampRightPanelWidth(width + 2));
    }

    if (event.key === "ArrowRight") {
      event.preventDefault();
      setRightPanelWidth((width) => clampRightPanelWidth(width - 2));
    }
  }

  return (
    <div
      ref={containerRef}
      className="flex flex-1 flex-col gap-6 py-8 lg:grid lg:gap-0"
      style={{
        gridTemplateColumns: `minmax(0, ${100 - rightPanelWidth}fr) 0.875rem minmax(0, ${rightPanelWidth}fr)`,
      }}
    >
      <div className="min-w-0">{left}</div>

      <div
        aria-label="调整左右面板宽度"
        aria-orientation="vertical"
        aria-valuemax={maxRightPanelWidth}
        aria-valuemin={minRightPanelWidth}
        aria-valuenow={rightPanelWidth}
        className="group hidden cursor-col-resize items-stretch justify-center px-1 lg:flex"
        onKeyDown={handleKeyDown}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={stopDragging}
        onPointerCancel={stopDragging}
        role="separator"
        tabIndex={0}
      >
        <div
          className={[
            "h-full w-px rounded-full bg-white/10 transition-colors",
            isDragging ? "bg-white/40" : "group-hover:bg-white/30",
          ].join(" ")}
        />
      </div>

      <aside className="min-w-0 space-y-4">{right}</aside>
    </div>
  );
}

function clampRightPanelWidth(width: number) {
  return Math.min(maxRightPanelWidth, Math.max(minRightPanelWidth, width));
}
