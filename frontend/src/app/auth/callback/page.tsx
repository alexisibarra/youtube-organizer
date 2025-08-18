// Next.js page to handle /auth/callback
// The backend now sets the JWT as an HttpOnly cookie, so the frontend just redirects.
// Learning note: With HttpOnly cookies, the token is not accessible via JS, improving security.

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

const AuthCallbackPage = () => {
  const router = useRouter();

  useEffect(() => {
    // No need to parse token; backend sets HttpOnly cookie
    // Just redirect to main app page
    router.replace("/");
  }, [router]);

  return <p>Processing authentication...</p>;
};

export default AuthCallbackPage;
