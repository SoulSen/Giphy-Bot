import asyncio
import os

import hangups
from hangups import CredentialsPrompt, RefreshTokenCache

from hanger import Client

print(os.listdir())
asyncio.run(Client(
    hangups.get_auth_stdin(
        './refresh-token.txt',
        manual_login=True)
)._hangups_client.connect())
