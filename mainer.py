import re
import requests
import html
import json
import random
import string
import math
import time
import os

from http.cookiejar import LWPCookieJar

URL='https://fpminer.com'
JUMLAH_WD=0.0001

ses=requests.Session()
ses.headers.update({
  'Authority': 'fpminer.com',
  'Accept': 'text/html, application/xhtml+xml',
  'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
  'Content-Type': 'application/json',
  'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
  'sec-ch-ua-mobile': '?1',
  'sec-ch-ua-platform': '"Android"',
  'sec-fetch-dest': 'empty',
  'sec-fetch-mode': 'cors',
  'sec-fetch-site': 'same-origin',
  'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-M236B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
  'X-Livewire': 'true'
})
ses.cookies=LWPCookieJar()

class _gData:
   def __init__(self, url):
      self._res=ses.get(url).text

   def get_csrf_token(self):
      reg=re.search('(?<="csrf-token"\scontent\=")([^"]+)', self._res)
      if reg:
         return reg.group(0)

   def get_livewire_data(self, name):
      reg=re.findall('(?<=wire\:initial\-data\=")([^"]+)', self._res)
      return (list(filter(lambda x:x["fingerprint"]["name"]==name,map(lambda x: json.loads(html.unescape(x)), reg))) or [{}])[0]

   def get_b36(self):
      int2base = lambda a, b: ''.join(
          [(string.digits +
            string.ascii_lowercase +
            string.ascii_uppercase)[(a // b ** i) % b]
           for i in range(int(math.log(a, b)), -1, -1)]
      )

      return int2base(int(str(random.random()+1).split('.')[-1]), 36)[7:]


class Bot:
   def __init__(self, w_address=''):
      self.data_login={}
      self.csrf_token=None
      self.w_address=w_address

   def _geror(self):
      if self.data_login:
         print(self.data_login['serverMemo']['errors'])

   def wd(self):
      if not 'redirect' in self.data_login["effects"]:
         exit('\nkesalahan: silahkan on-off kan mode pesawat')

      _data=_gData(self.data_login["effects"]["redirect"])
      data=_data.get_livewire_data('withdrawal')
      jumlah_wd=data["serverMemo"]["data"]["max_withdraw"]
      data.update({"updates":
         [
            {
               "type": "syncInput",
               "payload": {
                   "id": _data.get_b36(),
                   "name": "amount",
                   "value": str(jumlah_wd)
               }
            },
            {
               "type":"callMethod",
               "payload":{
                  "id": _data.get_b36(),
                  "method":"calcFees",
                  "params":[]
                }
            },
            {
               "type":"callMethod",
               "payload":{
                  "id": _data.get_b36(),
                  "method":"withdrawal",
                  "params":[]
               }
            }
         ]
      })
      resp=ses.post(f'{URL}/livewire/message/withdrawal',headers={
         "Content-Type": "application/json",
         "X-CSRF-Token": self.csrf_token,
      },json=data)

      if resp.status_code==200:
         return resp.json()


   def get_balance(self, delay=60):
      if not 'redirect' in self.data_login["effects"]:
         print(self._geror())
         exit('\nkesalahan: silahkan on-off kan mode pesawat')
      resp1=ses.get(self.data_login["effects"]["redirect"], timeout=(10,delay), verify=True)
      rtxt=re.search('(?<=balance_value\s\=\s)([.\d]+)', resp1.text)
      if rtxt:
         return rtxt.group()

   def login_claim(self, w_address=''):
      _data=_gData(URL)
      csrf_token=_data.get_csrf_token()
      data=_data.get_livewire_data('login')
      data.update({'updates': [
        {
          "type": "syncInput",
          "payload": {
            "id": _data.get_b36(),
            "name": "wallet",
            "value": w_address or self.w_address
          }
        },
        {
          "type": "callMethod",
          "payload": {
            "id": _data.get_b36(),
            "method": "start",
            "params": []
          }
        }
      ]})

      resp=ses.post(f'{URL}/livewire/message/login',
         headers={
             "Content-Type": "application/json",
             "X-CSRF-Token": csrf_token
      },json=data)

      if resp.status_code==200:
         self.csrf_token=csrf_token
         self.data_login=resp.json()
         return True


if __name__ == '__main__':
   os.system('clear')
   waddress=input(f'''

   silahkan masukkan address DOGE (faucetpay.io)
   ex: \033[96mD6mcwUx7QYguZNZRYA3hWwqsW6Lk1KMHH3\033[0m
   wd otomatis jika saldo sudah sampai \033[95m{JUMLAH_WD}\033[0m DOGE

   \n+ address(DOGE): ''')
   delay=input('+ delay default=10: ')
   if not delay.isdigit():
      delay=10
   delay=int(delay)
   if delay < 10:
      delay=10
   bot=Bot(waddress)
   if bot.login_claim():
      print(''.ljust(os.get_terminal_size().columns,'-'))
      print(f'berhasil login: \033[92m{waddress}\033[0m')
      print(f'otomatis klaim dengan delay: {delay} detik')
      while True:
         print(time.strftime('\033[94m[%H:%M:%S]\033[0m'), end=' ')
         try:
            balance=bot.get_balance(delay=delay)
            if balance:
               if float(balance) > JUMLAH_WD:
                  wd=bot.wd()
                  if wd:
                     print(f'berhasil wd: \033[95m{wd["serverMemo"]["data"]["final_amount"]}\033[0m DOGE', flush=True)
                     continue
               print(f'delay \033[93m{delay}s\033[0m: \033[95m{balance}\033[0m DOGE', flush=True)
            time.sleep(delay)
         except requests.exceptions.ConnectionError:
            print(f'error', flush=True)
         except KeyboardInterrupt:
            input('\n[ enter ] ')
            break
