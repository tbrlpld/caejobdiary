import argparse
import os
from shutil import copyfile


parser = argparse.ArgumentParser(
    description="Create dummy secrets file.")
parser.add_argument("dir", type=str, nargs=1)

config_dir = os.path.abspath(parser.parse_args().dir[0])
print("Output directory: {}".format(config_dir))
if not os.path.exists(config_dir):
    print("Config directory does not exist. Creating it...")
    os.mkdir(config_dir)


secrets_filepath = os.path.join(config_dir, "secrets.json")
print("Creating secrets dummy file  {} ...".format(secrets_filepath))

content = '''{
    "FILENAME": "secrets.json",
    "SECRET_KEY": "this-here-should-be-a-very-safe-key",
    "FEEDBACK_RECIPIENT_EMAIL": "someone@example.com",
    "OUTGOING_MAIL_HOST_SERVER": "smtp.example.com",
    "OUTGOING_MAIL_HOST_PORT": 25,
    "OUTGOING_MAIL_USER": "info@example.com",
    "OUTGOING_MAIL_PASSWORD": "somepassword",
    "WARNING_RECIPIENT_EMAIL": "admin@example.com",
    "DB_PASSWORD": "password"
}'''

if os.path.exists(secrets_filepath):
    print("Existing secrets detected. Backing it up ...")
    copyfile(secrets_filepath, secrets_filepath + ".backup")
with open(secrets_filepath, "w") as f:
    f.write(content)

print("Dummy file created. Please change the secret key!")
