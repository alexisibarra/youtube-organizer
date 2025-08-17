"use client";

import Image from "next/image";
import { normalizeSrc } from "./utils/normalizeSrc";

const sidebarLinks = [
  { label: "Home", icon: "icons/home.svg" },
  { label: "Explore", icon: "icons/explore.svg" },
  { label: "Subscriptions", icon: "icons/subscriptions.svg" },
  { label: "Originals", icon: "icons/originals.svg" },
  { label: "Youtube Music", icon: "icons/youtube-music.svg" },
  { label: "Library", icon: "icons/library.svg" },
];

export const YoutubeSidebar = () => {
  return (
    <nav className="sidebar">
      {sidebarLinks.map((link) => (
        <div className="sidebar-link" key={link.label}>
          <Image
            width={24}
            height={24}
            alt={link.label}
            src={normalizeSrc(link.icon)}
          />
          <div>{link.label}</div>
        </div>
      ))}
    </nav>
  );
};
