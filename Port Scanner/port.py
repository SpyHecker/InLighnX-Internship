import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# Map some common ports to services for display
COMMON_SERVICES = {
    20: "FTP-Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
}


def get_banner(sock, timeout=1.0, max_bytes=1024):
    """Try to grab a banner from an open socket."""
    sock.settimeout(timeout)
    try:
        # Send a simple probe (works for many TCP services like HTTP)
        try:
            sock.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
        except OSError:
            pass  # some services close on send, just try recv

        data = sock.recv(max_bytes)
        if not data:
            return ""
        return data.decode(errors="ignore").strip()
    except (socket.timeout, OSError):
        return ""


def scan_port(host, port, timeout=0.5):
    """Scan a single TCP port; return dict if open, else None."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        if result != 0:
            return None  # closed or filtered

        banner = get_banner(sock)
        service = COMMON_SERVICES.get(port, "Unknown")
        return {
            "port": port,
            "service": service,
            "banner": banner,
        }
    except OSError:
        return None
    finally:
        sock.close()


def print_results(results, host):
    """Print results in a simple table."""
    print(f"\nScan results for {host}")
    print("-" * 80)
    print(f"{'Port':<8} {'Service':<15} {'Banner'}")
    print("-" * 80)

    if not results:
        print("No open ports found in the specified range.")
        return

    for entry in sorted(results, key=lambda x: x["port"]):
        port = entry["port"]
        service = entry["service"]
        banner = entry["banner"].replace("\n", " ")[:200]  # trim long banners
        print(f"{port:<8} {service:<15} {banner}")


def main():
    target = input("Enter target IP or hostname: ").strip()
    try:
        host = socket.gethostbyname(target)
    except socket.gaierror:
        print("Could not resolve host.")
        return

    try:
        start_port = int(input("Enter start port: ").strip())
        end_port = int(input("Enter end port (inclusive): ").strip())
    except ValueError:
        print("Ports must be integers.")
        return

    if start_port < 1 or end_port > 65535 or start_port > end_port:
        print("Invalid port range.")
        return

    try:
        max_workers = int(input("Enter number of threads (e.g. 100): ").strip())
    except ValueError:
        max_workers = 100

    print(f"\nScanning {host} from port {start_port} to {end_port} using {max_workers} threads...\n")

    open_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(scan_port, host, port): port
            for port in range(start_port, end_port + 1)
        }

        try:
            for future in as_completed(futures):
                res = future.result()
                if res:
                    open_results.append(res)
        except KeyboardInterrupt:
            print("\nScan interrupted by user.")

    print_results(open_results, host)


if __name__ == "__main__":
    main()
