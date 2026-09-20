"""
birthday_wishes.py
------------------
PySpark script that:
  1. Reads employee Name and DOB from a CSV file
  2. Filters employees whose birthday matches today's date (month + day)
  3. Sends a birthday wish to each matching employee via Slack Incoming Webhook

Configuration via environment variables (or .env file for local testing):
  SLACK_WEBHOOK_URL  - Slack Incoming Webhook URL
  CSV_PATH           - Path to the employees CSV file (default: data/employees.csv)
    DEMO_DAILY_BIRTHDAY_NAME - Optional print-only demo name for daily testing
"""

import os
import sys
import json
import requests
import pandas as pd
from datetime import date
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

# ---------------------------------------------------------------------------
# Load config from environment variables
# ---------------------------------------------------------------------------
load_dotenv()  # loads from .env file if present (local dev only)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
DEMO_DAILY_BIRTHDAY_NAME = os.getenv("DEMO_DAILY_BIRTHDAY_NAME", "")
_csv_env = os.getenv("CSV_PATH", "")
CSV_PATH = _csv_env if _csv_env else os.path.join(os.path.dirname(__file__), "..", "data", "employees.csv")



# ---------------------------------------------------------------------------
# Slack helper
# ---------------------------------------------------------------------------
def send_slack_birthday_wish(name: str, webhook_url: str) -> bool:
    """
    Posts a birthday wish message to the configured Slack channel.

    Args:
        name (str): Full name of the birthday person.
        webhook_url (str): Slack Incoming Webhook URL.

    Returns:
        bool: True if message was sent successfully, False otherwise.
    """
    if not webhook_url:
        print(f"[WARN] SLACK_WEBHOOK_URL not set. Skipping Slack message for: {name}")
        return False

    message = {
        "text": (
            f":tada: *Happy Birthday, {name}!* :birthday:\n"
            f"Wishing you a wonderful day filled with joy and celebration!\n"
            f"_— Your Team_ :sparkles:"
        )
    }

    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(message),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200 and response.text == "ok":
            print(f"[SUCCESS] Slack wish sent to: {name}")
            return True
        else:
            print(f"[ERROR] Slack API returned {response.status_code}: {response.text} for: {name}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to send Slack message for {name}: {e}")
        return False


# ---------------------------------------------------------------------------
# PySpark logic
# ---------------------------------------------------------------------------
def create_spark_session() -> SparkSession:
    """Creates and returns a SparkSession."""
    spark = (
        SparkSession.builder
        .appName("BirthdayWishesApp")
        .master("local[*]")          # local mode — all CPU cores
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")  # suppress verbose INFO logs
    return spark


def read_employees(spark: SparkSession, csv_path: str):
    """
    Reads employee CSV into a Spark DataFrame.
    Expected columns: name, dob (YYYY-MM-DD), email (optional)

    On Windows, PySpark's native CSV reader fails with a Hadoop NativeIO
    UnsatisfiedLinkError when winutils.exe is absent. To avoid this, we read
    the CSV using pandas first and then convert to a Spark DataFrame — the
    result is identical for downstream Spark transformations.

    Args:
        spark (SparkSession): Active SparkSession.
        csv_path (str): Absolute or relative path to the CSV file.

    Returns:
        DataFrame: Spark DataFrame with employee records.
    """
    # Read via pandas to bypass Hadoop Windows NativeIO requirement
    pandas_df = pd.read_csv(
        csv_path,
        dtype={"name": str, "dob": str, "email": str},
        keep_default_na=False
    )

    # Ensure required columns exist
    for col in ["name", "dob"]:
        if col not in pandas_df.columns:
            raise ValueError(f"Missing required column '{col}' in CSV: {csv_path}")

    # Add email column if missing
    if "email" not in pandas_df.columns:
        pandas_df["email"] = ""

    # Convert to Spark DataFrame
    df = spark.createDataFrame(pandas_df[["name", "dob", "email"]])
    return df


def filter_todays_birthdays(df):
    """
    Filters the DataFrame to employees whose birthday is today.
    Compares only MONTH and DAY — ignores the birth year.

    Args:
        df (DataFrame): Full employee DataFrame.

    Returns:
        DataFrame: Filtered DataFrame with only today's birthdays.
    """
    today = date.today()
    today_month = today.month
    today_day   = today.day

    birthday_df = df.filter(
        (F.month(F.to_date(F.col("dob"), "yyyy-MM-dd")) == today_month) &
        (F.dayofmonth(F.to_date(F.col("dob"), "yyyy-MM-dd")) == today_day)
    )
    return birthday_df


def run():
    """
    Main entry point for the birthday wishes job.
    Orchestrates: SparkSession → Read CSV → Filter → Send Slack messages.
    """
    today = date.today()
    print("=" * 60)
    print(f"  Birthday Wishes Job — Running for: {today.strftime('%d %B %Y')}")
    print("=" * 60)

    # 1. Start Spark
    spark = create_spark_session()

    # 2. Read CSV
    csv_path = os.path.abspath(CSV_PATH)
    print(f"\n[INFO] Reading CSV from: {csv_path}")
    employees_df = read_employees(spark, csv_path)

    total_count = employees_df.count()
    print(f"[INFO] Total employees loaded: {total_count}")

    if total_count == 0:
        print("[WARN] No employee records found in the CSV. Exiting.")
        spark.stop()
        sys.exit(0)

    # 3. Show a preview of the data (for logs/debugging)
    print("\n[INFO] Sample data:")
    employees_df.show(5, truncate=False)

    # 4. Filter today's birthdays
    birthday_df = filter_todays_birthdays(employees_df)
    birthday_count = birthday_df.count()

    print(f"\n[INFO] Employees with birthday today ({today.strftime('%d-%b')}): {birthday_count}")

    if DEMO_DAILY_BIRTHDAY_NAME:
        print(f"[DEMO] Birthday today: {DEMO_DAILY_BIRTHDAY_NAME} (print-only; no Slack message)")

    if birthday_count == 0:
        print("[INFO] No birthdays today. No messages to send.")
        spark.stop()
        sys.exit(0)

    # 5. Show today's birthday people
    print("\n[INFO] Today's birthday employees:")
    birthday_df.show(truncate=False)

    # 6. Collect results and send Slack messages
    #    .collect() is safe here — birthday list will always be small
    birthday_people = birthday_df.select("name").collect()

    success_count = 0
    fail_count    = 0

    print("\n[INFO] Sending Slack birthday wishes...")
    for row in birthday_people:
        name = row["name"]
        sent = send_slack_birthday_wish(name, SLACK_WEBHOOK_URL)
        if sent:
            success_count += 1
        else:
            fail_count += 1

    # 7. Summary
    print("\n" + "=" * 60)
    print(f"  Job Complete — Sent: {success_count} | Failed: {fail_count}")
    print("=" * 60)

    spark.stop()

    # Exit with non-zero code if any message failed (useful for pipeline alerts)
    if fail_count > 0:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run()
