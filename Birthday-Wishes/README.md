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

### Create and push the Azure Repos repository

The script `push-to-azure.ps1` creates the Azure Repos repository (and can also
create the project), adds it as the `azure` Git remote, commits local changes,
and pushes the current branch. It does not remove or change the existing
GitHub `origin` remote.

First authenticate with Azure CLI:

```powershell
az login
az extension add --name azure-devops
az devops login --organization https://dev.azure.com/Deepaksingh0643
```

Run this once from the project directory only if the Azure repository still
needs its initial code push. The script is already configured for your Azure
DevOps project and repository named `Pipelines`:

```powershell
.\push-to-azure.ps1
```

`-CreateProject` is optional and requires permission to create projects. The
`Pipelines` project already exists, so the switch is not needed. The first
`git push` may request Azure DevOps credentials; use a Personal Access Token
with Code read/write permission, or let Git Credential Manager store them.

### Continuous GitHub-to-Azure sync from PowerShell

If new commits are pushed to the existing GitHub `origin` repository and you
want a local PowerShell process to mirror them into Azure Repos, run:

```powershell
.\watch-and-sync-to-azure.ps1
```

It checks for changes every 60 seconds and syncs all branches and tags. Keep
the PowerShell window open; press `Ctrl+C` to stop it. To change the interval:

```powershell
.\watch-and-sync-to-azure.ps1 -IntervalSeconds 300
```

This watcher requires that `push-to-azure.ps1` has already created and
authenticated the `azure` remote. For a server-side solution that does not
depend on your Windows PC being on, use a GitHub Actions workflow or an Azure
DevOps GitHub connection instead.

### GitHub Actions sync (recommended)

The repository also includes `.github/workflows/sync-to-azure.yml`. It runs on
every GitHub push and sends that branch and its tags to the Azure Repos project
`Pipelines`. No local watcher or extra software is required.

Configure it once in GitHub:

1. In Azure DevOps, create a Personal Access Token with **Code: Read & write**
  permission. Copy it immediately; Azure will not show it again.
2. In GitHub, open **Settings** → **Secrets and variables** → **Actions** →
  **New repository secret**.
3. Set the secret name to `AZURE_DEVOPS_PAT` and paste the PAT as its value.
4. Push a commit to GitHub. Open the repository's **Actions** tab and confirm
  the **Sync GitHub to Azure Repos** workflow succeeds.

The workflow uses the existing Azure organization `Deepaksingh0643`, project
`Pipelines`, and repository `Pipelines`. A Service Principal and local
software installation are not required for this GitHub-to-Azure sync.
After the workflow file and `AZURE_DEVOPS_PAT` secret are configured, do not
run the PowerShell push command for normal updates. A regular `git push origin`
automatically starts the GitHub Actions sync.

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
