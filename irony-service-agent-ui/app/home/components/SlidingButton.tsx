"use client";

import Image from "next/image";
import React, { useCallback, useEffect, useRef, useState } from "react";

interface SlidingButtonProps {
  onComplete: () => Promise<void>;
  isLoading?: boolean;
  loadingText?: string;
  buttonText?: string;
  iconSrc?: string;
}

export default function SlidingButton({
  onComplete,
  isLoading = false,
  loadingText = "Confirming...",
  buttonText = "Slide to confirm",
  iconSrc = "/mingcute_right-line_black.svg",
}: SlidingButtonProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [slidePosition, setSlidePosition] = useState(0);
  const completeTriggeredRef = useRef(false);
  const sliderRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleTouchStart = () => {
    if (!isLoading) setIsDragging(true);
  };

  const handleTouchMove = useCallback(
    (e: React.TouchEvent | React.MouseEvent) => {
      if (!isDragging || isLoading) return;

      const containerWidth = containerRef.current?.offsetWidth || 0;
      let clientX: number;

      if ("touches" in e) {
        clientX = e.touches[0].clientX;
      } else {
        clientX = (e as React.MouseEvent).clientX;
      }

      const rect = containerRef.current?.getBoundingClientRect();
      const position = Math.max(0, Math.min(clientX - (rect?.left || 0), containerWidth));
      setSlidePosition(position);

      if (position >= containerWidth - 10) {
        if (!completeTriggeredRef.current) {
          completeTriggeredRef.current = true;
          onComplete().catch(() => {
            setSlidePosition(0);
            completeTriggeredRef.current = false;
          });
        }
      }
    },
    [isDragging, isLoading, onComplete]
  );

  const handleTouchEnd = useCallback(() => {
    if (!isDragging) return;
    setIsDragging(false);

    const containerWidth = containerRef.current?.offsetWidth || 0;
    if (slidePosition < containerWidth - 10) {
      setSlidePosition(0);
    }
  }, [isDragging, slidePosition]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => handleTouchMove(e as any);
    const handleMouseUp = () => handleTouchEnd();

    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, handleTouchEnd, handleTouchMove]);

  return (
    <div ref={containerRef} className="relative h-14 bg-gray-100 rounded-full overflow-hidden">
      <div
        ref={sliderRef}
        className={`absolute left-0 top-0 h-full w-14 bg-amber-300 rounded-full cursor-pointer transition-colors
          ${isDragging ? "bg-amber-400" : ""} ${isLoading ? "cursor-not-allowed opacity-50" : ""}`}
        style={{ transform: `translateX(${slidePosition}px)` }}
        onMouseDown={handleTouchStart}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <div className="h-full w-full flex items-center justify-center">
          <Image src={iconSrc} alt="Slide" width={24} height={24} />
        </div>
      </div>
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <span className="text-gray-500">{isLoading ? loadingText : buttonText}</span>
      </div>
    </div>
  );
}
