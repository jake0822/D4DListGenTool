import requests
from bs4 import BeautifulSoup


BASE = "https://search.leonpa.gov"


def build_payload(address, token):
    data = [
        ("draw", "1"),
    ]

    columns = [
        ("ParcelId", True),
        ("Owners", True),
        ("Address", True),
        ("PropertyUse", True),
        ("Acreage", True),
        ("5", False),
        ("6", False),
    ]

    for i, (name, orderable) in enumerate(columns):
        data.extend([
            (f"columns[{i}][data]", name),
            (f"columns[{i}][name]", ""),
            (f"columns[{i}][searchable]", "true"),
            (f"columns[{i}][orderable]", "true" if orderable else "false"),
            (f"columns[{i}][search][value]", ""),
            (f"columns[{i}][search][regex]", "false"),
        ])

    data.extend([
        ("order[0][column]", "0"),
        ("order[0][dir]", "asc"),
        ("start", "0"),
        ("length", "10"),
        ("search[value]", ""),
        ("search[regex]", "false"),

        ("Address", address.upper()),
        ("ParcelId", ""),
        ("OwnerName", ""),
        ("SubDivision", ""),
        ("PropertyCategory", ""),
        ("TaxDistrict", ""),
        ("IsAg", ""),
        ("IsHomestead", ""),
        ("HasPool", ""),

        ("SquareFootageFrom", ""),
        ("__Invariant", "SquareFootageFrom"),

        ("SquareFootageTo", ""),
        ("__Invariant", "SquareFootageTo"),

        ("YearBuiltFrom", ""),
        ("__Invariant", "YearBuiltFrom"),

        ("YearBuiltTo", ""),
        ("__Invariant", "YearBuiltTo"),

        ("NumberOfAcresFrom", ""),
        ("NumberOfAcresTo", ""),

        ("__RequestVerificationToken", token),
    ])

    return data


session = requests.Session()

headers = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36",
}

print("Getting search page...")

page = session.get(
    f"{BASE}/Search/Property",
    headers=headers
)

soup = BeautifulSoup(page.text, "html.parser")

token = soup.find(
    "input",
    {"name": "__RequestVerificationToken"}
)["value"]

print("Token acquired")

payload = build_payload(
    "1525 PROCTOR ST",
    token
)

print("Sending search...")

response = session.post(
    f"{BASE}/Search/ExecutePropertySearch",
    data=payload,
    headers={
        **headers,
        "X-Requested-With": "XMLHttpRequest",
        "Origin": BASE,
        "Referer": f"{BASE}/Search/Property",
    }
)

print("\nSTATUS:", response.status_code)

print("\nRESPONSE HEADERS:")
print(response.headers)

print("\nRESPONSE TEXT:")
print(response.text)