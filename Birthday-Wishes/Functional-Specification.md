# Functional Specification

## 1. Document Control

| Item | Value |
|---|---|
| System | Birthday Wishes Automation |
| Version | 1.0 |
| Status | Current implementation specification |
| Primary repository | Birthday-Wishes |
| Last updated | 2026-09-13 |

## 2. Purpose

The Birthday Wishes Automation system identifies employees whose birthday is
on the current calendar date and sends a personalized birthday message to a
configured Slack channel. The job can run locally or automatically through an
Azure DevOps pipeline.

## 3. Scope

### In scope

- Read employee records from a CSV file.
- Validate the required CSV columns.
- Match birthdays by month and day, ignoring birth year.
- Print job progress, matching employees, and a completion summary.
- Send one Slack Incoming Webhook message per matching employee.
- Run the job on a daily Azure DevOps schedule.
- Support a Windows self-hosted Azure DevOps agent.
- Support print-only demo output for pipeline testing.

### Out of scope

- Sending email or direct Slack messages to individual users.
- Updating employee records from Slack or Azure DevOps.
- Persistent database storage.
- Employee authentication or user interface.
- Automatic retry of an individual failed Slack request.

## 4. Users and External Systems

| Actor/System | Responsibility |
|---|---|
| Scheduler | Starts the job once per day through Azure DevOps. |
| Job operator | Maintains the CSV and pipeline secret. |
| CSV file | Provides employee name and date-of-birth data. |
| Slack Incoming Webhook | Receives birthday messages. |
| Azure DevOps | Stores the repository and executes the scheduled pipeline. |
| Windows self-hosted agent | Provides the local execution environment when hosted parallelism is unavailable. |

## 5. Functional Requirements

### FR-01: Configuration

The system shall read configuration from environment variables. It shall support:

- `SLACK_WEBHOOK_URL`: Slack Incoming Webhook URL. Required for message delivery.
- `CSV_PATH`: Optional CSV path. If omitted, use `data/employees.csv`.
- `DEMO_DAILY_BIRTHDAY_NAME`: Optional print-only demo name. It shall never be sent to Slack.

For local execution, a `.env` file may provide these values. Pipeline secrets
shall be stored as secret variables and shall not be committed to Git.

### FR-02: Input file

The default input file shall be `data/employees.csv` and shall use this format:

```csv
name,dob,email
John Smith,1990-09-01,john.smith@example.com
```

Required columns are `name` and `dob`. The `email` column is optional and is
not used for Slack delivery.

### FR-03: Input validation

The system shall fail with a clear error if the CSV cannot be read or if a
required column is missing. An empty CSV shall produce a warning and exit
successfully without sending a message.

### FR-04: Birthday matching

The system shall parse `dob` values in `YYYY-MM-DD` format and compare only
month and day with the current system date. The birth year shall be ignored.

### FR-05: Message delivery

For every matching employee, the system shall send one JSON POST request to the
configured Slack webhook. The message shall include the employee name and a
birthday greeting. A request timeout shall be used to prevent indefinite hangs.

If the webhook is missing, the system shall print a warning and skip delivery.
If Slack returns a non-success response or the request fails, the employee shall
be counted as failed.

### FR-06: Exit status

The job shall exit with status 0 when processing completes with no failed Slack
messages. It shall exit with status 1 when one or more Slack messages fail.

No-birthday and empty-input cases shall exit successfully.

### FR-07: Logging

The job shall log:

- Execution date.
- CSV path.
- Total records loaded.
- Matching birthday count.
- Matching employee preview.
- Sent and failed message totals.
- Warnings and errors relevant to operation.

Secrets and webhook values shall never be printed.

### FR-08: Demo mode

When `DEMO_DAILY_BIRTHDAY_NAME` is configured, the job shall print a demo
birthday line for daily verification. Demo mode shall not add a fake employee
to the CSV and shall not send a Slack message for the demo name.

## 6. Operational Workflow

1. Azure DevOps checks out the repository.
2. The Windows self-hosted agent starts the job from the imported project folder.
3. Python dependencies are installed from `requirements.txt`.
4. The job reads the CSV and calculates today's birthdays.
5. Real matching employees receive Slack messages.
6. Logs and exit status are published to the Azure pipeline run.

The current pipeline is scheduled for 03:00 UTC and has push and pull-request
triggers disabled. The Windows computer must be powered on, online, and have
the Azure agent online at the scheduled time.

## 7. Technical Requirements

- Windows self-hosted Azure DevOps agent in the `Default` pool.
- Python 3.11 or a compatible supported version.
- Java 11, 17, or 21 for PySpark.
- Internet access to Azure DevOps and Slack.
- Python packages listed in `requirements.txt`.
- Azure pipeline variable `SLACK_WEBHOOK_URL`, marked secret.

## 8. Security Requirements

- Slack webhook URLs shall be treated as credentials.
- Azure DevOps PATs shall be used only for their intended operation and shall
  not be stored in source code.
- `.env` shall remain ignored by Git.
- Secrets shall be configured through Azure DevOps secret variables or an
  approved secret store.
- Exposed or leaked webhook URLs shall be revoked and replaced immediately.
- Pipeline logs shall not print secret values.

## 9. Error Handling

| Condition | Expected behavior |
|---|---|
| CSV missing | Job fails with a file/read error. |
| Required CSV column missing | Job fails with a validation error. |
| Empty CSV | Warning is logged; job exits successfully. |
| No birthday today | Informational message; no Slack request; success exit. |
| Webhook missing | Warning per matching employee; failed delivery count; nonzero exit if matches exist. |
| Slack timeout/network failure | Error is logged; employee counted as failed; job exits nonzero. |
| Azure agent offline | Pipeline waits or fails according to Azure DevOps job timeout; no local job runs. |
| Dependency installation failure | Pipeline fails before the birthday job starts. |

## 10. Acceptance Criteria

- Given a valid CSV containing an employee with today's month and day, the job
  identifies that employee.
- Given a valid Slack webhook, one birthday message is sent per matching
  employee.
- Given no matching birthdays, no Slack request is made and the job succeeds.
- Given a missing webhook and a matching employee, the job reports the skipped
  delivery and returns a failure status.
- Given `DEMO_DAILY_BIRTHDAY_NAME`, the name is printed but no Slack message is
  sent for that demo value.
- Given an online Windows self-hosted agent, Azure runs the YAML steps from the
  `Birthday-Wishes` folder.
- Given the configured daily schedule and an online agent, the job starts at
  the scheduled UTC time.
- No secret appears in source control or pipeline logs.

## 11. Traceability

| Requirement area | Implementation location |
|---|---|
| Job orchestration and matching | `src/birthday_wishes.py` |
| Employee data | `data/employees.csv` |
| Python dependencies | `requirements.txt` |
| Azure daily execution | `azure-pipelines.yml` |
| CI and PR validation | `azure-pipelines-validation.yml` |
| Azure repository source | Azure Repos repository `Pipelines` |

## 12. Technical Component Specification

| Component | Technical responsibility | Inputs | Outputs/side effects |
|---|---|---|---|
| `src/birthday_wishes.py` | Creates Spark, loads pandas CSV data, filters month/day, posts Slack messages, and controls exit status. | Environment variables and CSV file. | Console logs, Slack POST requests, process exit code. |
| `data/employees.csv` | Stores employee records used for birthday matching. | Maintained CSV rows. | Birthday candidates for the job. |
| `requirements.txt` | Defines Python runtime dependencies: PySpark, requests, pandas, and python-dotenv. | Pip installation. | Reproducible Python environment. |
| `azure-pipelines.yml` | Defines the daily schedule, self-hosted pool, dependency installation, secret mapping, and job execution. | Azure variables and checked-out repository. | Azure pipeline run and logs. |
| `azure-pipelines-validation.yml` | Performs CI checks without Slack delivery. | Repository changes. | Syntax validation result. |

### Runtime sequence

1. Azure checks out the repository into the agent workspace.
2. The Windows agent runs PowerShell from the `Birthday-Wishes` directory.
3. Python dependencies are installed from `requirements.txt`.
4. `birthday_wishes.py` reads the CSV and creates the birthday DataFrame.
5. Matching real employees are posted to Slack through the webhook.
6. The process exits with success or failure, which determines the pipeline result.

### Required versus optional implementation

The minimum production path is `src/birthday_wishes.py`,
`data/employees.csv`, `requirements.txt`, `azure-pipelines.yml`, a configured
Windows agent, and the secret `SLACK_WEBHOOK_URL`. Repository synchronization
repository synchronization utilities are not required for the Azure birthday
job once the Azure repository contains the source code.
