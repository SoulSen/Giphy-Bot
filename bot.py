import os
import random
import sys
import traceback
from io import BytesIO

import aiohttp
import validators
from aiohttp import ClientResponseError
from hanger import Image
from hanger.ext import commands
from loguru import logger

from datawriter import DataWriter

with open('./refresh-token.txt', 'w+') as _write_mode:
    _write_mode.write(os.environ['REFRESH_TOKEN'])

bot = commands.Bot('/', refresh_token='./refresh-token.txt')
original_stderr = sys.__stderr__


@bot.event
async def on_ready():
    bot._session = aiohttp.ClientSession()
    bot._giphy_api_key = os.environ['GIPHY_API_KEY']
    bot._owner = os.environ['OWNER_EMAIL']
    bot._latest_query = ''

    sys.stderr = DataWriter(terminal=original_stderr)
    sys.__stderr__ = sys.stderr

    print('Ready!')


@bot.command(aliases=['stickers'])
async def giphy(ctx, *query):
    async with ctx.conversation.focused(), ctx.conversation.typing():
        _type = 'gifs' if ctx.command == 'giphy' else 'stickers'
        query = ' '.join(query)

        logger.info(f'{ctx.author.fallback_name} is querying for {_type}, and is looking for {query}')

        if not validators.url(query):
            logger.info(f'{ctx.author.fallback_name} query was not a url')
            async with ctx.bot._session.get(f'https://api.giphy.com/v1/{_type}/search',
                                            params={'api_key': ctx.bot._giphy_api_key,
                                                    'q': query, 'limit': 50, 'offset': 0,
                                                    'rating': 'PG-13', 'lang': 'en'}, ) as resp:
                logger.info(f'{ctx.author.fallback_name} is now requesting to the Giphy API')
                json = await resp.json()
                try:
                    resp.raise_for_status()
                    gif_entries = json['data']

                    if len(gif_entries) == 0:
                        logger.info(f'{ctx.author.fallback_name} got no results from his / her query')
                        return await ctx.respond('No results found...')

                    query = random.choice(gif_entries)['url']
                except ClientResponseError as e:
                    logger.exception(f'{ctx.author.fallback_name} got a bad response from the Giphy API')
                    await ctx.conversation.send('Something broke... we might have gotten '
                                                'rate-limited.\nTelling my owner now!')
                    await notify_owner(ctx, f'{traceback.format_exc()}\nJSON Response: {json}')
                    raise e

        tag = query.split('/')[-1].strip()
        _id = tag.split('-')[-1].strip()
        bot._latest_query = f'Giphy Query: {query}\nGiphy ID: {_id}'
        logger.info(f'Giphy Query: {query} | Giphy ID: {_id}')
        file = BytesIO()

        async with ctx.bot._session.get(f'https://media.giphy.com/media/{_id}/giphy.gif') as resp:
            file.write(await resp.read())

        file.seek(0)
        await ctx.respond(image=Image(
            bot, file, filename='giphy.gif'
        ))


@bot.command()
async def debug(ctx):
    if ctx.author.canonical_email == ctx.bot._owner:
        async with ctx.bot._session.get('http://hasteb.in/documents',
                                        data=sys.__stderr__.readlines()) as resp:
            try:
                resp.raise_for_status()
                owner = await ctx.bot.fetch_user(email=ctx.bot._owner)
                key = (await resp.json())['key']
                await owner.send(f'Logs: https://hasteb.in/{key}.py')
            except ClientResponseError as e:
                logger.exception(f'Could not post debug to hasteb.in')
                await ctx.conversation.send('Bing bong your code sucks ding dong')
                raise e


async def notify_owner(ctx, error):
    async with ctx.bot._session.get('http://hasteb.in/documents', data=error) as resp:
        try:
            resp.raise_for_status()
            owner = await ctx.bot.fetch_user(email=ctx.bot._owner)
            key = (await resp.json())['key']
            await owner.send(f'Something went wrong...\n'
                             f'Sender: {ctx.author.fallback_name}\n'
                             f'Message: {ctx.message}\n'
                             f'Traceback: https://hasteb.in/{key}.py')
        except ClientResponseError as e:
            logger.exception(f"{ctx.author.fallback_name}'s error was not able to be posted to hasteb.in")
            await ctx.conversation.send('Something really really broke... notify my owner please!')
            raise e


bot.connect()
