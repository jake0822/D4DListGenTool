import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote


BASE_URL = "https://search.leonpa.gov"
SEARCH_PAGE = f"{BASE_URL}/Search/Property"
SEARCH_URL = f"{BASE_URL}/Search/ExecutePropertySearch"

import re

def normalize_address(address: str) -> str:
    replacements = {
        # Directions
        "north": "N",
        "south": "S",
        "east": "E",
        "west": "W",

        # Street types
        "street": "St",
        "avenue": "Ave",
        "drive": "Dr",
        "road": "Rd",
        "terrace": "Ter",
        "court": "Ct",
        "lane": "Ln",
        "circle": "Cir",
        "place": "Pl",
        "boulevard": "Blvd",
        "parkway": "Pkwy",
        "highway": "Hwy",
        "trail": "Trl",
        "way": "Way",
        "loop": "Loop",
    }

    result = address.strip()

    for long_name, short_name in replacements.items():
        result = re.sub(
            rf"\b{long_name}\b",
            short_name,
            result,
            flags=re.IGNORECASE
        )

    return result


def get_session_and_token():
    """
    Creates a session and gets the ASP.NET anti-forgery token.
    """

    session = requests.Session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        )
    }

    response = session.get(SEARCH_PAGE, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    token = soup.find(
        "input",
        {"name": "__RequestVerificationToken"}
    )["value"]

    return session, token, headers


def build_payload(address, token):
    """
    Builds the exact form that the Leon County site expects.
    """

    data = [
        ("draw", "1")
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


def search_property(session, token, headers, address):
    """
    Searches Leon County property records.
    """

    response = session.post(
        SEARCH_URL,
        data=build_payload(address, token),
        headers={
            **headers,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE_URL,
            "Referer": SEARCH_PAGE,
        },
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("recordsFiltered", 0) == 0:
        return None

    return data["data"][0]

def get_mailing_address(session, headers, parcel_id):
    """
    Opens the Leon County property details page and extracts
    the owner's mailing address.
    """

    if not parcel_id:
        return ""

    # Handles parcel IDs with spaces like "212527  D0090"
    encoded_id = quote(parcel_id.strip())

    details_url = f"{BASE_URL}/Property/Details/{encoded_id}"

    response = session.get(
        details_url,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the "Mailing Address" label
    label = soup.find(
        "label",
        string=lambda text: text and "Mailing Address" in text
    )

    if not label:
        return ""

    # The mailing address is stored in sibling divs
    address_parts = []

    current = label.find_next()

    while current:
        if current.name == "label":
            break

        if current.name == "div":
            text = current.get_text(" ", strip=True)

            if text:
                address_parts.append(text)

        current = current.find_next_sibling()

    return ", ".join(address_parts)

def main():

    with open(
        "addresses.txt",
        "r",
        encoding="utf-8"
    ) as file:
        addresses = [
            line.strip()
            for line in file
            if line.strip()
        ]

    print(f"\nFound {len(addresses)} addresses to process.\n")

    session, token, headers = get_session_and_token()

    results = []

    for index, address in enumerate(addresses, start=1):

        print(
            f"[{index}/{len(addresses)}] Searching: {address}"
        )

        try:
            search_address = normalize_address(address)

            result = search_property(
                session,
                token,
                headers,
                search_address
            )

            if result:

                owner = result.get("Owners", "Unknown")
                parcel_id = result.get("ParcelId")

                mailing_address = get_mailing_address(
                    session,
                    headers,
                    parcel_id
                )

                print(f"    ✓ {owner}")
                print(f"      Mailing: {mailing_address}")

                results.append({
                    "Address": result.get("Address"),
                    "Owner": owner,
                    "Mailing Address": mailing_address,
                })

            else:

                print("    ✗ No match")

                results.append({
                    "Address": address,
                    "Owner": "NOT FOUND",
                    "Mailing Address": "",
                })

        except Exception as error:

            print(f"    ERROR: {error}")

            results.append({
                "Address": address,
                "Owner": "ERROR",
                "Mailing Address": "",
            })

        # Be respectful to the county server
        time.sleep(0.25)

    with open(
        "owners.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "Address",
                "Owner",
                "Mailing Address",
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n=================================")
    print("DONE!")
    print(f"Processed {len(results)} addresses")
    print("Saved file: owners.csv")
    print("=================================")


if __name__ == "__main__":
    main()