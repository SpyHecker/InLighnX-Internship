#!/usr/bin/env python3
import argparse
import hashlib
import itertools
import string
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm


SUPPORTED_HASHES = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}


def get_hash_fn(hash_type):
    hash_type = hash_type.lower()
    if hash_type not in SUPPORTED_HASHES:
        raise ValueError(f"Unsupported hash type: {hash_type}")
    return SUPPORTED_HASHES[hash_type]


def check_hash(candidate, target_hash, hash_fn):
    """Return True if candidate’s hash == target_hash."""
    h = hash_fn(candidate.encode()).hexdigest()
    return h == target_hash.lower()


def load_wordlist(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            pwd = line.strip()
            if pwd:
                yield pwd


def generate_passwords(chars, min_len, max_len):
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(chars, repeat=length):
            yield "".join(combo)


def worker(candidate, target_hash, hash_fn):
    if check_hash(candidate, target_hash, hash_fn):
        return candidate
    return None


def crack_with_iterable(password_iter, target_hash, hash_fn, max_workers=8, total=None, desc="Cracking"):
    found = None
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        with tqdm(total=total, desc=desc, unit="pwd") as pbar:
            for pwd in password_iter:
                fut = executor.submit(worker, pwd, target_hash, hash_fn)
                futures[fut] = pwd

                # consume results as they complete
                done = []
                for f in futures:
                    if f.done():
                        done.append(f)
                for f in done:
                    futures.pop(f, None)
                    pbar.update(1)
                    result = f.result()
                    if result is not None:
                        found = result
                        # cancel remaining
                        for rem in futures:
                            rem.cancel()
                        return found
    return found


def main():
    parser = argparse.ArgumentParser(description="Password hash cracker (wordlist / brute force).")
    parser.add_argument("hash", help="Target hash to crack")
    parser.add_argument("-t", "--type", default="md5", help="Hash type (md5, sha1, sha256, sha512)")
    parser.add_argument("-w", "--wordlist", help="Path to wordlist file")
    parser.add_argument("--min-length", type=int, default=1, help="Minimum password length for brute force")
    parser.add_argument("--max-length", type=int, default=4, help="Maximum password length for brute force")
    parser.add_argument(
        "--charset",
        default=string.ascii_letters + string.digits,
        help="Characters to use in brute-force mode (default: letters+digits)",
    )
    parser.add_argument("--threads", type=int, default=8, help="Number of threads (default: 8)")

    args = parser.parse_args()

    try:
        hash_fn = get_hash_fn(args.type)
    except ValueError as e:
        print(e)
        return

    target_hash = args.hash.strip()

    # 1) Dictionary attack (if wordlist provided)
    if args.wordlist:
        print(f"[+] Starting dictionary attack using {args.wordlist}")
        # estimate total lines for tqdm (optional)
        try:
            with open(args.wordlist, "r", encoding="utf-8", errors="ignore") as f:
                total = sum(1 for _ in f)
        except OSError:
            print("[-] Could not open wordlist file.")
            return

        word_iter = load_wordlist(args.wordlist)
        found = crack_with_iterable(
            word_iter,
            target_hash,
            hash_fn,
            max_workers=args.threads,
            total=total,
            desc="Dictionary",
        )
        if found:
            print(f"[+] Password found (dictionary): {found}")
            return
        else:
            print("[-] Dictionary attack failed. Trying brute force...")

    # 2) Brute-force attack
    print(
        f"[+] Starting brute-force attack: "
        f"length {args.min_length}-{args.max_length}, "
        f"charset size={len(args.charset)}"
    )

    # total combinations (for tqdm)
    total = 0
    for length in range(args.min_length, args.max_length + 1):
        total += len(args.charset) ** length

    pwd_iter = generate_passwords(args.charset, args.min_length, args.max_length)
    found = crack_with_iterable(
        pwd_iter,
        target_hash,
        hash_fn,
        max_workers=args.threads,
        total=total,
        desc="Brute force",
    )

    if found:
        print(f"[+] Password found (brute force): {found}")
    else:
        print("[-] Password not found in given search space.")


if __name__ == "__main__":
    main()
