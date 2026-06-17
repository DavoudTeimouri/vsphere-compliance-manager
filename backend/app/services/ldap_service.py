from ldap3 import Server, Connection, ALL, NTLM, SIMPLE, ALL_ATTRIBUTES
from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPSocketOpenError
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

    def _get_server(self) -> Server:
        host = self.server_url.replace("ldap://", "").replace("ldaps://", "").split(":")[0]
        port = 636 if self.use_ssl else 389
        if ":" in self.server_url.split("//")[-1]:
            port = int(self.server_url.split(":")[-1])
        return Server(host, port=port, use_ssl=self.use_ssl, get_info=ALL, connect_timeout=10)

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        try:
            server = self._get_server()

            # Bind with service account to search for user
            if self.bind_dn and self.bind_password:
                conn = Connection(server, user=self.bind_dn, password=self.bind_password,
                                  authentication=SIMPLE, auto_bind=True)
            else:
                conn = Connection(server, auto_bind=True)

            # Search for the user
            search_filter = self.user_search_filter.replace("{username}", username)
            conn.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                attributes=["cn", "mail", "displayName", "memberOf", "sAMAccountName"]
            )

            if not conn.entries:
                logger.warning(f"LDAP user not found: {username}")
                return None

            entry = conn.entries[0]
            user_dn = entry.entry_dn

            # Now authenticate with user's own credentials
            user_conn = Connection(server, user=user_dn, password=password,
                                   authentication=SIMPLE)
            if not user_conn.bind():
                logger.warning(f"LDAP invalid credentials for: {username}")
                return None

            # Extract groups
            groups = []
            if hasattr(entry, "memberOf") and entry.memberOf:
                groups = list(entry.memberOf.values)

            return {
                "username": username,
                "full_name": str(entry.displayName) if hasattr(entry, "displayName") and entry.displayName else str(entry.cn),
                "email": str(entry.mail) if hasattr(entry, "mail") and entry.mail else None,
                "groups": groups,
                "dn": user_dn
            }

        except LDAPBindError:
            logger.warning(f"LDAP bind failed for: {username}")
            return None
        except LDAPSocketOpenError:
            logger.error(f"LDAP server unreachable: {self.server_url}")
            raise Exception("LDAP server is unreachable")
        except LDAPException as e:
            logger.error(f"LDAP error: {e}")
            raise

    def test_connection(self) -> bool:
        """Test service account bind only — used by settings endpoint."""
        try:
            server = self._get_server()
            conn = Connection(server, user=self.bind_dn, password=self.bind_password,
                              authentication=SIMPLE, auto_bind=True)
            conn.unbind()
            return True
        except Exception as e:
            logger.error(f"LDAP test connection failed: {e}")
            raise

    def map_role_from_groups(self, groups: list, group_mappings: Dict) -> str:
        """Map LDAP groups to application roles."""
        for role, group_dn in group_mappings.items():
            if group_dn and any(group_dn.lower() in g.lower() for g in groups):
                return role
        return "viewer"
