import asyncio
import os
import random
from io import BytesIO

import aiohttp
import validators
from hanger import Image
from hanger.ext import commands
from hangups import get_auth_stdin


with open('./refresh-token.txt', 'w+') as _write_mode:
    _write_mode.write(os.environ['REFRESH_TOKEN'])


bot = commands.Bot('/', cookies=get_auth_stdin('./refresh-token.txt', manual_login=True))


@bot.event
async def on_ready():
    bot._session = aiohttp.ClientSession()
    bot._giphy_api_key = os.environ['GIPHY_API_KEY']
    
    print('Ready!')


@bot.command(aliases=['stickers'])
async def giphy(ctx, *query):
    await ctx.conversation.focus(15)
    _type = 'gifs' if ctx.command == 'giphy' else 'stickers'

    query = ' '.join(query)

    if not validators.url(query):
        async with bot._session.get(f'https://api.giphy.com/v1/{_type}/search',
                                    params={'api_key': bot._giphy_api_key,
                                            'q': query, 'limit': 100, 'offset': 0,
                                            'rating': 'PG-13', 'lang': 'en'}) as resp:
            try:
                query = random.choice((await resp.json())['data'])['url']
            except IndexError:
                await ctx.conversation.send('Something broke... we might have gotten '
                                            'rate-limited.\nTelling my owner now!')
                print(await resp.json())

    _id = query.split('-')[-1].strip()
    file = BytesIO()

    async with bot._session.get(f'https://media.giphy.com/media/{_id}/giphy.gif') as resp:
        file.write(await resp.read())

    file.seek(0)
    await ctx.send(image=Image(
        bot, file, filename='giphy.gif'
    ))

    await ctx.conversation.focus(15)


asyncio.run(bot.connect())
