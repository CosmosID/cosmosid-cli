from os import cpu_count, getenv

MAX_CONCURRENT_DOWNLOADS = 4
CHUNK_SIZE = int(getenv("CHUNK_SIZE", 4 * 1024**2))

CONCURRENT_DOWNLOADS = int(
    getenv("CONCURRENT_DOWNLOADS", min(cpu_count() * 2, MAX_CONCURRENT_DOWNLOADS))
)
