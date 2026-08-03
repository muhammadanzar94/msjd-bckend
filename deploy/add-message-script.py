"""
Add a 'Message' column to manchester_mosques.xlsx with a personalized
outreach message for each mosque, using its Name and City.

Usage:
    pip install pandas openpyxl
    python add_messages.py
"""

import re
import pandas as pd

INPUT_FILE = "manchester_mosques.xlsx"
OUTPUT_FILE = "manchester_msgs.xlsx"  # change to INPUT_FILE to overwrite in place

MESSAGE_TEMPLATE = """Assalamu Alaikum. {name} doesn't have a website yet - I build free ones for masjids.
See an example + details: 
https://youtube.com/shorts/0QxAGnopdrE?si=bGYj_3dtFpXyZUgG
https://youtu.be/pxCBEFcVQy8?si=P6dki2qfiZ8OpSxp

for more info message at: +447435603167
"""


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def main():
    df = pd.read_excel(INPUT_FILE)

    def build_message(row):
        name = str(row.get("Name", "")).strip()
        city = str(row.get("City", "")).strip() or "your area"
        if not name:
            return ""
        return MESSAGE_TEMPLATE.format(name=name, city=city, slug=slugify(name))

    df["Message"] = df.apply(build_message, axis=1)
    df.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")
    print(f"Saved {len(df)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()