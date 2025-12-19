import requests
import threading

domain = "youtube.com"
subdomains_file = "Subdomain Enumeration Tool\subdomains.txt"
output_file = "Subdomain Enumeration Tool\discovered_subdomains.txt"

discovered_subdomains = []
lock = threading.Lock()

def check_subdomain(subdomain):
    """Check if a subdomain is active by making an HTTP request."""
    url = f"http://{subdomain}.{domain}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            with lock:
                discovered_subdomains.append(subdomain)
                print(f"[+] Found: {subdomain}")
    except requests.ConnectionError:
        pass
    except Exception as e:
        print(f"[!] Error checking {subdomain}: {e}")

def main():
    
    try:
        with open(subdomains_file, "r") as f:
            subdomains = f.read().splitlines()
    except FileNotFoundError:
        print(f"Error: {subdomains_file} not found.")
        return

    threads = []
    for sub in subdomains:
        t = threading.Thread(target=check_subdomain, args=(sub,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    with open(output_file, "w") as f:
        for sub in discovered_subdomains:
            print(sub, file=f)

    print(f"\n[+] Scan complete. Discovered {len(discovered_subdomains)} subdomains.")
    print(f"[+] Results saved to {output_file}")

if __name__ == "__main__":
    main()
