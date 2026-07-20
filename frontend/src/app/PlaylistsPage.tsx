import React from "react";
import { usePlaylists } from "./hooks/usePlaylists";
import { PlaylistCard } from "../components/PlaylistCard";

export default function PlaylistsPage() {
  const { playlists, loading, error } = usePlaylists();

  if (loading) return <div>Loading playlists...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "2rem",
        justifyContent: "flex-start",
        padding: "2rem",
        minHeight: "100vh",
      }}
    >
      {playlists.map((playlist) => (
        <PlaylistCard
          key={playlist.id}
          title={playlist.title}
          video_count={playlist.itemCount}
          updated_at={playlist.publishedAt}
          thumbnail_url={playlist.thumbnailUrl}
        />
      ))}
    </div>
  );
}
