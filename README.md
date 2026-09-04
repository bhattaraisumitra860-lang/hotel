# Hotel 77

Flask hotel website using the real Hotel 77 photographs in `static/uploads`.

## Run locally

Install the packages from `requirements.txt`, set `SECRET_KEY`, and optionally set
`ADMIN_PASSWORD`. Without `DATABASE_URL`, local development stores editable state
in `data.json`.

## Deploy to Vercel

This repository includes `api/index.py` and `vercel.json` for Vercel's Python
runtime. Configure these Vercel environment variables:

- `SECRET_KEY`: long random session secret
- `ADMIN_PASSWORD`: strong password used only on first database seed
- `DATABASE_URL`: managed PostgreSQL connection string with SSL enabled

The first request creates the `hotel_state` table and seeds it once. Subsequent
deployments read the existing record and never reset administrator changes.

If saving from the admin panel returns a storage setup message, add the managed
PostgreSQL connection string as `DATABASE_URL` in the Vercel project settings and
redeploy. Vercel's deployment filesystem cannot store admin edits permanently.

For Supabase, open **Connect**, copy the **Transaction pooler** connection string
(port `6543`), and add it to Vercel as `DATABASE_URL`. Keep the database password
only in Vercel environment variables; never commit the connection string.

Vercel's filesystem is ephemeral. The included seeded photographs are deploy-time
assets; for admin-uploaded photographs, configure object storage and store its
public URL in the gallery data rather than relying on local uploads.

Do not run `npm install` in this repository. It has no `package.json`; use
`py -3 -m pip install -r requirements.txt` for local setup.
