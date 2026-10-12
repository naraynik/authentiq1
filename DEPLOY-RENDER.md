# Put AuthentiQ online (free): Render + Neon + Sepolia

When you finish, you will have three public `https://` addresses:

| What | Address |
|---|---|
| Website | https://authentiq-kkw-web.onrender.com |
| Admin portal | https://authentiq-kkw-admin.onrender.com |
| API (+ docs at `/api/docs`) | https://authentiq-kkw-api.onrender.com |

Everything is free. You need about 45 minutes, a Google account and an email address. No command line.

| Service | Used for |
|---|---|
| **GitHub** | Holds the project code. Render builds from it. |
| **Neon** | The PostgreSQL database |
| **MetaMask** + a **Sepolia faucet** | A test wallet with free test ETH that pays for writing products to the blockchain |
| **Render** | Runs the API, website and admin portal |

---

## Step 1: Put the project on GitHub (10 min)

1. Create an account at **https://github.com/signup** (skip if you have one).
2. Install **GitHub Desktop** from **https://desktop.github.com** and sign in with that account.
3. Unzip `authentiq-complete.zip`, for example to `Documents\authentiq`.
4. In GitHub Desktop: **File → Add local repository…** → choose the `authentiq` folder.
   It says the folder is not a repository yet: click **create a repository** → **Create repository**.
5. Click **Publish repository** (top bar). Leaving **Keep this code private** ticked is fine.

`.gitignore` already keeps passwords (`.env`), uploaded Aadhaar files and databases out of GitHub.

## Step 2: Create the database on Neon (5 min)

1. Go to **https://neon.tech** → **Sign up** → **Continue with Google**.
2. Create a project: name `authentiq`, Postgres version 16, region **AWS Asia Pacific (Singapore)** (closest to India).
3. On the project dashboard, click **Connect**, and copy the **connection string**. It looks like
   `postgresql://neondb_owner:xxxx@ep-xxxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`
4. Keep it in Notepad for step 4 (this is a password; do not share it).

The tables are created automatically when the API first starts.

## Step 3: Make a test wallet with free Sepolia ETH (10 min)

The API writes each product to the Sepolia test blockchain. That costs "gas", paid in **test ETH, which is free and has no real value**.

1. Install **MetaMask** in Chrome from **https://metamask.io/download** → **Create a new wallet** → set a password → save the secret phrase somewhere safe.
2. Show test networks: click the network selector (top left) → turn on **Show test networks** → choose **Sepolia**.
3. Copy your wallet address: click the account name at the top (starts with `0x…`).
4. Get free test ETH: open **https://cloud.google.com/application/web3/faucet/ethereum/sepolia**, sign in with Google, paste the address, choose **Sepolia**, click **Receive**.
   After a minute, MetaMask shows about **0.05 SepoliaETH**. That covers the contract plus roughly 20–40 products (it depends on network traffic). You can claim again every day.
   (Other faucets if that one is busy: https://faucets.chain.link/sepolia, https://www.alchemy.com/faucets/ethereum-sepolia)
5. Copy the wallet's private key: account menu (⋮) → **Account details** → **Show private key** → enter your MetaMask password → copy it (starts with `0x`, 66 characters; if it has no `0x`, add `0x` in front).
6. Keep it in Notepad for step 4.

**Use this wallet only for AuthentiQ testing. Never send real money to it**, because its private key is stored on Render.

## Step 4: Deploy on Render (15 min, mostly waiting)

1. Go to **https://render.com** → **Get Started** → **Sign up with GitHub**, and allow Render to see your `authentiq` repository.
2. Click **New** (top right) → **Blueprint**.
3. Choose the `authentiq` repository → **Connect**. Render reads `render.yaml` and lists three services: `authentiq-kkw-api`, `authentiq-kkw-web`, `authentiq-kkw-admin`.
4. It asks for four values:

   | Name | What to paste |
   |---|---|
   | `DATABASE_URL` | the Neon connection string (step 2) |
   | `ADMIN_EMAIL` | the email you will use to log in to the admin portal |
   | `ADMIN_PASSWORD` | a new password: 8+ characters with upper case, lower case, a number and a symbol |
   | `BLOCKCHAIN_PRIVATE_KEY` | the MetaMask private key (step 3) |

5. Click **Apply** (or **Deploy Blueprint**). Render builds all three. The API takes 5–10 minutes the first time.
6. When `authentiq-kkw-api` shows **Live**, open
   **https://authentiq-kkw-api.onrender.com/api/health/blockchain**
   It should say `"contract_accessible": true` and `"chain_id": 11155111`. On its very first start the API deploys the smart contract to Sepolia (about 30 seconds). Its address is saved in the database, so it is not deployed again.

Done. Open the website and the admin portal. Try the flow in README.md, "Try the whole flow". After registering a product, its scan report has a link **See this record on the public blockchain (Etherscan)**.

---

## Good to know

- **The first visit can take about 50 seconds.** Render's free API goes to sleep after 15 minutes without visitors and wakes on the next request. Before a demo, open https://authentiq-kkw-api.onrender.com/api/health once to wake it.
- **Registering a product takes 15–30 seconds**, because the API waits until Sepolia includes the transaction in a block. The button shows "Storing on the blockchain…".
- **AI on the free plan:** the API runs the Random Forest model plus the copied-code and distributor checks. The GNN model needs PyTorch, which does not fit in the free plan's 512 MB of memory. On a paid plan with 2 GB, change the API's build command to `pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements.txt` and the GNN switches on by itself.
- **Camera scanning works on phones**, because Render gives every site `https://`.
- **Updating the site:** change files in the `authentiq` folder, then in GitHub Desktop write a short summary → **Commit to main** → **Push origin**. Render redeploys automatically.
- **Out of test ETH?** Registering fails with a message mentioning "insufficient funds". Claim more from the faucet (step 3.4).
- **Look at the database:** in Neon, open **Tables** (browse rows) or **SQL Editor**.
- **See the logs:** Render → `authentiq-kkw-api` → **Logs**.

## Different addresses?

Web addresses on Render are shared by everyone. If someone already uses `authentiq-kkw-api`, Render adds a few letters (for example `authentiq-kkw-api-x7k2.onrender.com`). Then:

1. Copy the API's real address from its page on Render.
2. In **authentiq-kkw-web** and **authentiq-kkw-admin**: **Environment** → set `VITE_API_URL` to that address → **Save, rebuild and deploy**.

The website and admin portal may get letters added too; the API already accepts `authentiq-kkw-web…` and `authentiq-kkw-admin…` with any suffix. If you rename the services, also update `CORS_ORIGIN_REGEX` on the API.

## Troubleshooting

| You see | Do this |
|---|---|
| Website says "Cannot reach the AuthentiQ server" | The API is waking up: wait a minute and try again. If it persists, check `VITE_API_URL` (above) and the API's **Logs**. |
| API logs: `Refusing to start in production with default …` | Set `ADMIN_PASSWORD` in the API's **Environment** tab. |
| API logs: `could not translate host name` or `password authentication failed` | `DATABASE_URL` is wrong; copy it again from Neon. |
| `/api/health/blockchain` shows `"contract_accessible": false` | The wallet has no test ETH, or the private key is wrong. Fund it (step 3.4), then on Render: API → **Manual Deploy** → **Restart service**. |
| Admin login says "This account is not an admin account" | Use the `ADMIN_EMAIL` / `ADMIN_PASSWORD` from Render, not a manufacturer account. |
