# Environment Variables

To connect the frontend to your backend API, you must set the `NEXT_PUBLIC_BACKEND_URL` environment variable.

1. Copy `env.template` to `.env` in the `frontend/` directory:

   ```sh
   cp env.template .env
   ```

2. Edit `.env` and set the correct backend URL (default is `http://localhost:8000` for local development):

   ```env
   NEXT_PUBLIC_BACKEND_URL=https://localhost:8000
   ```

3. Restart the Next.js dev server after changing `.env`.

**Note:** The `env.template` file documents all required environment variables for the frontend. Always keep it up to date for other developers.

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## HTTPS for Local Development

To support secure cookies and OAuth2, the frontend must also run on HTTPS locally.

### Generating a Self-Signed Certificate

Run this from the project root:

```sh
sh generate-frontend-cert.sh
```

This will create `localhost.crt` and `localhost.key` in `frontend/certs/`. These are ignored by git.

### Using HTTPS with Next.js

- If running locally (not in Docker), start Next.js with:
  ```sh
  next dev --turbo --https --ssl-cert ./certs/localhost.crt --ssl-key ./certs/localhost.key
  ```
- If using Docker Compose, update the service to use these certs and pass the right flags to Next.js.

### Deployment Note

- For production, you must use certificates from a trusted Certificate Authority (e.g., Let's Encrypt) instead of self-signed certs.
- Update your deployment configuration to use the production certs and keys.
- Never commit private keys or certificates to version control.
