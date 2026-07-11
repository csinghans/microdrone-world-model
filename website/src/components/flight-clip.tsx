"use client";

import { useEffect, useRef, useState } from "react";

type FlightClipProps = {
  src: string;
  poster: string;
  title: string;
  description: string;
  ariaLabel: string;
  playLabel: string;
  pauseLabel: string;
  priority?: boolean;
};

export function FlightClip({
  src,
  poster,
  title,
  description,
  ariaLabel,
  playLabel,
  pauseLabel,
  priority = false,
}: FlightClipProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reducedMotion) {
      video.pause();
      return;
    }

    void video.play().catch(() => undefined);
  }, []);

  async function togglePlayback() {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused) {
      try {
        await video.play();
        setIsPlaying(true);
      } catch {
        setIsPlaying(false);
      }
    } else {
      video.pause();
      setIsPlaying(false);
    }
  }

  return (
    <figure className="flight-clip">
      <div className="flight-clip__screen">
        <video
          ref={videoRef}
          muted
          loop
          playsInline
          poster={poster}
          preload={priority ? "metadata" : "none"}
          aria-label={ariaLabel}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        >
          <source src={src} type="video/mp4" />
        </video>
        <div className="flight-clip__reticle" aria-hidden="true" />
        <span className="flight-clip__status" aria-hidden="true">
          {isPlaying ? "REC" : "HOLD"}
        </span>
        <button
          className="flight-clip__control"
          type="button"
          onClick={togglePlayback}
          aria-pressed={isPlaying}
        >
          <span aria-hidden="true">{isPlaying ? "Ⅱ" : "▶"}</span>
          {isPlaying ? pauseLabel : playLabel}
        </button>
      </div>
      <figcaption>
        <strong>{title}</strong>
        <span>{description}</span>
      </figcaption>
    </figure>
  );
}
