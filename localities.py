import requests

from data_cache import get_or_load


CKAN_BASE = "https://data.gov.il/api/3/action"

DATASET_ID = "citiesandsettelments"


def find_localities_resource():
    response = requests.get(
        f"{CKAN_BASE}/package_show",
        params={
            "id": DATASET_ID,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("success"):
        raise RuntimeError(
            "Could not load Israeli localities dataset."
        )

    resources = data["result"]["resources"]

    for resource in resources:
        resource_id = resource.get("id")

        if not resource_id:
            continue

        if not resource.get("datastore_active"):
            continue

        try:
            sample_response = requests.get(
                f"{CKAN_BASE}/datastore_search",
                params={
                    "resource_id": resource_id,
                    "limit": 1,
                },
                timeout=30,
            )

            sample_response.raise_for_status()

            sample_data = sample_response.json()

            records = (
                sample_data
                .get("result", {})
                .get("records", [])
            )

            if not records:
                continue

            fields = set(
                records[0].keys()
            )

            if {
                "city_code",
                "city_name_he",
            }.issubset(fields):
                return resource_id

        except requests.RequestException:
            continue

    raise RuntimeError(
        "Could not find a usable Israeli "
        "localities resource."
    )


def load_localities_raw():
    print(
        "Loading Israeli locality names..."
    )

    resource_id = find_localities_resource()

    response = requests.get(
        f"{CKAN_BASE}/datastore_search",
        params={
            "resource_id": resource_id,
            "limit": 2000,
        },
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    records = (
        data
        .get("result", {})
        .get("records", [])
    )

    localities = {}

    for record in records:
        code = record.get(
            "city_code"
        )

        name = record.get(
            "city_name_he"
        )

        if code is None or not name:
            continue

        code = str(code).strip()

        # CKAN sometimes returns numeric values
        # as strings ending in .0
        if code.endswith(".0"):
            code = code[:-2]

        localities[code] = (
            str(name).strip()
        )

    print(
        "Localities loaded:",
        len(localities),
    )

    return localities


def load_localities():
    return get_or_load(
        "israel_localities_v1",
        load_localities_raw,
        ttl_minutes=43200,
    )


if __name__ == "__main__":
    localities = load_localities()

    for code in [
        "2530",
        "7100",
        "6600",
        "8300",
    ]:
        print(
            code,
            "->",
            localities.get(code),
        )