import os
import pickle
import time


CACHE_DIR = "data/cache"
DEFAULT_TTL_MINUTES = 30


def ensure_cache_directory():
    os.makedirs(
        CACHE_DIR,
        exist_ok=True,
    )


def get_cache_path(key):
    ensure_cache_directory()

    safe_key = (
        key.replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    return os.path.join(
        CACHE_DIR,
        f"{safe_key}.pkl",
    )


def is_cache_valid(
    path,
    ttl_minutes=DEFAULT_TTL_MINUTES,
):
    if not os.path.exists(path):
        return False

    age_seconds = (
        time.time()
        - os.path.getmtime(path)
    )

    max_age_seconds = (
        ttl_minutes * 60
    )

    return (
        age_seconds
        < max_age_seconds
    )


def save_cache(key, data):
    path = get_cache_path(key)

    with open(path, "wb") as file:
        pickle.dump(
            data,
            file,
        )


def load_cache(key):
    path = get_cache_path(key)

    with open(path, "rb") as file:
        return pickle.load(file)


def get_or_load(
    key,
    loader,
    ttl_minutes=DEFAULT_TTL_MINUTES,
):
    path = get_cache_path(key)

    if is_cache_valid(
        path,
        ttl_minutes,
    ):
        print(
            f"Using cached data: {key}"
        )

        try:
            return load_cache(key)

        except (
            pickle.UnpicklingError,
            EOFError,
            AttributeError,
            ImportError,
        ):
            print(
                f"Cache damaged. "
                f"Reloading: {key}"
            )

    print(
        f"Refreshing data: {key}"
    )

    data = loader()

    save_cache(
        key,
        data,
    )

    return data


def clear_cache():
    ensure_cache_directory()

    removed = 0

    for filename in os.listdir(
        CACHE_DIR
    ):
        if not filename.endswith(
            ".pkl"
        ):
            continue

        path = os.path.join(
            CACHE_DIR,
            filename,
        )

        os.remove(path)
        removed += 1

    print(
        f"Removed {removed} cache files."
    )


if __name__ == "__main__":
    clear_cache()