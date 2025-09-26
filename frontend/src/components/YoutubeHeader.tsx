"use client";

import Image from "next/image";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faSearch,
  faMicrophone,
  faUpload,
  faBell,
  faTh,
  faBars,
} from "@fortawesome/free-solid-svg-icons";
import { faYoutube, faGoogle } from "@fortawesome/free-brands-svg-icons";
import { useEffect, useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

const handleGoogleLogin = async () => {
  try {
    // Call the backend endpoint that returns the Google OAuth2 URL
    const res = await fetch(`${BACKEND_URL}/api/auth/google/`);

    if (!res.ok) {
      throw new Error("Failed to fetch auth URL");
    }

    const data = await res.json();

    if (!data.auth_url) throw new Error("No auth_url in response");

    // Redirect the user to the Google OAuth2 URL
    window.location.href = data.auth_url;
  } catch (err) {
    console.error(err);

    // Optionally, show an error to the user
    alert(
      "Error starting authentication: " +
        (err instanceof Error ? err.message : String(err))
    );
  }
};

// --- Session Management: Check if user is logged in ---
// Learning note: We use useState to track user info, and useEffect to check login status on mount.
export const YoutubeHeader = () => {
  // Learning note: Add 'profile_picture' as optional to match backend user object
  const [user, setUser] = useState<null | {
    username: string;
    email: string;
    profile_picture?: string;
  }>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Call backend to check if user is logged in
    fetch(`${BACKEND_URL}/api/auth/me/`, {
      credentials: "include",
    })
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error("Not authenticated");
      })
      .then((data) => {
        setUser(data);
        setLoading(false);
      })
      .catch(() => {
        setUser(null);
        setLoading(false);
      });
  }, []);

  return (
    <header className="header">
      <div className="left-section">
        <FontAwesomeIcon icon={faBars} className="hamburger-logo" size="2x" />

        <FontAwesomeIcon icon={faYoutube} className="text-red-600" size="2x" />

        <h1 className="logo-text font-sans font-bold text-black">
          YouTube Organizer
        </h1>
      </div>

      <div className="middle-section">
        <input className="search-bar" type="text" placeholder="Search" />

        <button className="search-button">
          <span className="search-icon">
            <FontAwesomeIcon icon={faSearch} size="lg" />
          </span>
          <div className="tooltip">Search</div>
        </button>

        <button className="voice-search-button">
          <span className="voice-search-icon">
            <FontAwesomeIcon icon={faMicrophone} size="lg" />
          </span>
          <div className="tooltip">Search with your voice</div>
        </button>
      </div>

      <div className="right-section">
        <div className="upload-icon-container mr-3">
          <span className="upload-icon">
            <FontAwesomeIcon icon={faUpload} size="lg" />
          </span>
          <div className="tooltip">Create</div>
        </div>

        <div className="youtube-apps-icon-container mr-3">
          <span className="youtube-apps-icon">
            <FontAwesomeIcon icon={faTh} size="lg" />
          </span>
          <div className="tooltip">Youtube apps</div>
        </div>

        <div className="notifications-icon-container mr-3">
          <span className="notifications-icon">
            <FontAwesomeIcon icon={faBell} size="lg" />
          </span>
          <div className="notifications-count">3</div>
          <div className="tooltip">Notifications</div>
        </div>

        {/* --- AUTH UI --- */}
        {loading ? null : user ? (
          // Show real user info: avatar (if available), username/email, fallback to first letter
          <div
            className="avatar-tooltip-wrapper"
            style={{
              position: "relative",
              display: "flex",
              alignItems: "center",
            }}
          >
            <div
              className="profile-picture-container"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                cursor: "pointer",
              }}
            >
              {user.profile_picture ? (
                <Image
                  height={32}
                  width={32}
                  alt={
                    user.username
                      ? `Avatar for ${user.username}`
                      : "User avatar"
                  }
                  className="current-user-picture-icon"
                  src={user.profile_picture}
                />
              ) : (
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    background: "#ccc",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: "bold",
                    fontSize: 18,
                    color: "#333",
                  }}
                  aria-label={user.username}
                >
                  {user.username ? user.username[0].toUpperCase() : "?"}
                </div>
              )}
            </div>
            {/* Tooltip popup for username/email */}
            <span
              style={{
                visibility: "hidden",
                opacity: 0,
                position: "absolute",
                left: "110%",
                top: "50%",
                transform: "translateY(-50%)",
                background: "#222",
                color: "#fff",
                padding: "6px 12px",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: 500,
                whiteSpace: "nowrap",
                zIndex: 10,
                transition: "opacity 0.2s",
                pointerEvents: "none",
              }}
              className="user-tooltip"
            >
              {user.username}
              <br />
              <span style={{ color: "#aaa", fontSize: 12 }}>{user.email}</span>
            </span>
          </div>
        ) : (
          // Show sign in button if not logged in
          <div>
            <button
              onClick={handleGoogleLogin}
              className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-1 px-4 rounded shadow mr-3 mb-1"
            >
              <span style={{ marginRight: 8 }}>
                <FontAwesomeIcon icon={faGoogle} size="lg" />
              </span>
              Sign in
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
// End of YoutubeHeader component
