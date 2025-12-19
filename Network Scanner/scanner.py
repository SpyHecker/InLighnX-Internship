import scapy.all as scapy
import ipaddress
import socket
import threading
from queue import Queue

def scan(ip, result_queue):
    try:
        # Use Layer 3 socket instead of Layer 2 for Windows compatibility
        # Send ICMP ping to check if host is alive
        ans = scapy.sr1(scapy.IP(dst=str(ip))/scapy.ICMP(), timeout=1, verbose=False)
        if ans:
            ip_addr = str(ip)
            # Try to get MAC address using ARP (may not work without winpcap)
            mac_addr = "N/A"
            try:
                arp_result = scapy.sr1(scapy.ARP(pdst=str(ip)), timeout=1, verbose=False)
                if arp_result:
                    mac_addr = arp_result.hwsrc
            except:
                pass
            
            # Get hostname
            try:
                hostname = socket.gethostbyaddr(ip_addr)[0]
            except (socket.herror, socket.gaierror):
                hostname = "Unknown"
            result_queue.put((ip_addr, mac_addr, hostname))
    except Exception as e:
        # Silently skip hosts that cause errors
        pass

def print_results(results):
    # Print header
    print("{:<16}  {:<18}  {:<}".format("IP Address", "MAC Address", "Hostname"))
    print("-" * 50)
    for ip, mac, host in results:
        print("{:<16}  {:<18}  {:<}".format(ip, mac, host))

def main():
    cidr = input("Enter network (CIDR notation, e.g., 192.168.1.0/24): ")
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        print("Invalid CIDR notation.")
        return

    result_queue = Queue()
    threads = []
    for ip in network.hosts():
        t = threading.Thread(target=scan, args=(ip, result_queue))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    print_results(results)

if __name__ == "__main__":
    main()