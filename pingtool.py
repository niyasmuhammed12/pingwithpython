#!/usr/bin/env python3
"""
Subnet Ping Scanner
Pings all IP addresses in a subnet and reports non-pingable ones
Supports concurrent pinging for faster execution
"""

import subprocess
import ipaddress
import concurrent.futures
import sys
import time
from typing import List, Tuple

def ping_host(ip: str, timeout: int = 1) -> Tuple[str, bool]:
    """
    Ping a single host and return the IP and ping status
    
    Args:
        ip: IP address to ping
        timeout: Ping timeout in seconds
        
    Returns:
        Tuple of (ip_address, is_reachable)
    """
    try:
        # Use ping command with timeout
        # -c 1: send only 1 packet
        # -W timeout: wait timeout seconds for response
        # -q: quiet output
        result = subprocess.run(
            ['ping', '-c', '1', '-W', str(timeout), ip],
            capture_output=True,
            text=True,
            timeout=timeout + 1
        )
        
        # Return True if ping was successful (return code 0)
        return ip, result.returncode == 0
        
    except subprocess.TimeoutExpired:
        return ip, False
    except Exception as e:
        print(f"Error pinging {ip}: {e}")
        return ip, False

def scan_subnet(subnet: str, max_workers: int = 50, timeout: int = 1) -> List[str]:
    """
    Scan all hosts in a subnet and return non-pingable IPs
    
    Args:
        subnet: Subnet in CIDR notation (e.g., '172.25.12.0/24')
        max_workers: Maximum number of concurrent ping operations
        timeout: Ping timeout in seconds
        
    Returns:
        List of non-pingable IP addresses
    """
    try:
        # Parse the subnet
        network = ipaddress.IPv4Network(subnet, strict=False)
        
        # Get all host IPs (excluding network and broadcast addresses)
        host_ips = [str(ip) for ip in network.hosts()]
        
        print(f"Scanning subnet {subnet}")
        print(f"Total hosts to scan: {len(host_ips)}")
        print(f"Using {max_workers} concurrent workers")
        print(f"Ping timeout: {timeout} seconds")
        print("-" * 50)
        
        non_pingable = []
        pingable_count = 0
        
        # Use ThreadPoolExecutor for concurrent pinging
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all ping tasks
            future_to_ip = {
                executor.submit(ping_host, ip, timeout): ip 
                for ip in host_ips
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_ip):
                ip, is_reachable = future.result()
                
                if is_reachable:
                    pingable_count += 1
                    print(f"✓ {ip} - REACHABLE")
                else:
                    non_pingable.append(ip)
                    print(f"✗ {ip} - NOT REACHABLE")
        
        print("-" * 50)
        print(f"Scan completed!")
        print(f"Pingable hosts: {pingable_count}")
        print(f"Non-pingable hosts: {len(non_pingable)}")
        
        return non_pingable
        
    except Exception as e:
        print(f"Error scanning subnet: {e}")
        return []

def get_subnet_input() -> str:
    """
    Get subnet input from user with validation
    
    Returns:
        Valid subnet in CIDR notation
    """
    while True:
        print("\nSubnet Ping Scanner")
        print("=" * 50)
        print("Enter the subnet you want to scan for non-pingable IPs")
        print("Examples:")
        print("  192.168.1.0/24")
        print("  172.16.0.0/16") 
        print("  10.0.0.0/8")
        print("  192.168.1.0/28")
        print("-" * 50)
        
        subnet_input = input("Enter subnet (CIDR notation): ").strip()
        
        if not subnet_input:
            print("❌ Error: Please enter a subnet")
            continue
            
        try:
            # Validate the subnet format
            network = ipaddress.IPv4Network(subnet_input, strict=False)
            
            # Check if the subnet is too large (more than 1024 hosts)
            if network.num_addresses > 1024:
                response = input(f"⚠️  Warning: This subnet has {network.num_addresses} addresses. This may take a while. Continue? (y/n): ").strip().lower()
                if response not in ['y', 'yes']:
                    continue
            
            return str(network)
            
        except ipaddress.AddressValueError:
            print("❌ Error: Invalid subnet format. Please use CIDR notation (e.g., 192.168.1.0/24)")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function"""
    # Get subnet from user input
    subnet = get_subnet_input()
    
    print(f"\n🔍 Starting scan for subnet: {subnet}")
    print("Looking for non-pingable IP addresses...")
    print("=" * 60)
    
    start_time = time.time()
    
    # Scan the subnet
    non_pingable_ips = scan_subnet(subnet, max_workers=50, timeout=1)
    
    end_time = time.time()
    scan_duration = end_time - start_time
    
    print(f"\n⏱️  Scan completed in {scan_duration:.2f} seconds")
    
    # Display results
    print("\n" + "=" * 60)
    print("📋 SCAN RESULTS")
    print("=" * 60)
    
    if non_pingable_ips:
        print(f"🔴 Found {len(non_pingable_ips)} non-pingable IP addresses:")
        print("-" * 40)
        for ip in sorted(non_pingable_ips, key=lambda x: ipaddress.IPv4Address(x)):
            print(f"  ❌ {ip}")
            
        print(f"\n📊 Summary:")
        print(f"  • Total IPs scanned: {len(list(ipaddress.IPv4Network(subnet).hosts()))}")
        print(f"  • Non-pingable IPs: {len(non_pingable_ips)}")
        print(f"  • Pingable IPs: {len(list(ipaddress.IPv4Network(subnet).hosts())) - len(non_pingable_ips)}")
    else:
        print("🟢 All IP addresses in the subnet are pingable!")
        print(f"📊 Total IPs scanned: {len(list(ipaddress.IPv4Network(subnet).hosts()))}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
