# ping tool with python

The goal of this tool is to get the non pingable IPs to use for assigning to servers when we provide one subnet as an input, this will help avoid manual pinging of each IPs and finding the vacant IP to assign to newly onboarding Servers.

The script is logically broken down into four main functions, each with a specific responsibility.

1. ping_host(ip: str, timeout: int = 1) -> Tuple[str, bool]
This is the core "worker" function. Its only job is to ping a single IP address and report whether it was successful.

subprocess.run(...): This is the key line. It executes an external command from within Python. Here, it runs the system's built-in ping command.

['ping', '-c', '1', '-W', str(timeout), ip]: This is the command it runs.

ping: The network utility.

-c 1: Sends only one ICMP echo request packet.

-W str(timeout): Waits for a response for the specified timeout in seconds. (Note: These flags are for Linux/macOS. Windows uses -n 1 and -w <milliseconds>).

capture_output=True: Prevents the ping command's output from being printed directly to your console. It's captured by Python instead.

timeout=timeout + 1: This is a safeguard. It tells the subprocess module to kill the ping command if the entire process takes longer than expected, preventing the script from hanging.

return ip, result.returncode == 0: A command-line program returns an exit code when it finishes. For ping, a return code of 0 means the host was reachable. Any other code (like 1 or 2) indicates a failure. This line neatly returns the IP address and a True/False value for its reachability.

try...except Block: This handles errors gracefully. If the ping command times out or another error occurs, it prints a message and safely returns False.

2. scan_subnet(subnet: str, max_workers: int = 50, timeout: int = 1) -> List[str]
This function is the "manager" that orchestrates the entire scan.

ipaddress.IPv4Network(subnet): This uses the powerful ipaddress library to parse the CIDR notation string (e.g., '172.25.12.0/24') into a network object. This object understands the network's properties.

network.hosts(): This is a convenient method from the ipaddress library that generates all usable host IP addresses within the subnet, automatically excluding the network address (e.g., 172.25.12.0) and the broadcast address (e.g., 172.25.12.255).

concurrent.futures.ThreadPoolExecutor(max_workers=max_workers): This is the magic behind the script's speed.

It creates a "pool" of worker threads (up to 50 by default).

Instead of running pings in a slow, sequential for loop, it submits all the ping_host tasks to the thread pool.

The thread pool runs these tasks concurrently, which is highly efficient for I/O-bound operations like waiting for a network response.

concurrent.futures.as_completed(future_to_ip): This is a clever iterator. It doesn't wait for all pings to finish. Instead, it yields each ping_host task's result as soon as it's completed, allowing the script to provide real-time feedback (✓ REACHABLE or ✗ NOT REACHABLE).

Result Aggregation: As each ping result comes in, the function checks if it was successful. If not (is_reachable is False), it adds the IP to the non_pingable list. Finally, it returns this list.

3. get_subnet_input() -> str
This function handles all user interaction and input validation, making the script more robust and user-friendly.

while True: loop: Keeps asking the user for input until a valid subnet is provided.

try...except ipaddress.AddressValueError: This is the primary validation check. If the user enters something that isn't a valid CIDR notation (like "hello" or "192.168.1"), the ipaddress library will raise an AddressValueError, which is caught here, and a helpful error message is displayed.

Subnet Size Warning: The check if network.num_addresses > 1024: is a great user experience feature. It warns the user before starting a potentially very long scan on a large network and gives them a chance to back out.

4. main()
This is the main entry point that ties everything together.

Execution Flow: It calls the other functions in the correct order:

Calls get_subnet_input() to get a valid subnet from the user.

Records the start_time using the time module.

Calls scan_subnet() to perform the actual work.

Records the end_time and calculates the total duration.

Prints a clear, well-formatted summary of the results, listing the non-pingable IPs.

The if __name__ == "__main__": block is standard Python practice. It ensures that the main() function is called only when the script is executed directly, not when it's imported as a module into another script.

Execution Flow Summary
You run the script (python your_script_name.py).

The main() function starts.

get_subnet_input() prompts you to enter a subnet. It validates your input.

main() receives the valid subnet and calls scan_subnet().

scan_subnet() generates a list of all IPs to be pinged.

A ThreadPoolExecutor is created. It takes the list of IPs and assigns a ping_host task for each one to a worker thread. Up to 50 pings can happen at the same time.

As each ping_host task finishes, as_completed() reports the result. A real-time status line is printed to the console.

Once all pings are complete, scan_subnet() returns a final list of all IPs that failed the ping test.

main() receives this list, calculates the total scan time, and prints the final, formatted results.
