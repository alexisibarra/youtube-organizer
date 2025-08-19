"use client";
import React from "react";
import VideoPreview from "./VideoPreview";
import { videosMetadata } from "./utils/videosMetadata";

/**
 * VideoPreviewList renders the list of videos using the VideoPreview component.
 */
export const VideoPreviewList = () => {
  return (
    <>
      <main>
        <section className="video-grid">
          {videosMetadata.map((video) => (
            <VideoPreview key={video.videoUrl} {...video} />
          ))}
        </section>
      </main>
    </>
  );
};
