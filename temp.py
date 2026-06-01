import os
import time
import requests
import pandas as pd
import matplotlib.pyplot as plt

S2_API_KEY = os.getenv("S2_API_KEY")

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

QUERY = '"iCub"'
START_YEAR = 2006
YEAR_RANGE = f"{START_YEAR}-"

FIELDS = ",".join([
    "paperId",
    "title",
    "year",
    "authors",
    "venue",
    "publicationDate",
    "citationCount",
    "url",
    "abstract",
])

headers = {}
if S2_API_KEY:
    headers["x-api-key"] = S2_API_KEY

params = {
    "query": QUERY,
    "year": YEAR_RANGE,
    "fields": FIELDS,
    "limit": 100,
}

papers = []
token = None

while True:
    if token:
        params["token"] = token

    r = requests.get(BASE_URL, params=params, headers=headers, timeout=30)

    if r.status_code == 429:
        wait = int(r.headers.get("Retry-After", 10))
        print(f"Rate limited. Sleeping {wait}s...")
        time.sleep(wait)
        continue

    r.raise_for_status()
    data = r.json()

    papers.extend(data.get("data", []))
    print(f"Fetched {len(papers)} papers...")

    token = data.get("token")
    if not token:
        break

    time.sleep(1)

df = pd.DataFrame(papers)

df = df[df["year"].notna()].copy()
df["year"] = df["year"].astype(int)
df = df[df["year"] >= START_YEAR]

df["authors"] = df["authors"].apply(
    lambda xs: "; ".join(a.get("name", "") for a in xs) if isinstance(xs, list) else ""
)

df.to_csv("icub_semantic_scholar_papers_2006_today.csv", index=False)

year_counts = (
    df.groupby("year")
      .size()
      .reindex(range(START_YEAR, pd.Timestamp.today().year + 1), fill_value=0)
)

year_counts.rename("paper_count").to_csv("icub_papers_by_year_2006_today.csv")

plt.figure(figsize=(11, 4))
plt.bar(year_counts.index, year_counts.values)
#plt.xlabel("Year")
plt.ylabel("Number of papers")
plt.title('Annual Publications Related to iCub')
plt.xticks(year_counts.index, rotation=45)
plt.tight_layout()

plt.savefig("icub_papers_by_year_2006_today.png", dpi=300)
plt.savefig("icub_papers_by_year_2006_today.pdf", bbox_inches="tight")

plt.show()

print(f"Total papers found: {len(df)}")
print("Saved:")
print("- icub_semantic_scholar_papers_2006_today.csv")
print("- icub_papers_by_year_2006_today.csv")
print("- icub_papers_by_year_2006_today.png")
print("- icub_papers_by_year_2006_today.pdf")