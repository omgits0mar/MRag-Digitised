import { useEffect, useRef, useState } from "react";

const SCROLL_THRESHOLD_PX = 72;

export function useTranscriptScroll(activityKey: string) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [jumpToLatestVisible, setJumpToLatestVisible] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return undefined;
    }

    const handleScroll = (): void => {
      const distanceFromBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight;

      setJumpToLatestVisible(distanceFromBottom > SCROLL_THRESHOLD_PX);
    };

    handleScroll();
    container.addEventListener("scroll", handleScroll);
    return () => {
      container.removeEventListener("scroll", handleScroll);
    };
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (container === null || jumpToLatestVisible) {
      return;
    }

    container.scrollTop = container.scrollHeight;
  }, [activityKey, jumpToLatestVisible]);

  function scrollToLatest(): void {
    const container = containerRef.current;
    if (container === null) {
      return;
    }

    container.scrollTop = container.scrollHeight;
    setJumpToLatestVisible(false);
  }

  return {
    containerRef,
    jumpToLatestVisible,
    scrollToLatest,
  };
}
