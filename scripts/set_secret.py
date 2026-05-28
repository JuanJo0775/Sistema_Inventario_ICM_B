#!/usr/bin/env python3
"""Upload GitHub Actions repository secrets via the REST API.

Usage:
  export GITHUB_TOKEN="<your_pat>"
  python scripts/set_secret.py --owner JuanJo0775 --repo Sistema_Inventario_ICM_B \
    --name STAGING_SSH_PRIVATE_KEY --file C:\Users\JUAN JOSE\.ssh\id_ed25519_staging

Requires: requests, pynacl
"""
import argparse
import base64
import json
import os
import sys

import requests
from nacl import public, encoding


GH_API = "https://api.github.com"


def get_public_key(owner, repo, token):
    url = f"{GH_API}/repos/{owner}/{repo}/actions/secrets/public-key"
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    r.raise_for_status()
    data = r.json()
    return data["key"], data["key_id"]


def encrypt_secret(public_key_b64, secret_value):
    pubkey = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
    sealed_box = public.SealedBox(pubkey)
    encrypted = sealed_box.encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()


def put_secret(owner, repo, token, name, encrypted_value, key_id):
    url = f"{GH_API}/repos/{owner}/{repo}/actions/secrets/{name}"
    payload = {"encrypted_value": encrypted_value, "key_id": key_id}
    r = requests.put(url, headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
                     data=json.dumps(payload))
    r.raise_for_status()
    return r.status_code


def main():
    p = argparse.ArgumentParser(description="Upload a secret to a repository's Actions secrets")
    p.add_argument("--owner", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--file", help="path to file with secret value")
    p.add_argument("--value", help="secret value (mutually exclusive with --file)")
    p.add_argument("--token-env", default="GITHUB_TOKEN", help="env var with PAT")
    args = p.parse_args()

    token = os.getenv(args.token_env)
    if not token:
        print(f"Set environment variable {args.token_env} with your PAT", file=sys.stderr)
        sys.exit(2)

    if args.file:
        path = os.path.expanduser(args.file)
        with open(path, "r", encoding="utf-8") as fh:
            secret = fh.read()
    elif args.value:
        secret = args.value
    else:
        print("Provide --file or --value", file=sys.stderr)
        sys.exit(2)

    public_key_b64, key_id = get_public_key(args.owner, args.repo, token)
    encrypted = encrypt_secret(public_key_b64, secret)
    put_secret(args.owner, args.repo, token, args.name, encrypted, key_id)
    print("Secret uploaded:", args.name)


if __name__ == '__main__':
    main()
