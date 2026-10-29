
import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from .models import PasswordSetupToken


#-----------------------------------------------------------#
# Generate Password Setup Token
#-----------------------------------------------------------#

# Generates a secure password setup token for a user.
# Stores only the SHA-256 hash of the token in the database.
# The raw token is returned for use in the password setup URL.
def generate_password_setup_token(user):

    # Invalidate any previous unused password setup tokens.
    PasswordSetupToken.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(
        used_at=timezone.now(),
    )

    # Generate a cryptographically secure random token.
    raw_token = secrets.token_urlsafe(32)

    # Convert the raw token into a SHA-256 hash.
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    # Set the token expiration to 24 hours from now.
    expires_at = timezone.now() + timedelta(hours=24)

    # Store the hashed token and its expiration in the database.
    PasswordSetupToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    # Return the raw token for the secure email link.
    return raw_token


#-----------------------------------------------------------#
# Validate Password Setup Token
#-----------------------------------------------------------#

# Finds the token using its hash and checks whether it is valid.
# Returns the token record if valid, otherwise returns None.
def validate_password_setup_token(raw_token):

    # Reject empty or missing tokens.
    if not raw_token:
        return None

    # Hash the raw token before searching the database.
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    # Retrieve the matching token record.
    token_record = (
        PasswordSetupToken.objects
        .select_related("user")
        .filter(token_hash=token_hash)
        .first()
    )

    # Reject tokens that do not exist or are no longer valid.
    if token_record is None or not token_record.is_valid():
        return None

    return token_record
