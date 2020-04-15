import asyncio
import os
import random
import re
import traceback
from io import BytesIO

import aiohttp
import validators
from aiohttp import ClientResponseError
from hanger import Image
from hanger.ext import commands
from loguru import logger

with open('./refresh-token.txt', 'w+') as _write_mode:
    _write_mode.write(os.environ['REFRESH_TOKEN'])


time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h":3600, "s":1, "m":60, "d":86400}
bot = commands.Bot('/', refresh_token='./refresh-token.txt')


@bot.event
async def on_ready():
    bot._session = aiohttp.ClientSession()
    bot._giphy_api_key = os.environ['GIPHY_API_KEY']
    bot._owner = os.environ['OWNER_EMAIL']
    bot._latest_query = ''

    print('Ready!')


@bot.command(aliases=['stickers'])
async def giphy(ctx, *query):
    async with ctx.conversation.focused(), ctx.conversation.typing():
        _type = 'gifs' if ctx.command == 'giphy' else 'stickers'
        query = ' '.join(query)

        logger.info(f'{ctx.user.fallback_name} is querying for {_type}, and is looking for {query}')

        if not validators.url(query):
            logger.info(f'{ctx.user.fallback_name} query was a url')
            async with bot._session.get(f'https://api.giphy.com/v1/{_type}/search',
                                        params={'api_key': bot._giphy_api_key,
                                                'q': query, 'limit': 100, 'offset': 0,
                                                'rating': 'PG-13', 'lang': 'en'},) as resp:
                logger.info(f'{ctx.user.fallback_name} is now requesting to the Giphy API')
                json = await resp.json()
                try:
                    resp.raise_for_status()
                    gif_entries = json['data']

                    if len(gif_entries) == 0:
                        logger.info(f'{ctx.user.fallback_name} got no results from his / her query')
                        return await ctx.respond('No results found...')

                    query = random.choice(gif_entries)['url']
                except ClientResponseError as e:
                    logger.exception(f'{ctx.user.fallback_name} got a bad response from the Giphy API')
                    await ctx.conversation.send('Something broke... we might have gotten '
                                                'rate-limited.\nTelling my owner now!')
                    await notify_owner(ctx, bot, f'{traceback.format_exc()}\nJSON Response: {json}')
                    raise e

        _id = query.split('-')[-1].strip()
        bot._latest_query = f'Giphy Query: {query}\nGiphy ID: {_id}'
        logger.info(f'Giphy Query: {query}\nGiphy ID: {_id}')
        file = BytesIO()

        async with bot._session.get(f'https://media.giphy.com/media/{_id}/giphy.gif') as resp:
            file.write(await resp.read())

        file.seek(0)
        await ctx.send(image=Image(
            bot, file, filename='giphy.gif'
        ))


@bot.command()
async def latest_query(ctx):
    if ctx.user.canonical_email == ctx.bot._owner:
        await ctx.respond(ctx.bot._latest_query)


@bot.command()
async def tempmute(ctx, member, time):
    if ctx.user.canonical_email == ctx.bot._owner:
        args = time.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k]*float(v)
            except KeyError:
                return await ctx.respond("{} is an invalid time-key! h/m/s/d are valid!".format(k))
            except ValueError:
                return await ctx.respond("{} is not a number!".format(v))

        user = await ctx.bot.fetch_user(email=member)
        participant = ctx.conversation.get_participant(user.id)
        await ctx.conversation.remove_user(participant)
        await asyncio.sleep(time)
        await ctx.conversation.add_user(user)


async def notify_owner(ctx, bot, error):
    async with bot._session.get('http://hasteb.in/documents', data=error) as resp:
        try:
            resp.raise_for_status()
            owner = bot.fetch_user(email=bot._owner)
            key = await resp.json()['key']
            await owner.send(f'Something went wrong...\n'
                             f'Sender: {ctx.user.fallback_name}\n'
                             f'Message: {ctx.message}\n'
                             f'Traceback: https://hasteb.in/{key}.py')
        except ClientResponseError as e:
            await ctx.conversation.send('Something really really broke... notify my owner please!')
            raise e


bot.connect()
