"""Business logic for policy manager."""
import json
import os
import pprint
import sys
import time

import requests
from dane_jwe_jws.encryption import Encryption

from idlib import Bootstrap

def main():
    """All the magic begins and ends here, without exception."""
    config = get_config()
    crypto = Bootstrap(config["dane_id"], config["crypto_path"], config["app_uid"])
    policy_file = os.path.join(config["policy_file_dir"], "policy.json")
    danish_mapping = os.path.join(config["policy_file_dir"], "mapping.json")

    # Get the policy from disk, if it exists...
    try:
        current_policy = policy_from_file(policy_file)
    except FileNotFoundError:
        print("Policy file {} does not yet exist.".format(policy_file))  # NOQA
        current_policy = {}
    
    # Loop for live policy management...
    while True:
        
        # Get the policy URL template from DNS
        print("Application name: {}".format(config["policy_name"]))
        print("Policy URL: {}".format(config["policy_url"]))
        
        try:
            encrypted_policy = get_policy_from_server(config["policy_url"], config["policy_name"], config["dane_id"])
        except json.decoder.JSONDecodeError:
            err = ("No policy available. "
                   "Are we a member of {}?").format(config["policy_dns_name"])
            print(err)
            time.sleep(30)
            continue

        # Decrypt the policy
        policy_payload = Encryption.decrypt(encrypted_policy, crypto.get_path_for_pki_asset("key"))
        policy_json = json.loads(policy_payload)
        # Compare the current policy to downloaded. Write to disk if different.
        if current_policy != policy_json:
            print("Access policy changed. Updating local copy.")
            # Write the new policy to file.
            policy_to_file(policy_json, policy_file)
            print("Wrote updated policy to "
                  "{}".format(policy_file))
            time.sleep(1)
            # Update running policy from file.
            current_policy = policy_from_file(policy_file)
            print("Updated policy:")
            pprint.pprint(current_policy)
            write_radius_pkix_cd_manage_trust_infile(policy_json, config["ssids"], config["trust_infile_path"])
        time.sleep(120)


def write_radius_pkix_cd_manage_trust_infile(policy_json, ssids, trust_infile_path):
    """Write the input file for radius_pkix_cd_manage_trust.py."""
    ssid_list = ssids.split(",")
    tifile_lines = []
    for ssid in ssid_list:
        for role in policy_json["roles"]:
            if role["name"] == ssid:
                lines = ["{}|{}".format(ssid, supplicant) for supplicant in role["members"]]
                tifile_lines.extend(lines)
    if not tifile_lines:
        print("No policy lines for trust infile! Ensure that SSIDs map to policy roles!")
        return
    tifile_contents = "\n".join(tifile_lines)
    with open(trust_infile_path, "w") as tifile:
        tifile.write(tifile_contents)
    print("Updated {}".format(trust_infile_path))


def policy_from_file(file_path):
    """Return dictionary from policy file."""
    with open(file_path) as pol_file:
        policy = pol_file.read()
    return json.loads(policy)


def policy_to_file(policy, file_path):
    """Write policy JSON to file."""
    with open(file_path, "w") as f_obj:
        f_obj.write(json.dumps(policy))
    return


def decrypt_payload(key_file_path, encrypted_policy):
    """Decrypt and return payload from JWE."""
    key_contents = Crypto.get_file_contents(key_file_path)
    decrypted = JWEWrapper.decrypt(key_contents, encrypted_policy)
    return decrypted


def get_policy_from_server(policy_url, application_name, dane_id):
    """Return JSON response from policy server."""
    params = {"application_name": application_name, "device_name": dane_id}
    response = requests.get(policy_url, params=params)
    return response.json()


def get_config():
    """Get config from env vars.

    Return:
        dict: Keys are: policy_url, dane_id, policy_file_dir, crypto_path,
            policy_name, ssids.
    """
    config = {}
    for x in ["policy_url", "policy_file_dir", "dane_id", 
              "crypto_path", "policy_name", "app_uid", "ssids",
              "trust_infile_path"]:
        config[x] = os.getenv(x.upper())
    for k, v in config.items():
        if v is None:
            print("Missing essential configuration: {}".format(k.upper()))
    if None in config.values():
        time.sleep(30)
        sys.exit(1)
    return config


if __name__ == "__main__":
    main()
