"""
Secure credential storage for Linear API authentication.

Handles encrypted storage of credentials using system keyring with additional encryption.
"""

import base64
import json
import logging
from typing import Any

import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class CredentialStorage:
    """
    Secure credential storage using keyring and encryption.

    Stores sensitive credentials in the system keyring with additional
    encryption layer for extra security. Uses static salt for key derivation
    which is acceptable since we're not hashing passwords - the salt provides
    deterministic key generation from user_id.

    Security considerations:
    - Keyring provides OS-level credential protection
    - Additional Fernet encryption protects against keyring vulnerabilities
    - PBKDF2 fallback with high iteration count for systems without keyring
    - Static salt is safe here as it's for key derivation, not password hashing
    """

    SERVICE_NAME = "linear-cli"
    KEY_SALT = b"linear-cli-salt-2023"  # Static salt is acceptable for deterministic key derivation from user_id

    def __init__(self, user_id: str = "default"):
        """
        Initialize credential storage.

        Args:
            user_id: User identifier for credential isolation
        """
        # Ensure user_id is a string (handle PosixPath objects)
        self.user_id = str(user_id)
        self._keyring_available = self._check_keyring_availability()
        self._cipher = self._get_cipher()

    def _check_keyring_availability(self) -> bool:
        """
        Check if keyring backend is available without generating warnings.

        Returns:
            bool: True if keyring can be used, False otherwise
        """
        try:
            # Try a simple keyring operation to test availability
            keyring.get_password("test-service", "test-user")
            return True
        except Exception:
            # Keyring backend is not available, we'll use PBKDF2 fallback
            return False

    def _get_cipher(self) -> Fernet:
        """
        Get or create encryption cipher for credential storage.

        Uses keyring for key storage with PBKDF2 fallback for systems
        where keyring is unavailable. The encryption provides an additional
        security layer beyond keyring's native protection.

        Returns:
            Fernet: Encryption cipher instance
        """
        if self._keyring_available:
            try:
                # Try to get existing key from keyring
                key_b64 = keyring.get_password(self.SERVICE_NAME, f"{self.user_id}_key")
                if key_b64:
                    key = base64.urlsafe_b64decode(key_b64.encode())
                else:
                    # Generate new key and store it
                    key = Fernet.generate_key()
                    key_b64 = base64.urlsafe_b64encode(key).decode()
                    keyring.set_password(self.SERVICE_NAME, f"{self.user_id}_key", key_b64)

                return Fernet(key)
            except Exception:
                # Keyring failed after being available, fall through to PBKDF2
                self._keyring_available = False
        
        # Use PBKDF2 fallback (either keyring not available or failed)
        logger.debug("Using PBKDF2 key derivation for credential encryption")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.KEY_SALT,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.user_id.encode()))
        return Fernet(key)

    def store_credentials(self, credentials: dict[str, Any]) -> None:
        """
        Store encrypted credentials in keyring.

        Args:
            credentials: Dictionary of credentials to store
        """
        try:
            # Encrypt credentials
            encrypted_data = self._cipher.encrypt(json.dumps(credentials).encode())
            encoded_data = base64.urlsafe_b64encode(encrypted_data).decode()

            if self._keyring_available:
                # Store in keyring
                keyring.set_password(self.SERVICE_NAME, self.user_id, encoded_data)
                logger.debug("Credentials stored securely in keyring")
            else:
                # When keyring is not available, we can't store credentials persistently
                # This is expected behavior - credentials will need to be re-entered
                logger.debug("Keyring not available - credentials cannot be stored persistently")
                raise AuthenticationError("Credential storage not available - keyring backend missing")
                
        except AuthenticationError:
            # Re-raise authentication errors as-is
            raise
        except Exception as e:
            logger.debug(f"Failed to store credentials: {e}")
            raise AuthenticationError(f"Failed to store credentials: {e}") from e

    def retrieve_credentials(self) -> dict[str, Any] | None:
        """
        Retrieve and decrypt credentials from keyring.

        Returns:
            Dictionary of credentials or None if not found
        """
        if not self._keyring_available:
            logger.debug("Keyring not available - no stored credentials")
            return None
            
        try:
            # Get from keyring
            encoded_data = keyring.get_password(self.SERVICE_NAME, self.user_id)
            if not encoded_data:
                logger.debug("No stored credentials found")
                return None

            # Decrypt credentials
            encrypted_data = base64.urlsafe_b64decode(encoded_data.encode())
            decrypted_data = self._cipher.decrypt(encrypted_data)
            credentials_raw = json.loads(decrypted_data.decode())

            # Ensure we have a dictionary
            if not isinstance(credentials_raw, dict):
                logger.debug("Invalid credentials format in storage")
                return None

            credentials: dict[str, Any] = credentials_raw
            logger.debug("Credentials retrieved successfully")
            return credentials
        except Exception as e:
            logger.debug(f"Failed to retrieve credentials: {e}")
            return None

    def delete_credentials(self) -> None:
        """
        Delete credentials from keyring.
        """
        if not self._keyring_available:
            logger.debug("Keyring not available - no credentials to delete")
            return
            
        try:
            keyring.delete_password(self.SERVICE_NAME, self.user_id)
            keyring.delete_password(self.SERVICE_NAME, f"{self.user_id}_key")
            logger.debug("Credentials deleted successfully")
        except Exception as e:
            logger.debug(f"Failed to delete credentials: {e}")
