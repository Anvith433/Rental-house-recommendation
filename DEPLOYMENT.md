# Deploying RentWise

Two parts:

1. [Run it on your own computer](#part-1-run-it-on-your-computer-docker) to check that everything works.
2. [Put it on the internet for free](#part-2-put-it-online-for-free-render--neon) so anyone can open it and create an account.

---

## Part 1: Run it on your computer (Docker)

**You need:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 1. Create your `.env` file

Open a terminal in the project folder (the one that contains `docker-compose.yml`).

Windows (Command Prompt):
```cmd
copy .env.example .env
notepad .env
```

macOS / Linux:
```bash
cp .env.example .env
nano .env
```

### 2. Fill in these four lines, then save

```ini
DJANGO_SECRET_KEY=<a long random string, 50+ characters>
POSTGRES_PASSWORD=<any password for the local database>
SEED_ON_START=true
SEED_DEMO_PASSWORD=<password for the two demo accounts>
```

To generate a secret key:

- With Python: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- Windows PowerShell: `-join ((48..57)+(65..90)+(97..122) | Get-Random -Count 50 | % {[char]$_})`

Leave every other line as it is.

### 3. Start it

```bash
docker compose up --build
```

The first build takes a few minutes. Then open **http://localhost:8080**.

- Anyone using the site can **create their own account** with the "Create account" button.
- Two demo accounts are created on first start, both using your `SEED_DEMO_PASSWORD`:
  - `demo@rentwise.dev`: a normal user
  - `admin@rentwise.dev`: an administrator. Open the Admin dashboard from the account menu.

To stop it, press `Ctrl+C`. Your data is kept in a Docker volume. To delete everything, run `docker compose down -v`.

### Troubleshooting

| Message | Fix |
|---|---|
| `required variable POSTGRES_PASSWORD is missing a value` | There's no `.env` file, or `POSTGRES_PASSWORD` is empty. Repeat steps 1–2. |
| `exec /entrypoint.sh: no such file or directory` | Windows line endings. Run `git pull` (the repo now forces the correct line endings), or re-download the ZIP. |
| `port is already allocated` | Something else is using port 8080. Set `APP_PORT=8090` in `.env` and open http://localhost:8090. |
| Can't sign in to `/django-admin/` | Expected over plain HTTP locally when `SECURE_COOKIES=True`. Keep `SECURE_COOKIES=False` in `.env` for local use. |

---

## Part 2: Put it online for free (Render + Neon)

You get a public link such as `https://rentwise.onrender.com` that anyone can open and sign up on.

| Part | Service | Cost |
|---|---|---|
| Website (React) | Render **static site** | Free |
| API (Django) | Render **free web service** | Free (it sleeps after 15 minutes without visitors; the next visit takes about a minute to wake it) |
| Database | **Neon** PostgreSQL | Free, permanent (Render's free database is deleted after 30 days, so we don't use it) |

You'll need a GitHub account (you already have one), a Render account and a Neon account. Both can be created with "Sign in with GitHub".

### Step 1: Create the database on Neon

1. Go to **https://neon.tech** and sign up.
2. Create a project. Name it `rentwise` and pick the region closest to you, for example *Asia Pacific (Singapore)* if you're in India.
3. On the project dashboard, click **Connect** and copy the **connection string**. It looks like:
   ```
   postgresql://neondb_owner:xxxxxxxx@ep-something-123456.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
   Keep it private: it contains the database password.

### Step 2: Deploy on Render with the blueprint

1. Go to **https://render.com** and sign up with GitHub.
2. Click **New +** → **Blueprint**.
3. Connect your GitHub account if asked, and choose the repository **Rental-house-recommendation**.
4. Render reads `render.yaml` and shows two services: **rentwise-api** and **rentwise**. It asks for the values marked as secret:

   | Variable | What to enter |
   |---|---|
   | `DATABASE_URL` | The Neon connection string from step 1 |
   | `CSRF_TRUSTED_ORIGINS` | `https://rentwise.onrender.com` (your website's address; see the note below) |
   | `SEED_DEMO_PASSWORD` | A password for the demo accounts |

   `DJANGO_SECRET_KEY` is generated for you automatically.
5. Click **Apply** and wait about 5–10 minutes for both services to build.

### Step 3: Check the addresses match

Render names each service after its `name` in `render.yaml`. If a name is already taken by someone else, Render adds a suffix, for example `rentwise-api-ab12.onrender.com`.

1. In the Render dashboard, open **rentwise-api** and note its URL.
2. If it is **not** exactly `https://rentwise-api.onrender.com`, open **rentwise** → **Redirects/Rewrites** and change the three rules that point to `rentwise-api.onrender.com` to your real API URL. You can also edit `render.yaml` and push.
3. If your website URL is not exactly `https://rentwise.onrender.com`, open **rentwise-api** → **Environment** and set `CSRF_TRUSTED_ORIGINS` to your real website URL.

### Step 4: Open your website

Open the **rentwise** URL, for example `https://rentwise.onrender.com`.

- Check `https://<your-site>/api/health/`. It should show `{"status": "ok", "database": "ok"}`. The first request after a sleep can take about a minute.
- Create an account, or sign in as `demo@rentwise.dev` / `admin@rentwise.dev` with your `SEED_DEMO_PASSWORD`.
- Share the link: anyone can sign up.

### After going live

- **Change the demo passwords**, or deactivate the demo accounts in Admin dashboard → Users. If you'd rather start without demo accounts and listings, set `SEED_ON_START` to `false` before the first deploy.
- **Make yourself an admin:** register your own account, then sign in as `admin@rentwise.dev`, open Admin dashboard → Users, and click **Make admin** next to your account.
- **API docs** are at `https://rentwise-api.onrender.com/api/docs/` (the API's own address, not the website's, because the website's security policy blocks the documentation page's external scripts).
- **Updates:** every push to `main` redeploys automatically.

### Free-plan limits to know about

- The API sleeps after 15 minutes without visitors, so the first visit after that waits about a minute.
- 512 MB of memory and 750 free hours a month. One always-on service uses about 730 hours, so there's enough for a demo.
- Rate limits and live engine metrics are kept per process.
