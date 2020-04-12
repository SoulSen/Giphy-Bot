import asyncio

import hangups
from hangups import CredentialsPrompt, RefreshTokenCache

from hanger import Client

asyncio.run(Client(
    hangups.get_auth_stdin(
        RefreshTokenCache('./refresh-token.txt'),
        manual_login=True)
)._hangups_client.connect())
