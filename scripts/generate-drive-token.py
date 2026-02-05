"""Google Drive OAuth token generator using Secret Manager."""

import os
import tempfile
from pathlib import Path

from google.cloud import secretmanager
from google_auth_oauthlib.flow import InstalledAppFlow

GCP_PROJECT_ID = "eiq-development"
SECRET_ID = "google_drive_oauth_json"
SECRET_NAME = f"projects/{GCP_PROJECT_ID}/secrets/{SECRET_ID}/versions/latest"

# Use the same token location as gdocs-analysis workflow
TOKEN_FILE = Path.home() / ".config" / "gdocs-analysis" / "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def main():
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": SECRET_NAME})
    drive_oauth_secret = response.payload.data.decode("UTF-8")

    with tempfile.NamedTemporaryFile(
        mode="w+t", encoding="utf-8", suffix=".json", delete=False
    ) as temp_file:
        # Write the string to the temporary file
        temp_file.write(drive_oauth_secret)
        temp_file.flush()
        temp_file_path = temp_file.name

    try:
        flow = InstalledAppFlow.from_client_secrets_file(temp_file_path, SCOPES)

        print("\n** MANUAL AUTHORIZATION REQUIRED **")
        print(
            "\n!!! Make sure you start a SSH tunnel with port 8989 forwarded to your laptop !!!\n"
        )
        creds = flow.run_local_server(open_browser=False, bind_addr="0.0.0.0", port=8989)
        print("\n")
        os.makedirs(TOKEN_FILE.parent, exist_ok=True)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"✓ Token saved to {TOKEN_FILE}")
    finally:
        # Clean up temp file
        os.unlink(temp_file_path)


if __name__ == "__main__":
    import sys

    # Allow force regeneration with --force flag
    force = "--force" in sys.argv

    if not TOKEN_FILE.exists() or force:
        if force and TOKEN_FILE.exists():
            print(f"⚠️  Forcing regeneration of existing token at {TOKEN_FILE}")
            TOKEN_FILE.unlink()
        main()
    else:
        print(f"Token file already exists at {TOKEN_FILE}")
        print("Delete it first if you want to regenerate: rm", TOKEN_FILE)
        print("Or use --force flag: python scripts/generate-drive-token.py --force")
