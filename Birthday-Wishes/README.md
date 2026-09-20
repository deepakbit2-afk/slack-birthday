# 🎂 Birthday Wishes — PySpark + Slack

A PySpark job that reads employee names and dates of birth from a CSV file,
detects whose birthday is **today**, and sends them a personalised 🎉 wish
via **Slack Incoming Webhook**.

---

## 📁 Project Structure

```
Birthday-Wishes/
├── data/
│   └── employees.csv          # Employee data (name, dob, email)
├── src/
│   └── birthday_wishes.py     # Main PySpark script
├── watch-and-push.py          # Optional local change watcher
├── requirements.txt           # Python dependencies
├── .env.example               # Template for local secrets
└── README.md
```

---

## ⚙️ Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.8 – 3.11 |
| Java (JDK) | 11 or 17 (required by PySpark) |
| PySpark | 3.5.1 |

### Install Java (if not already installed)
- Download from: https://adoptium.net/
- Verify: `java -version`

### Set JAVA_HOME (Windows)
```powershell
# Example — adjust path to your JDK install location
[System.Environment]::SetEnvironmentVariable("JAVA_HOME","C:\Program Files\Eclipse Adoptium\jdk-11.0.21.9-hotspot","Machine")
```

---

## 🚀 Local Setup & Run

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure your Slack Webhook
```bash
# Copy the template
cp .env.example .env

# Edit .env and set your actual Slack Webhook URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

> **How to get a Slack Webhook URL:**
> 1. Go to https://api.slack.com/apps → Create App → "From scratch"
> 2. Enable **Incoming Webhooks**
> 3. Click **Add New Webhook to Workspace** → choose a channel
> 4. Copy the Webhook URL

### 3. Edit the CSV (optional)
Open `data/employees.csv` and add your employee records:
```csv
name,dob,email
Your Name,YYYY-MM-DD,your@email.com
```

### 4. Run the script
```bash
python src/birthday_wishes.py
```

### 5. Automatically push local changes to GitHub

After installing the dependencies, start the optional local watcher from the
`Birthday-Wishes` directory:

```powershell
python watch-and-push.py
```

The watcher waits 10 seconds after the last file change, then stages all
repository changes, creates an `Automatic local sync` commit, and pushes the
current branch to `origin`. Change the delay when needed:

```powershell
python watch-and-push.py --debounce 5
```

Git authentication must already work with `git push origin main`. Do not keep
webhook URLs, PATs, temporary documents, or generated files in the repository;
add them to `.gitignore` before enabling automatic commits. Press `Ctrl+C` to
stop the watcher. Windows Task Scheduler can start this command at logon.

---

## 📊 How It Works

1. **SparkSession** starts in local mode (`local[*]`) — no cluster needed
2. Reads `employees.csv` into a Spark DataFrame
3. Filters rows where `MONTH(dob) = today's month` AND `DAY(dob) = today's day`
4. For each birthday person → POSTs a JSON message to your Slack channel via Incoming Webhook

---

## 📝 CSV Format

```csv
name,dob,email
John Smith,1990-09-01,john.smith@example.com
```

| Column | Type | Required | Format |
|--------|------|----------|--------|
| `name` | string | ✅ Yes | Full name |
| `dob`  | string | ✅ Yes | `YYYY-MM-DD` |
| `email`| string | ❌ No  | Optional |

---

## ☁️ Azure DevOps Automation

The repository includes `azure-pipelines.yml`, which runs the job every day at
03:00 UTC on a Microsoft-hosted Ubuntu agent. Pushes and pull requests do not
run the job automatically.

The separate `azure-pipelines-validation.yml` pipeline is for CI/PR validation.
It runs on changes to `main` and on pull requests targeting `main`; it only
installs dependencies and checks Python syntax, so it never sends a Slack wish.

### One-time setup

1. Push this repository to Azure Repos or GitHub.
2. In Azure DevOps, open **Pipelines** → **New pipeline**, select the repository,
  choose **Existing Azure Pipelines YAML file**, and select
  `/azure-pipelines.yml`.
3. Create a pipeline variable named `SLACK_WEBHOOK_URL`, paste in the Slack
  Incoming Webhook URL, and enable **Keep this value secret**.
4. Run the pipeline once manually to confirm the connection. After that, the
  scheduled run sends wishes automatically.

Create a second Azure DevOps pipeline using
`/azure-pipelines-validation.yml` for the validation checks. If your repository
is already hosted in Azure Repos, no Git mirroring is required: both pipelines
read the same repository. For Azure Repos pull requests, enable this pipeline
as a branch policy under **Repos** → **Branches** → `main` → **Branch policies**
→ **Build validation**. This is what blocks a PR when validation fails.

If your source repository is GitHub, connect it from **Project Settings** →
**Service connections** → **GitHub**, then create the pipeline from the GitHub
repository. In that setup, GitHub changes trigger the validation pipeline
directly; copying every commit into Azure Repos is not necessary.

The free Azure DevOps tier includes Microsoft-hosted agent time subject to its
current free parallel-job/minute quota. This job uses one short hosted run per
day; dependency installation is included in each run.

To change the run time, edit the cron expression in `azure-pipelines.yml`.
Azure DevOps interprets it as UTC.

### Windows self-hosted agent

The pipeline can run on your Windows computer without hosted parallelism. The
YAML uses the `Default` self-hosted agent pool and PowerShell steps. Set it up
once in Azure DevOps:

1. Open **Organization settings** → **Agent pools** → **Default** → **New agent**.
2. Select **Windows**, download the agent, and extract it to a folder such as
  `C:\agent`.
3. Open PowerShell as Administrator and run the downloaded `config.cmd`.
4. Enter the organization URL, choose the `Default` pool, and authenticate
  with a PAT that has **Agent Pools: Read & manage** permission.
5. When asked whether to run as a service, answer `Y`, then start the service.
6. Confirm the agent is **Online** under **Organization settings** → **Agent
  pools** → **Default** → **Agents**.

Install Python 3.11+ and Java 11, 17, or 21 on that computer, and verify:

```powershell
python --version
java -version
```

The computer must be powered on and connected to the internet at 03:00 UTC.
After the agent is online, create or edit the Azure pipeline using
`/Birthday-Wishes/azure-pipelines.yml` and run it once manually.

The pipeline currently prints `Energetic Demo User` every day as a print-only
demo birthday. It does not send a Slack message for that demo name. Remove the
`DEMO_DAILY_BIRTHDAY_NAME` line from the YAML when you want only real employee
birthdays from the CSV.

### Repository synchronization

The local `watch-and-push.py` utility can push changes to GitHub automatically.
The GitHub Actions workflow then mirrors GitHub to the Azure Repos repository
`Pipelines`. The sync direction is intentionally one-way:
`local machine -> GitHub -> Azure Repos`.

## 🔐 Security Notes

- **Never commit `.env`** to version control — it contains your Slack webhook URL
- `.env.example` is safe to commit (it has no real secrets)
- For production pipelines, store secrets in Azure DevOps Variable Groups or Azure Key Vault

---

## 🧪 Testing

To test without a real Slack webhook, just leave `SLACK_WEBHOOK_URL` blank.
The script will log a warning and skip sending but still show you which birthdays were detected.

To force a birthday match today, temporarily set a DOB in `employees.csv` to today's date in `MM-DD` format.

---

## 📅 Sample Output

```
============================================================
  Birthday Wishes Job — Running for: 01 September 2026
============================================================

[INFO] Reading CSV from: C:\...\data\employees.csv
[INFO] Total employees loaded: 8

[INFO] Sample data:
+--------------+----------+-------------------------+
|name          |dob       |email                    |
+--------------+----------+-------------------------+
|John Smith    |1990-09-01|john.smith@example.com   |
|Jane Doe      |1985-03-15|jane.doe@example.com     |
...

[INFO] Employees with birthday today (01-Sep): 3
[INFO] Today's birthday employees:
+--------------+----------+---------------------------+
|name          |dob       |email                      |
+--------------+----------+---------------------------+
|John Smith    |1990-09-01|john.smith@example.com     |
|Ravi Singh    |1992-09-01|ravi.singh@example.com     |
|Priya Sharma  |1993-09-01|priya.sharma@example.com   |
+--------------+----------+---------------------------+

[INFO] Sending Slack birthday wishes...
[SUCCESS] Slack wish sent to: John Smith
[SUCCESS] Slack wish sent to: Ravi Singh
[SUCCESS] Slack wish sent to: Priya Sharma

============================================================
  Job Complete — Sent: 3 | Failed: 0
============================================================
```
