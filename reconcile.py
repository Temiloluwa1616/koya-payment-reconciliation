#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py

Rules (from the README):
  * Skip lines that are not valid JSON (the export has truncated lines).
  * Skip events that have no txn_id.
  * A payment can be attempted several times under the same txn_id. Only the
    latest attempt (by ts, not by line order) counts.
  * A payment is collected only if its latest attempt is "success".
  * Amounts are sometimes strings with thousands separators ("4,804.15").
"""
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def parse_ts(value):
    # ts is UTC, e.g. "2026-09-21T15:30:26Z"
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def parse_amount(value):
    # Go through str() so floats are not carried as binary approximations.
    return Decimal(str(value).replace(",", "").strip())


latest = {}  # txn_id -> latest event

with open("payments.jsonl", encoding="utf-8") as f:
    for line in f:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue  # truncated / unreadable line
        if not isinstance(event, dict):
            continue
        txn_id = event.get("txn_id")
        if not txn_id:
            continue  # no transaction id, cannot be attributed
        previous = latest.get(txn_id)
        if previous is None or parse_ts(event["ts"]) > parse_ts(previous["ts"]):
            latest[txn_id] = event

total = Decimal("0")
count = 0
for event in latest.values():
    if event["status"] == "success":
        total += parse_amount(event["amount"])
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{int(total.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}")