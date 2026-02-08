"""
Security Middleware - Permissions-Policy Header.

Adds the Permissions-Policy header to all responses, restricting
browser features for enhanced security.
"""

from django.conf import settings


class PermissionsPolicyMiddleware:
    """
    Middleware that adds the Permissions-Policy header to responses.

    This header (formerly Feature-Policy) restricts which browser features
    can be used, enhancing security by preventing abuse of APIs like
    camera, microphone, geolocation, etc.

    Configuration:
        Set PERMISSIONS_POLICY in settings as a dict where:
        - Keys are feature names (e.g., "camera", "microphone")
        - Values are lists of allowed origins (empty list = disabled)

    Example:
        PERMISSIONS_POLICY = {
            "camera": [],          # Disabled for all
            "microphone": ["self"], # Self only
            "geolocation": ["https://maps.google.com"],  # Specific origin
        }
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.policy_header = self._build_policy_header()

    def _build_policy_header(self):
        """Build the Permissions-Policy header value from settings."""
        policy_dict = getattr(settings, "PERMISSIONS_POLICY", {})

        if not policy_dict:
            return None

        policy_parts = []
        for feature, origins in policy_dict.items():
            if not origins:
                # Empty list = disabled
                policy_parts.append(f"{feature}=()")
            elif origins == ["self"]:
                policy_parts.append(f"{feature}=(self)")
            else:
                origins_str = " ".join(f'"{o}"' for o in origins)
                policy_parts.append(f"{feature}=({origins_str})")

        return ", ".join(policy_parts)

    def __call__(self, request):
        response = self.get_response(request)

        if self.policy_header:
            response["Permissions-Policy"] = self.policy_header

        return response
