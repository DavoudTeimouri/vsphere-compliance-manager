import ldap
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class LDAPService:
    def __init__(self, server_url: str, base_dn: str, bind_dn: str = None,
                 bind_password: str = None, user_search_filter: str = None,
                 group_search_base: str = None, use_ssl: bool = False):
        self.server_url = server_url
        self.base_dn = base_dn
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.user_search_filter = user_search_filter or "(sAMAccountName={username})"
        self.group_search_base = group_search_base or base_dn
        self.use_ssl = use_ssl

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        try:
            conn = ldap.initialize(self.server_url)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
            if self.use_ssl:
                conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
                conn.start_tls_s()
            # Bind with service account to search
            if self.bind_dn and self.bind_password:
                conn.simple_bind_s(self.bind_dn, self.bind_password)
            else:
                conn.simple_bind_s()
            # Search for the user
            search_filter = self.user_search_filter.replace("{username}", ldap.filter.escape_filter_chars(username))
            results = conn.search_s(
                self.base_dn, ldap.SCOPE_SUBTREE, search_filter,
                ['cn', 'mail', 'displayName', 'memberOf', 'sAMAccountName']
            )
            if not results:
                logger.warning(f"LDAP user not found: {username}")
                return None
            user_dn, user_attrs = results[0]
            if not user_dn:
                return None
            # Authenticate with user credentials
            try:
                conn.simple_bind_s(user_dn, password)
            except ldap.INVALID_CREDENTIALS:
                logger.warning(f"LDAP invalid credentials for: {username}")
                return None
            # Extract user info
            def get_attr(attrs, key):
                val = attrs.get(key, [])
                if val and isinstance(val[0], bytes):
                    return val[0].decode('utf-8', errors='ignore')
                return val[0] if val else None
            groups = []
            for g in user_attrs.get('memberOf', []):
                if isinstance(g, bytes):
                    g = g.decode('utf-8', errors='ignore')
                groups.append(g)
            return {
                "username": username,
                "full_name": get_attr(user_attrs, 'displayName') or get_attr(user_attrs, 'cn'),
                "email": get_attr(user_attrs, 'mail'),
                "groups": groups,
                "dn": user_dn
            }
        except ldap.SERVER_DOWN:
            logger.error(f"LDAP server unreachable: {self.server_url}")
            raise Exception("LDAP server is unreachable")
        except Exception as e:
            logger.error(f"LDAP authentication error: {e}")
            raise

    def map_role_from_groups(self, groups: list, group_mappings: Dict) -> str:
        """Map LDAP groups to application roles."""
        # group_mappings = {"admin": "cn=vcm-admins,...", "operator": "cn=vcm-ops,..."}
        for role, group_dn in group_mappings.items():
            if any(group_dn.lower() in g.lower() for g in groups):
                return role
        return "viewer"
