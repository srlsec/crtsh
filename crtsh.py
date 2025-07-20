#!/usr/bin/env python3
import argparse
import requests
import json
import re
import urllib.parse
from typing import List

def display_banner():
    banner = """
            _       _     
   ___ _ __| |_ ___| |__  
  / __| '__| __/ __| '_ \ 
 | (__| |  | |_\__ \ | | |  by srlsec
  \___|_|   \__|___/_| |_|
                          
"""
    print(banner)

def clean_results(data: List[str]) -> List[str]:
    """Clean and filter results"""
    cleaned = []
    seen = set()
    
    for item in data:
        if not item:
            continue
        
        # Remove wildcards
        item = re.sub(r'\*\.', '', item)
        
        # Remove email addresses
        item = re.sub(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})', '', item)
        
        # Normalize and deduplicate
        item = item.strip().lower()
        if item and item not in seen:
            seen.add(item)
            cleaned.append(item)
    
    return sorted(cleaned)

def search_domain(domain: str):
    """Search crt.sh for certificates matching a domain"""
    if not domain:
        print("Error: Domain name is required.")
        return
    
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        if not response.text:
            print(f"No results found for domain {domain}")
            return
            
        data = json.loads(response.text)
        
        # Extract all possible domain fields
        results = []
        for entry in data:
            if 'common_name' in entry:
                results.append(entry['common_name'])
            if 'name_value' in entry:
                # name_value can be a string with \n separated values
                if isinstance(entry['name_value'], str):
                    results.extend(entry['name_value'].split('\\n'))
                else:
                    results.append(entry['name_value'])
        
        cleaned = clean_results(results)
        
        if not cleaned:
            print("No valid results found.")
            return
            
        output_file = f"output/domain.{domain}.txt"
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(cleaned))
        
        print("\n" + '\n'.join(cleaned) + "\n")
        print(f"\033[32m[+]\033[0m Total domains found: \033[31m{len(cleaned)}\033[0m")
        print(f"\033[32m[+]\033[0m Output saved in {output_file}")
        
    except Exception as e:
        print(f"Error searching domain: {e}")

def search_organization(org: str):
    """Search crt.sh for certificates matching an organization"""
    if not org:
        print("Error: Organization name is required.")
        return
    
    # Format organization name for URL (replace spaces with +)
    org_encoded = urllib.parse.quote_plus(org)
    url = f"https://crt.sh/?O={org_encoded}&output=json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        if not response.text:
            print(f"No results found for organization {org}")
            return
            
        data = json.loads(response.text)
        results = [entry['common_name'] for entry in data if 'common_name' in entry]
        cleaned = clean_results(results)
        
        if not cleaned:
            print("No valid results found.")
            return
            
        # Create safe filename by replacing special characters
        safe_org = re.sub(r'[^a-zA-Z0-9]', '_', org)
        output_file = f"org.{safe_org}.txt"
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(cleaned))
        
        print("\n" + '\n'.join(cleaned) + "\n")
        print(f"\033[32m[+]\033[0m Total domains found: \033[31m{len(cleaned)}\033[0m")
        print(f"\033[32m[+]\033[0m Output saved in {output_file}")
        
    except Exception as e:
        print(f"Error searching organization: {e}")

def main():
    display_banner()
    
    parser = argparse.ArgumentParser(description='Search crt.sh certificate database')
    parser.add_argument('-d', '--domain', help='Search Domain Name (e.g., hackerone.com)')
    parser.add_argument('-o', '--org', help='Search Organization Name (e.g., "Sony Network Communications Inc.")')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    if args.domain:
        search_domain(args.domain)
    elif args.org:
        search_organization(args.org)

if __name__ == '__main__':
    main()
