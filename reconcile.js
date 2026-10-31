// Payment reconciliation.
//
// Reads payments.jsonl and works out how much money we actually collected.
// Run:  node reconcile.js
//
// Rules (from the README):
//   * Skip lines that are not valid JSON (the export has truncated lines).
//   * Skip events that have no txn_id.
//   * Only the latest attempt per txn_id counts, chosen by ts and not by line order.
//   * A payment is collected only if its latest attempt is "success".
//   * Amounts are sometimes strings with thousands separators ("4,804.15").

const fs = require("fs");

// Work in kobo (integers) so adding 22k amounts does not pick up float error.
function toKobo(value) {
  const cleaned = String(value).replace(/,/g, "").trim();
  return Math.round(Number(cleaned) * 100);
}

const latest = new Map(); // txn_id -> latest event

const lines = fs.readFileSync("payments.jsonl", "utf8").split("\n").filter((l) => l.trim().length > 0);
for (const line of lines) {
  let event;
  try {
    event = JSON.parse(line);
  } catch {
    continue; // truncated / unreadable line
  }
  if (event === null || typeof event !== "object" || Array.isArray(event)) continue;
  if (!event.txn_id) continue; // no transaction id, cannot be attributed

  const previous = latest.get(event.txn_id);
  if (!previous || Date.parse(event.ts) > Date.parse(previous.ts)) {
    latest.set(event.txn_id, event);
  }
}

let totalKobo = 0;
let count = 0;
for (const event of latest.values()) {
  if (event.status === "success") {
    totalKobo += toKobo(event.amount);
    count += 1;
  }
}

const expected = parseInt(fs.readFileSync("expected.txt", "utf8").trim(), 10);

if (count !== expected) {
  console.log(`Check failed: counted ${count} successful payments, expected ${expected}.`);
  console.log("Something in the data isn't being handled the way the README describes.");
} else {
  console.log(`Check passed: ${count} successful payments.`);
  console.log(`Your code: KOYA-${Math.round(totalKobo / 100)}`);
}