#!/usr/bin/env python3
"""
Fix Storacha credentials by converting them to the expected base64url format.

The Storacha API expects all tokens to be in base64url format (prefixed with 'u'),
but the credentials are currently in different formats:
- Auth token: base64 (prefixed with 'm')  
- Space DID key: base58btc (prefixed with 'z')
"""

import base64
import base58
import os
from pathlib import Path

def multibase_decode(encoded_str: str) -> bytes:
    """
    Decode a multibase encoded string.
    
    Multibase prefixes:
    - 'u' = base64url
    - 'm' = base64
    - 'z' = base58btc
    """
    if not encoded_str:
        raise ValueError("Empty string")
    
    prefix = encoded_str[0]
    data = encoded_str[1:]
    
    if prefix == 'u':
        # base64url - add padding if needed
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data)
    elif prefix == 'm':
        # base64 - add padding if needed
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += '=' * padding
        return base64.b64decode(data)
    elif prefix == 'z':
        # base58btc
        return base58.b58decode(data)
    else:
        raise ValueError(f"Unsupported multibase prefix: {prefix}")


def multibase_encode_base64url(data: bytes) -> str:
    """Encode bytes as base64url with 'u' prefix."""
    encoded = base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')
    return 'u' + encoded


def convert_credentials():
    """Convert Storacha credentials to base64url format."""
    
    # Load environment variables from the example file to see current values
    env_file = Path(__file__).parent / "env.example"
    
    if not env_file.exists():
        print("❌ env.example file not found")
        return
    
    print("🔧 Converting Storacha credentials to base64url format...")
    
    # Read current credentials from env.example
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    changes_made = False
    
    for line in lines:
        if line.startswith('STORACHA_AUTH_TOKEN='):
            # Extract the token value
            token = line.split('=', 1)[1].strip()
            if token.startswith('m'):
                print(f"Converting AUTH_TOKEN from base64 to base64url...")
                try:
                    # Decode from base64 (m prefix)
                    decoded_data = multibase_decode(token)
                    # Re-encode as base64url (u prefix)
                    new_token = multibase_encode_base64url(decoded_data)
                    new_line = f"STORACHA_AUTH_TOKEN={new_token}\n"
                    new_lines.append(new_line)
                    print(f"✅ Converted AUTH_TOKEN: {token[:20]}... -> {new_token[:20]}...")
                    changes_made = True
                except Exception as e:
                    print(f"❌ Failed to convert AUTH_TOKEN: {e}")
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        elif line.startswith('STORACHA_SPACE_DID='):
            # Extract the DID value
            did = line.split('=', 1)[1].strip()
            if did.startswith('did:key:z'):
                print(f"Converting SPACE_DID key from base58btc to base64url...")
                try:
                    # Extract the key part (after 'did:key:')
                    key_part = did[8:]  # Remove 'did:key:'
                    if key_part.startswith('z'):
                        # Decode from base58btc (z prefix)
                        decoded_data = multibase_decode(key_part)
                        # Re-encode as base64url (u prefix)
                        new_key = multibase_encode_base64url(decoded_data)
                        new_did = f"did:key:{new_key}"
                        new_line = f"STORACHA_SPACE_DID={new_did}\n"
                        new_lines.append(new_line)
                        print(f"✅ Converted SPACE_DID: {did} -> {new_did}")
                        changes_made = True
                    else:
                        new_lines.append(line)
                except Exception as e:
                    print(f"❌ Failed to convert SPACE_DID: {e}")
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        else:
            new_lines.append(line)
    
    if changes_made:
        # Write the updated file
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        print(f"✅ Updated {env_file}")
        
        # Also create a .env file with the corrected values
        env_actual = Path(__file__).parent / ".env"
        with open(env_actual, 'w') as f:
            f.writelines(new_lines)
        print(f"✅ Created {env_actual}")
        
        print("\n🎉 Credential conversion complete!")
        print("Now run the test script again: python3 test_storacha_setup.py")
    else:
        print("ℹ️ No conversions needed - credentials are already in correct format")


if __name__ == "__main__":
    try:
        convert_credentials()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc() 