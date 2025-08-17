"use client";

import Image from "next/image";
import { normalizeSrc } from "./utils/normalizeSrc";

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
    console.error({ err });

    // Optionally, show an error to the user
    alert(
      "Error starting authentication: " +
        (err instanceof Error ? err.message : String(err))
    );
  }
};

export const YoutubeHeader = () => {
  // TODO: Implement authentication state tracking
  // In a real app, you would use Redux or React Context to track if the user is authenticated.
  // For now, we'll just always show the login button for demonstration.

  return (
    <header className="header">
      <div className="left-section">
        <Image
          alt="hamburger menu"
          className="hamburger-logo"
          src={normalizeSrc("/icons/hamburger-menu.svg")}
          width={24}
          height={24}
        />

        <Image
          className="youtube-logo"
          src={normalizeSrc("/icons/youtube-logo.svg")}
          alt="YouTube Logo"
          width={100}
          height={30}
        />
      </div>

      <div className="middle-section">
        <input className="search-bar" type="text" placeholder="Search" />

        <button className="search-button">
          <Image
            height={25}
            width={25}
            alt="voice search icon"
            className="search-icon"
            src={normalizeSrc("icons/search.svg")}
          />
          <div className="tooltip">Search</div>
        </button>

        <button className="voice-search-button">
          <Image
            height={24}
            width={24}
            alt="voice search icon"
            className="voice-search-icon"
            src={normalizeSrc("icons/voice-search-icon.svg")}
          />

          <div className="tooltip">Search with your voice</div>
        </button>
      </div>

      <div className="right-section">
        <div className="upload-icon-container">
          <Image
            height={24}
            width={24}
            alt="upload icon"
            className="upload-icon"
            src={normalizeSrc("icons/upload.svg")}
          />
          <div className="tooltip">Create</div>
        </div>

        <div className="youtube-apps-icon-container">
          <Image
            height={24}
            width={24}
            alt="youtube apps icon"
            className="youtube-apps-icon"
            src={normalizeSrc("icons/youtube-apps.svg")}
          />
          <div className="tooltip">Youtube apps</div>
        </div>

        <div className="notifications-icon-container">
          <Image
            height={24}
            width={24}
            alt="notifications icon"
            className="notifications-icon"
            src={normalizeSrc("icons/notifications.svg")}
          />
          <div className="notifications-count">3</div>
          <div className="tooltip">Notifications</div>
        </div>

        <div className="profile-picture-container">
          <Image
            height={32}
            width={32}
            alt="current user picture"
            className="current-user-picture-icon"
            src={normalizeSrc("channel-pictures/my-channel.jpg")}
          />
        </div>

        {/* --- AUTH BUTTON --- */}
        <div style={{ marginLeft: "auto", paddingRight: 16 }}>
          <button
            onClick={handleGoogleLogin}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded shadow mb-4"
          >
            <img
              src="/icons/google.svg"
              alt="Google"
              style={{ width: 20, height: 20, marginRight: 8 }}
            />
            Sign in with Google
          </button>
        </div>
      </div>
    </header>
  );
};
// End of YoutubeHeader component
