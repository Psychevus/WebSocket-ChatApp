import hmac
import hashlib
from django.test import TestCase, Client, override_settings
from chat.licensing import validate_license, EnterpriseFeatureDisabled, PUBLIC_SALT


class LicensingTestCase(TestCase):
    def test_validate_license_valid(self):
        key = hmac.new(PUBLIC_SALT, b"license", hashlib.sha256).hexdigest()
        self.assertTrue(validate_license(key))

    def test_validate_license_invalid(self):
        with self.assertRaises(EnterpriseFeatureDisabled):
            validate_license("badkey")


class EnterpriseGatingTestCase(TestCase):
    @override_settings(ENTERPRISE_LICENSE_KEY="invalid")
    def test_saml_scim_forbidden(self):
        client = Client()
        resp = client.get("/saml2/")
        self.assertEqual(resp.status_code, 403)
        resp = client.get("/scim/v2/")
        self.assertEqual(resp.status_code, 403)
