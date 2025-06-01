#!/usr/bin/env python3
"""
Generate UCAN authorization headers for Storacha using the w3 CLI.

This script generates the proper X-Auth-Secret and Authorization headers
needed for Storacha HTTP Bridge API calls.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_w3_command(cmd_args):
    """Run a w3 CLI command and return the output."""
    try:
        result = subprocess.run(
            ["w3"] + cmd_args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running w3 command: {e}")
        print(f"stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: w3 CLI not found. Please install it first:")
        print("npm install -g @web3-storage/w3cli")
        return None

def check_w3_setup():
    """Check if w3 CLI is installed and configured."""
    print("🔍 Checking w3 CLI setup...")
    
    # Check if w3 is installed
    try:
        result = subprocess.run(["w3", "--version"], capture_output=True, text=True)
        print(f"✅ w3 CLI version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ w3 CLI not found. Please install it:")
        print("npm install -g @web3-storage/w3cli")
        return False
    
    # Check login status
    spaces = run_w3_command(["space", "ls"])
    if not spaces:
        print("❌ No w3 spaces found. Please login first:")
        print("w3 login <your-email>")
        print("w3 space create")
        return False
    
    print("✅ w3 CLI is configured")
    return True

def get_space_did():
    """Get the DID of the current w3 space."""
    spaces = run_w3_command(["space", "ls"])
    if not spaces:
        return None
    
    # Parse the space list - the active space is marked with *
    for line in spaces.split('\n'):
        if line.strip().startswith('*'):
            # Extract the DID from the line
            parts = line.strip().split()
            if len(parts) >= 2:
                return parts[1]  # The DID should be the second part
    
    # If no active space, take the first one
    lines = spaces.split('\n')
    if lines and lines[0].strip():
        parts = lines[0].strip().split()
        if len(parts) >= 1:
            return parts[0] if parts[0].startswith('did:') else parts[1] if len(parts) > 1 else None
    
    return None

def generate_auth_headers(space_did, capabilities=None, expiration_hours=24):
    """Generate UCAN auth headers using w3 CLI."""
    if capabilities is None:
        capabilities = ['store/add', 'upload/add', 'upload/list']
    
    print(f"🔑 Generating UCAN headers for space: {space_did}")
    print(f"   Capabilities: {', '.join(capabilities)}")
    print(f"   Expiration: {expiration_hours} hours")
    
    # Calculate expiration timestamp
    import time
    expiration = int(time.time()) + (expiration_hours * 3600)
    
    # Build the w3 bridge generate-tokens command
    cmd = ["bridge", "generate-tokens", space_did]
    for cap in capabilities:
        cmd.extend(["--can", cap])
    cmd.extend(["--expiration", str(expiration)])
    
    output = run_w3_command(cmd)
    if not output:
        return None, None
    
    # Parse the output to extract headers
    auth_secret = None
    auth_token = None
    
    for line in output.split('\n'):
        if 'X-Auth-Secret header:' in line:
            auth_secret = line.split(':', 1)[1].strip()
        elif 'Authorization header:' in line:
            auth_token = line.split(':', 1)[1].strip()
    
    return auth_secret, auth_token

def update_env_file(auth_secret, auth_token):
    """Update the .env file with the new UCAN headers."""
    env_file = Path(__file__).parent / ".env"
    
    print(f"📝 Updating {env_file} with UCAN headers...")
    
    # Read existing content
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update or add UCAN headers
    new_lines = []
    found_secret = False
    found_token = False
    
    for line in lines:
        if line.startswith('STORACHA_UCAN_SECRET='):
            new_lines.append(f"STORACHA_UCAN_SECRET={auth_secret}\n")
            found_secret = True
        elif line.startswith('STORACHA_UCAN_TOKEN='):
            new_lines.append(f"STORACHA_UCAN_TOKEN={auth_token}\n")
            found_token = True
        else:
            new_lines.append(line)
    
    # Add new lines if not found
    if not found_secret:
        new_lines.append(f"STORACHA_UCAN_SECRET={auth_secret}\n")
    if not found_token:
        new_lines.append(f"STORACHA_UCAN_TOKEN={auth_token}\n")
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Environment file updated!")

def main():
    print("🚀 Generating UCAN authorization headers for Storacha...")
    
    # Check w3 CLI setup
    if not check_w3_setup():
        return 1
    
    # Get space DID
    space_did = get_space_did()
    if not space_did:
        print("❌ Could not determine space DID")
        return 1
    
    print(f"📍 Using space: {space_did}")
    
    # Generate headers
    auth_secret, auth_token = generate_auth_headers(space_did)
    if not auth_secret or not auth_token:
        print("❌ Failed to generate UCAN headers")
        return 1
    
    print("✅ Generated UCAN headers successfully!")
    print(f"   X-Auth-Secret: {auth_secret[:20]}...")
    print(f"   Authorization: {auth_token[:30]}...")
    
    # Update .env file
    update_env_file(auth_secret, auth_token)
    
    print("\n🎉 UCAN headers generated and saved!")
    print("You can now test the Storacha connection again:")
    print("python3 test_storacha_setup.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 