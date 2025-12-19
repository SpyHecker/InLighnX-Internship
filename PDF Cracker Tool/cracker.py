import argparse
import itertools
import string
import sys
import pikepdf
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_passwords(wordlist_file):
    with open(wordlist_file, "r") as f:
        for line in f:
            password = line.strip()
            if password:
                yield password

def generate_passwords(charset, min_length, max_length):
    for length in range(min_length, max_length+1):
        for combo in itertools.product(charset, repeat=length):
            yield ''.join(combo)

def try_password(pdf_file, password):
    try:
        with pikepdf.open(pdf_file, password=password):
            return password  # Success!
    except pikepdf._core.PasswordError:
        return None
    except Exception as e:
        return None

def decrypt_pdf(pdf_file, passwords, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(try_password, pdf_file, pwd): pwd
            for pwd in passwords
        }
        for f in tqdm(as_completed(futures), total=len(futures), desc="Cracking", unit="pw"):
            result = f.result()
            if result is not None:
                return result
    return None

def parse_args():
    parser = argparse.ArgumentParser(description="PDF Cracker Tool (by Inlighn Tech)")
    parser.add_argument("pdf_file", help="Path to password-protected PDF")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--wordlist", type=str, help="Path to wordlist file")
    group.add_argument("--bruteforce", action="store_true", help="Use brute-force attack")
    parser.add_argument("--min-length", type=int, default=1, help="Min password length (brute-force)")
    parser.add_argument("--max-length", type=int, default=3, help="Max password length (brute-force)")
    parser.add_argument("--charset", type=str, default=string.ascii_lowercase, help="Charset (brute-force)")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads to use")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.wordlist:
        try:
            passwords = list(load_passwords(args.wordlist))
        except FileNotFoundError:
            print(f"Wordlist file '{args.wordlist}' not found.", file=sys.stderr)
            sys.exit(1)
        if not passwords:
            print("Wordlist is empty!", file=sys.stderr)
            sys.exit(1)
    elif args.bruteforce:
        passwords = list(generate_passwords(args.charset, args.min_length, args.max_length))
        if not passwords:
            print("No passwords generated! Check min/max length or charset.", file=sys.stderr)
            sys.exit(1)
    else:
        print("Either --wordlist or --bruteforce must be set.", file=sys.stderr)
        sys.exit(1)
    print(f"[*] Attempting to crack '{args.pdf_file}' ({len(passwords)} passwords)...")
    found = decrypt_pdf(args.pdf_file, passwords, max_workers=args.threads)
    if found:
        print(f"[+] Success! Password found: '{found}'")
    else:
        print("[-] Password not found.")
