import React, { FC } from "react";
import Image from "next/image";
import { normalizeSrc } from "./utils/normalizeSrc";

interface VideoPreviewProps {
  videoUrl: string;
  videoTime: string;
  thumbnail: string;
  channelUrl: string;
  channelImage: string;
  channelTooltipImage: string;
  channelName: string;
  channelStats: string;
  title: string;
  views: string;
  uploadTime: string;
}

/**
 * VideoPreview renders a single video preview card, preserving the full structure and classes.
 * All data is passed in as props for full parametrization.
 */
const VideoPreview: FC<VideoPreviewProps> = ({
  videoUrl,
  videoTime,
  thumbnail,
  channelUrl,
  channelImage,
  channelTooltipImage,
  channelName,
  channelStats,
  title,
  views,
  uploadTime,
}) => (
  <div className="video-preview">
    <div className="thumbnail-row">
      <a href={videoUrl} target="_blank" className="video-title-link">
        <Image
          width={281}
          height={157}
          className="thumbnail"
          src={normalizeSrc(thumbnail)}
          alt={title + " thumbnail"}
        />
      </a>

      <div className="video-time">{videoTime}</div>
    </div>

    <div className="video-info-grid">
      <div className="channel-picture">
        <div className="profile-picture-container">
          <a href={channelUrl} target="_blank" className="channel-link">
            <Image
              alt="profile picture"
              className="profile-picture"
              src={normalizeSrc(channelImage)}
              width={36}
              height={36}
            />
          </a>

          <div className="channel-tooltip">
            <Image
              width={50}
              height={50}
              className="channel-tooltip-picture"
              src={normalizeSrc(channelTooltipImage)}
              alt={channelName + " tooltip"}
            />
            <div className="channel-info-tooltip">
              <p className="channel-tooltip-name">{channelName}</p>

              <p className="channel-tooltip-stats">{channelStats}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="video-info">
        <a href={videoUrl} target="_blank" className="video-title-link">
          <p className="video-title">{title}</p>
        </a>

        <div className="tooltip-hover">
          <a href={channelUrl} target="_blank" className="channel-link">
            <p className="video-author">{channelName}</p>
          </a>

          <p className="video-stats">
            {views} &#183; {uploadTime}
          </p>
        </div>
      </div>
    </div>
  </div>
);

export default VideoPreview;
