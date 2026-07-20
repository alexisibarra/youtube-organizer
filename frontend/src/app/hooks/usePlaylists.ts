// usePlaylists.ts
// Custom React hook to fetch playlists from the backend API
// Teaching note: This hook uses useEffect and useState to fetch data when the component mounts.
// You can extend this to handle loading/error states and pagination as needed.

import { useEffect, useState } from "react";

export type Playlist = {
  channelTitle: string;
  description: string;
  id: string;
  itemCount: number;
  publishedAt: string;
  thumbnailUrl: string;
  title: string;
};

export function usePlaylists() {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPlaylists() {
      try {
        const res = await fetch(
          "https://localhost:8000/api/youtube/playlists/",
          { credentials: "include" }
        );
        if (!res.ok) throw new Error("Failed to fetch playlists");
        const data = await res.json();
        // Teaching: Map YouTube API response to normalized Playlist objects
        const playlists: Playlist[] = (data.items || []).map((item: any) => ({
          id: item.id,
          title: item.snippet.title,
          description: item.snippet.description,
          thumbnailUrl:
            item.snippet.thumbnails?.maxres?.url ||
            item.snippet.thumbnails?.high?.url ||
            item.snippet.thumbnails?.medium?.url ||
            item.snippet.thumbnails?.default?.url ||
            "",
          itemCount: item.contentDetails?.itemCount ?? 0,
          publishedAt: item.snippet.publishedAt,
          channelTitle: item.snippet.channelTitle,
        }));
        setPlaylists(playlists);
      } catch (err: unknown) {
        // Type guard to safely access error message
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError(`An unknown error occurred: ${err}`);
        }
      } finally {
        setLoading(false);
      }
    }
    fetchPlaylists();
  }, []);

  return { playlists, loading, error };
}
