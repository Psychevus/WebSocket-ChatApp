# Entra ID SAML SSO and SCIM Provisioning

This guide explains how to configure the chat application for SAML 2.0 single sign-on with Microsoft Entra ID (Azure AD) and how to enable automatic user and group provisioning via SCIM.

## SAML 2.0 Configuration

1. **Create an Enterprise Application** in the Entra ID portal and choose the *SAML* sign-on method.
2. Set the *Identifier (Entity ID)* to the URL of the application's metadata endpoint, e.g.:
   ```
   https://<your-domain>/saml2/metadata/
   ```
3. Set the *Reply URL (Assertion Consumer Service)* to:
   ```
   https://<your-domain>/saml2/acs/
   ```
4. Download the federation metadata XML from Entra ID and convert it to the `djangosaml2` JSON format. Save the file and point `SAML_CONFIG_PATH` to its location when starting the application.

A minimal `SAML_CONFIG_PATH` JSON might look like:
```json
{
  "metadata": {
    "remote": [
      {
        "url": "https://login.microsoftonline.com/<tenant-id>/federationmetadata/2007-06/federationmetadata.xml"
      }
    ]
  },
  "entityid": "https://<your-domain>/saml2/metadata/",
  "service": {
    "sp": {
      "name": "ChatApp",
      "endpoints": {
        "assertion_consumer_service": [
          ["https://<your-domain>/saml2/acs/", "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"]
        ]
      }
    }
  }
}
```

Once configured, users can authenticate using the **SAML Login** link on the login page.

## SCIM Provisioning

1. In Entra ID, enable *Provisioning* for the enterprise application.
2. Use the following endpoints for the SCIM connection:
   - **Users**: `https://<your-domain>/scim/v2/Users`
   - **Groups**: `https://<your-domain>/scim/v2/Groups`
3. Set the authentication method to **Bearer Token** and supply the same token as `SCIM_BEARER_TOKEN` in the application's environment.

When provisioning is enabled, Entra ID will automatically create and update users and groups by calling these endpoints.

## Testing the Flow

After completing the configuration, initiate a test sign-in from Entra ID. A new user should be provisioned through SCIM on first login, completing the round trip between SAML authentication and SCIM provisioning.
