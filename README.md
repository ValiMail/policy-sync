# policy-sync

## Currently in BETA and subject to change!!

Valimail dotAuth policy sync Balena Block.

This Balena Block manages a local copy of a pipe-separated and JSON representation of policy.

## What it does

This Balena Block allows you to:

* Retrieve the device's application policy from Valimail's dotAuth policy management engine.
* Save the application policy to disk in JSON and pipe-separated format.

Structure of the JSON policy file:

```json
{"name": "APPLICATION_NAME",
 "roles": [
     {"name": "ROLE_NAME",
      "members": [
          "some._device.example",
          "someother._device.example"
      ]
     }
 ]
}
```

And the text representation (for supporting network access rules):

```text
role_name|some._device.example
role_four|another._device.example
```

The text representation of the policy is a distilled version of what's in the JSON file. The text file will only represent the roles indicated in the `ROLES` environment variable.

## Steps for use

### Prerequisites

* A DNS-based identity
* An account with Valimail's policy management beta.

1. Create a service in your `docker-compose.yml` file as shown [below](#docker-compose).
1. Establish your device's DNS name, using (https://github.com/ValiMail/identity-manager)
1. Configure environment variables for the device (see [Configuration](#Configuration), below)

### Configuration

Configuration is defined in environment variables:

| Variable   | Description                                                  |
|------------|--------------------------------------------------------------|
| DANE_ID    | This is the device's DNS name.                               |
| POLICY_URL | This is the URL for the Valimail dotAuth policy engine.      |
| APP_NAME   | This is the name of the application.                         |
| ROLES      | A comma-separated list of roles to represent in policy text. |

## docker-compose

This example contains the identity manager container, which makes managing the DNS-based identity easier.

```yaml
version: "2.1"

services:
  identity-manager:
    image: gcr.io/ValiMail/identity-manager
    restart: always
    volumes:
      - "identity:/etc/dane_id"
  policy-sync:
    image: gcr.io/ValiMail/policy-sync
    restart: always
    volumes:
      - "identity:/etc/dane_id"
      - "policy:/var/valimail_policy"

volumes:
  identity:
  policy:
```

Mount the `policy` volume into the container needing to access the policy JSON. Then files will be named `policy.json` and `policy.text`

## Notes

* While this is all based on standards and functionality that you can replicate with open-source technology, Valimail provides an easy interface and API for managing DNS-bound identities like this, at scale. If you want to automate the bootstrapping process, reach out to iot@valimail.com for access to the beta!