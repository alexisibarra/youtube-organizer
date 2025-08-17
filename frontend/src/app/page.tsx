"use client";
import { YoutubeTemplate } from "../components/YoutubeTemplate";

export default function Home() {
  // const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

  // const handleSignIn = async () => {
  //   try {
  //     // Call the backend endpoint that returns the Google OAuth2 URL
  //     const res = await fetch(`${BACKEND_URL}/api/auth/google/`);

  //     if (!res.ok) {
  //       throw new Error("Failed to fetch auth URL");
  //     }
  //     const data = await res.json();
  //     if (!data.auth_url) throw new Error("No auth_url in response");
  //     // Redirect the user to the Google OAuth2 URL
  //     window.location.href = data.auth_url;
  //   } catch (err) {
  //     console.error({ err });

  //     // Optionally, show an error to the user
  //     alert(
  //       "Error starting authentication: " +
  //         (err instanceof Error ? err.message : String(err))
  //     );
  //   }
  // };

  // <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
  {
    /* <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start"> */
  }
  {
    /* Sign in with Google button */
  }
  {
    /* <button
          onClick={handleSignIn}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded shadow mb-4"
        >
          Sign in with Google
        </button> */
  }

  {
    /* </main> */
  }
  {
    /*  */
  }
  return <YoutubeTemplate />;
  // </div>
}
