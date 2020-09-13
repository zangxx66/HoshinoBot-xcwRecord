from quart import request, make_response, Response
import asyncio
import nonebot
import re
import json
import time
import base64
from . import sv
from .arena import http_query
from .. import chara
from itertools import zip_longest

bot = nonebot.get_bot()
app = bot.server_app
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = 'SBDNFIEWQODN'
anhao_sb = 'ueめんなさい'


@app.route('/arena/query', methods=['POST'])
async def query():
    authorization = request.headers['authorization']
    try:
        anhao = str(base64.b64decode(authorization), 'eucjp')
        if anhao != anhao_sb:
            response = await gen_response('error:\nwho are you')
            return response
    except Exception as ex:
        sv.logger.error(ex)
        response = await gen_response('error:\nwdnmd')
        return response
    reqs = await request.get_json()
    key = int(reqs['ts'])
    now = time.time()
    if now < key:
        response = await gen_response('error\ninvalid ts')
        return response
    if now - key > 20:
        response = await gen_response('error:\ninvalid ts')
        return response
    defen = reqs['def']
    if isinstance(defen, list) is False:
        response = await gen_response('error:\ninvalid parameter')
        return response
    if len(defen) < 5:
        response = await gen_response('error:\nnot enough length')
        return response
    if len(defen) > 5:
        response = await gen_response('error:\ninvalid length')
        return response
    if len(defen) != len(set(defen)):
        response = await gen_response('error:\nrepeating elements')
        return response
    if any(chara.is_npc((i - 1)/100) for i in defen):
        response = await gen_response('error:\ninvalid element')
        return response
    reg = reqs['region']
    result = await http_query(id_list=defen, user_id=0, region=reg, force=False)
    if isinstance(result, str):
        result = f'error:\n{result}'
    elif not len(result):
        result = 'error:\nno homework'
    else:
        result = [v for v in result]
        result = json.dumps(result, ensure_ascii=False)
        # sv.logger.info(f'[query INFO]:{result}')
    response = await gen_response(result)
    return response


async def gen_response(result: str) -> Response:
    response = await make_response(result, {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache'
    })
    response.timeout = None
    return response
