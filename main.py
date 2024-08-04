import asyncio
import aiohttp
import time
import random
import uuid
import os

app_token = 'd28721be-fd2d-4b45-869e-9f253b554e50'
promo_id = '43e35910-c168-4634-ad4f-52fd764a843f'

# إعدادات Telegram
telegram_bot_token = '5983976147:AAEBi_6FZM1SP3AQ0fQOkrzNFhjlcNve2V0'
telegram_chat_id = '-1002168723416'

async def generate_client_id():
    timestamp = int(time.time() * 1000)
    random_numbers = ''.join(str(random.randint(0, 9)) for _ in range(19))
    return f"{timestamp}-{random_numbers}"

async def login_client():
    client_id = await generate_client_id()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post('https://api.gamepromo.io/promo/login-client', json={
                'appToken': app_token,
                'clientId': client_id,
                'clientOrigin': 'deviceid'
            }, headers={
                'Content-Type': 'application/json; charset=utf-8',
            }) as response:
                data = await response.json()
                return data['clientToken']
        except Exception as error:
            print(f'Ошибка при входе клиента: {error}')
            await asyncio.sleep(5)
            return await login_client()  # Recursive call

async def register_event(token):
    event_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post('https://api.gamepromo.io/promo/register-event', json={
                'promoId': promo_id,
                'eventId': event_id,
                'eventOrigin': 'undefined'
            }, headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json; charset=utf-8',
            }) as response:
                data = await response.json()
                if not data.get('hasCode', False):
                    await asyncio.sleep(5)
                    return await register_event(token)  # Recursive call
                else:
                    return True
        except Exception as error:
            await asyncio.sleep(5)
            return await register_event(token)  # Recursive call in case of error

async def create_code(token):
    async with aiohttp.ClientSession() as session:
        response = None
        while not response or not response.get('promoCode'):
            try:
                async with session.post('https://api.gamepromo.io/promo/create-code', json={
                    'promoId': promo_id
                }, headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json; charset=utf-8',
                }) as resp:
                    response = await resp.json()
            except Exception as error:
                print(f'Ошибка при создании кода: {error}')
                await asyncio.sleep(1)
        return response['promoCode']

async def send_to_telegram(message):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage', json={
                'chat_id': telegram_chat_id,
                'text': message
            }) as response:
                return await response.json()
        except Exception as error:
            print(f'Ошибка при отправке сообщения в Telegram: {error}')

async def gen():
    token = await login_client()
    print(token)
    
    await register_event(token)
    code_data = await create_code(token)
    print('Сгенерированный код:', code_data)

    # إرسال النتائج إلى Telegram
    await send_to_telegram(f'Сгенерированный код: {code_data}')

async def main():
    while True:
        try:
            tasks = [gen() for _ in range(4)]
            await asyncio.gather(*tasks)
        except Exception as error:
            print(f'Ошибка: {error}')
        await asyncio.sleep(5)  # إضافة فترة تأخير قصيرة قبل تكرار الحلقة

asyncio.run(main())
