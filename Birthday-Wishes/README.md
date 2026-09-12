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

### One-time setup

1. Push this repository to Azure Repos or GitHub.
2. In Azure DevOps, open **Pipelines** → **New pipeline**, select the repository,
  choose **Existing Azure Pipelines YAML file**, and select
  `/azure-pipelines.yml`.
3. Create a pipeline variable named `SLACK_WEBHOOK_URL`, paste in the Slack
  Incoming Webhook URL, and enable **Keep this value secret**.
4. Run the pipeline once manually to confirm the connection. After that, the
  scheduled run sends wishes automatically.

The free Azure DevOps tier includes Microsoft-hosted agent time subject to its
current free parallel-job/minute quota. This job uses one short hosted run per
day; dependency installation is included in each run.

To change the run time, edit the cron expression in `azure-pipelines.yml`.
Azure DevOps interprets it as UTC.

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
