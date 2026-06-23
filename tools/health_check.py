#!/usr/bin/env python3
"""
Health Check Tool with Retry Mechanism and Exponential Backoff
Implements bounty requirements for gh_4695123037
"""

import time
import socket
import requests
import argparse
import logging
from typing import Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_http_service(url: str, timeout: int = 10, retries: int = 3, backoff: float = 2.0) -> Tuple[bool, str]:
    """Check HTTP service with retry mechanism and exponential backoff."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return True, f"HTTP service at {url} is healthy (status: {response.status_code})"
            else:
                logger.warning(f"Attempt {attempt + 1}/{retries}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{retries}: {str(e)}")
        
        if attempt < retries - 1:
            delay = backoff * (2 ** attempt)
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    return False, f"HTTP service at {url} failed after {retries} attempts"


def check_tcp_port(host: str, port: int, timeout: int = 10, retries: int = 3, backoff: float = 2.0) -> Tuple[bool, str]:
    """Check TCP port with retry mechanism and exponential backoff."""
    for attempt in range(retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return True, f"TCP port {port} on {host} is open"
            else:
                logger.warning(f"Attempt {attempt + 1}/{retries}: Port {port} closed (error code: {result})")
        except socket.error as e:
            logger.warning(f"Attempt {attempt + 1}/{retries}: {str(e)}")
        
        if attempt < retries - 1:
            delay = backoff * (2 ** attempt)
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    return False, f"TCP port {port} on {host} failed after {retries} attempts"


def main():
    parser = argparse.ArgumentParser(description='Health check tool with retry mechanism')
    parser.add_argument('--http', help='HTTP URL to check')
    parser.add_argument('--host', help='Host for TCP check')
    parser.add_argument('--port', type=int, help='Port for TCP check')
    parser.add_argument('--timeout', type=int, default=10, help='Connection timeout (default: 10)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries (default: 3)')
    parser.add_argument('--backoff', type=float, default=2.0, help='Base backoff time in seconds (default: 2.0)')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    if args.http:
        success, message = check_http_service(args.http, args.timeout, args.retries, args.backoff)
    elif args.host and args.port:
        success, message = check_tcp_port(args.host, args.port, args.timeout, args.retries, args.backoff)
    else:
        parser.error("Either --http or --host/--port must be specified")
    
    if args.json:
        import json
        result = {
            "success": success,
            "message": message,
            "retries": args.retries,
            "backoff": args.backoff
        }
        print(json.dumps(result, indent=2))
    else:
        if success:
            logger.info(message)
        else:
            logger.critical(message)
            exit(1)


if __name__ == "__main__":
    main()
