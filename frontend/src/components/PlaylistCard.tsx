import React from "react";
import Image from "next/image";
import styles from "./PlaylistCard.module.css";

export type PlaylistCardProps = {
  title: string;
  video_count: number;
  updated_at: string;
  thumbnail_url: string;
};

export const PlaylistCard: React.FC<PlaylistCardProps> = ({
  title,
  video_count,
  updated_at,
  thumbnail_url,
}) => {
  return (
    <div className={styles.card}>
      <Image
        src={thumbnail_url}
        alt={title}
        className={styles.thumbnail}
        width={320} // Set appropriate width
        height={180} // Set appropriate height
        priority // Improves LCP for above-the-fold images
      />

      <div className={styles.info}>
        <h3 className={styles.title}>{title}</h3>
        {/* <p className={styles.meta}>
          {privacy_status} &bull; Playlist
        </p> */}
        <p className={styles.meta}>{video_count.toLocaleString()} videos</p>
        <p className={styles.meta}>
          Updated {new Date(updated_at).toLocaleDateString()}
        </p>
        <a className={styles.link} href="#">
          View full playlist
        </a>
      </div>
    </div>
  );
};
