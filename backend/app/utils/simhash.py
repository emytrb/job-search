import hashlib
import re


def compute_simhash(text: str) -> int:
    """Compute a 64-bit SimHash fingerprint for the given text.

    Returns a signed integer suitable for PostgreSQL BigInteger storage.
    """
    # Normalize: lowercase, keep only word characters and spaces
    text = re.sub(r"[^\w\s]", "", text.lower())
    words = text.split()

    if len(words) < 3:
        # Too short for shingles, hash the whole text
        digest = hashlib.md5(text.encode()).hexdigest()
        result = int(digest[:16], 16)
        return result if result < (1 << 63) else result - (1 << 64)

    # Create 3-word shingles
    shingles = [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]

    # Build 64-bit fingerprint via majority voting
    v = [0] * 64
    for shingle in shingles:
        h = int(hashlib.md5(shingle.encode()).hexdigest()[:16], 16)
        for i in range(64):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1

    result = 0
    for i in range(64):
        if v[i] > 0:
            result |= 1 << i

    # Convert to signed for PostgreSQL BigInteger
    if result >= (1 << 63):
        result -= 1 << 64
    return result


def hamming_distance(h1: int, h2: int) -> int:
    """Compute the Hamming distance between two 64-bit SimHash values."""
    return bin((h1 ^ h2) & ((1 << 64) - 1)).count("1")
