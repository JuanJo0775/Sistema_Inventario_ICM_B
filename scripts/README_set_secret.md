Set secrets for GitHub Actions via API

Prereqs
- Python 3.8+
- Install dependencies: `pip install requests pynacl`

Usage

1. Create a PAT (Personal Access Token) in GitHub with repo access and set it to env var `GITHUB_TOKEN`:

```bash
export GITHUB_TOKEN="<your_pat>"
```

2. Upload a secret from a file:

```bash
python scripts/set_secret.py --owner JuanJo0775 --repo Sistema_Inventario_ICM_B --name STAGING_SSH_PRIVATE_KEY --file ~/.ssh/id_ed25519_staging
python scripts/set_secret.py --owner JuanJo0775 --repo Sistema_Inventario_ICM_B --name STAGING_SSH_HOST --value "staging.example.com"
python scripts/set_secret.py --owner JuanJo0775 --repo Sistema_Inventario_ICM_B --name STAGING_SSH_USER --value "deployuser"
python scripts/set_secret.py --owner JuanJo0775 --repo Sistema_Inventario_ICM_B --name STAGING_SSH_PORT --value "22"
```

Notes
- The script uses the repository public key to encrypt the secret value (same behavior as `gh`).
- Remove the PAT from your env after use: `unset GITHUB_TOKEN` (or in PowerShell `Remove-Item Env:\GITHUB_TOKEN`).
