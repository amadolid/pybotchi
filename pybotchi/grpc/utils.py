"""Pybotchi GRPC Utilities."""

from aiofiles import open


CERT_CACHE: dict[str, bytes] = {}


async def read_cert(path: str) -> bytes:
    """Read Cert."""
    if not (cert := CERT_CACHE.get(path)):
        async with open(path, "rb") as f:
            CERT_CACHE[path] = cert = await f.read()

    return cert
