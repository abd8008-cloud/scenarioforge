#!/usr/bin/env python3
"""Generate a PBKDF2 password hash for Streamlit Secrets."""
import argparse
import hashlib
import secrets

parser = argparse.ArgumentParser(description="Generate a ScenarioForge admin password hash")
parser.add_argument("password", help="The admin password to hash")
args = parser.parse_args()
salt = secrets.token_bytes(16)
digest = hashlib.pbkdf2_hmac("sha256", args.password.encode("utf-8"), salt, 310_000)
print(f"{salt.hex()}:{digest.hex()}")
