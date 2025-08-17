"use client";

import Image from "next/image";
import { normalizeSrc } from "./utils/normalizeSrc";

export const YoutubeHeader = () => {
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
          {/*
            TODO: Decide if we want a notification system.
            If so, make this section dynamic to reflect the user's real notification count and details.
            If not, consider removing this section entirely.
            This will require a product/design decision and, if kept, integration with backend/user data.
          */}
          <div className="notifications-count">3</div>

          <div className="tooltip">Notifications</div>
        </div>

        {/*
          TODO: make this dynamic
          We want to show a dynamic image here that reflects the current logged in user.
          In the future, this should display the user's profile picture if authenticated,
          or a default avatar if not logged in. This will require integrating authentication
          and passing user data to the header component.
        */}
        <Image
          height={32}
          width={32}
          alt="current user picture"
          className="current-user-picture-icon"
          src={normalizeSrc("channel-pictures/my-channel.jpg")}
        />
      </div>
    </header>
  );
};
