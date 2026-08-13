"""Generate a synthetic orders CSV in the same shape the real (excluded) sample
data had — used as the demo fixture and to keep the repo reproducible without
any real customer data. Re-run with a fixed seed for stable output.

Usage: python sample/generate_synthetic_orders.py
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

SEED = 20260813
fake = Faker("sv_SE")
Faker.seed(SEED)
random.seed(SEED)

LOCATIONS = ["Malmö", "Helsingborg"]
TREATMENTS = [
    "chiropody 60 min x1",
    "deep therapy massage 60 min",
    "spa body treatment detox & recovery 60 min",
    "foot massage 45 min x1",
    "aromavedic body massage 60 min x1",
    "flexi massage (focus on neck, shoulders, back) 45 min x1",
    "yoga massage 60 min x1",
    "head massage 45 min x1",
    "swedish massage 60 min x1",
    "foot care wellness package 75 min x1",
    "foot care wellness spa 60 min x1",
]
OUTPUT_PATH = Path(__file__).resolve().parent / "sample_orders.csv"


def fake_order_number(batch: int) -> str:
    return f"b:bfy{9000 + batch}-{random.randint(1000, 99999)}"


def fake_office_email(full_name: str) -> str:
    local = full_name.lower().replace(" ", ".")
    return f"{local}@{fake.domain_name()}"


def main(row_count: int = 60) -> None:
    rows = []
    current_date = date(2026, 1, 22)
    batch = 500

    for _ in range(row_count):
        full_name = fake.name()
        location = random.choice(LOCATIONS)
        is_cancel = random.random() < 0.05

        rows.append(
            {
                "date": current_date.isoformat(),
                "full_name": full_name,
                "order_number": fake_order_number(batch),
                "is_cancel": is_cancel,
                "office_email": fake_office_email(full_name),
                "private_email": fake.free_email() if random.random() > 0.15 else "",
                "treatment_selected": random.choice(TREATMENTS),
                "location": location,
            }
        )
        batch -= random.randint(1, 3)
        if random.random() < 0.6:
            current_date -= timedelta(days=random.randint(0, 2))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} synthetic orders to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
