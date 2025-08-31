import React, { useRef, useEffect } from "react";

interface ScrollingTextProps {
  text: string;
  speed?: number;
  pause?: number;
  className?: string;
}

const ScrollingText: React.FC<ScrollingTextProps> = ({
  text,
  speed = 1,
  pause = 3000,
  className = "",
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const textEl = textRef.current;

    if (!container || !textEl) return;

    textEl.style.transform = "translateX(0)";
    let animation: number;
    let timeoutId: NodeJS.Timeout;

    const startScroll = () => {
      const isOverflowing = textEl.scrollWidth > container.clientWidth;
      if (!isOverflowing) return;
      
      let x = 0;

      const scroll = () => {
        x -= speed;
        textEl.style.transform = `translateX(${x}px)`;

        if (x <= -textEl.scrollWidth) {
          cancelAnimationFrame(animation);
          x = 0;
          textEl.style.transform = `translateX(${x}px)`;
          timeoutId = setTimeout(() => {
            animation = requestAnimationFrame(scroll);
          }, pause);
          return;
        }

        animation = requestAnimationFrame(scroll);
      };

      timeoutId = setTimeout(() => {
        animation = requestAnimationFrame(scroll);
      }, pause);
    };

    animation = requestAnimationFrame(() => {
      requestAnimationFrame(startScroll);
    });

    return () => {
      cancelAnimationFrame(animation);
      clearTimeout(timeoutId);
    };
  }, [text, speed, pause]);

  return (
    <div
      ref={containerRef}
      className={`overflow-hidden whitespace-nowrap w-full ${className}`}
    >
      <div ref={textRef} className="inline-block transform translate-x-0">
        {text}
      </div>
    </div>
  );
};

export default ScrollingText;
