import requests
from concurrent.futures import ThreadPoolExecutor

class MarketReader:
    def __init__(self, gui=None, ocr=None):
        self.api_str = "https://api.warframe.market/v1/items"
        self.region = "en"
        self.platform = "pc"
        self.gui = gui
        self.ocr = ocr
        self.prime_items = None
        self.exit_now = False
        self.ducats = {}
        self.headers = {'Platform': self.platform, 'Region': self.region}
        self.primes = []
        self.threads = 4
        self.price_csv = 'resources\\allprice.csv'
        self.ducats_csv = 'resources\\ducats.csv'
        self.primes_txt = 'resources\\primes.txt'
        self.prime_dict_list = None

    def get_prime_items(self):
        if self.prime_items is None:
            response = requests.get(self.api_str)
            json_response = response.json()
            items = json_response['payload']['items']
            self.prime_items = [x for x in items if "Prime " in x['item_name'] and not x['item_name'].endswith("Set")]
            if self.gui is None:
                print("Found {} primes".format(len(self.prime_items)))
            else:
                self.gui.update_primes_info(len(self.prime_items), self.prime_items[-1]['item_name'])
            self.update_prime_dict()

    def update_prime_dict(self):
        prime_dict = set()
        for prime_item in self.prime_items:
            words = prime_item['item_name'].split(" ")
            prime_dict = prime_dict.union(words)
        self.prime_dict_list = list(prime_dict)
        self.prime_dict_list.sort()
        if self.ocr is not None:
            self.ocr.prime_dict = self.prime_dict_list
        with open(self.primes_txt, 'w') as c:
            c.write("\n".join(self.prime_dict_list))

    def update_ducats_sub(self, url_name, item_name):
        if self.exit_now:
            return
        response = requests.get("{}/{}".format(self.api_str, url_name), headers=self.headers)
        if self.exit_now:
            return
        json_response = response.json()
        ducat = 0
        for item in json_response['payload']['item']['items_in_set']:
            if item['url_name'] == url_name:
                ducat = self.safe_cast(item['ducats'], int, 0)
                break

        self.ducats[item_name] = ducat
        if self.gui is None:
            print("{}/{}: {},{}".format(len(self.ducats), len(self.prime_items), item_name, ducat))
        elif len(self.ducats) % int(len(self.prime_items) / 100) == 0:
            self.set_ducats_progress()

    def update_ducats(self):
        self.get_prime_items()
        self.ducats = {}
        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            for prime in self.prime_items:
                ex.submit(self.update_ducats_sub, prime['url_name'], prime['item_name'])
            ex.shutdown(wait=True)

        if self.ocr is not None:
            self.ocr.ducats = self.ducats
            self.ocr.ducats["Forma Blueprint"] = 0
        self.update_ducats_csv()
        if self.gui is not None:
            self.gui.finished_update_progress()
            self.gui.update_ducats_time()

    def update_ducats_csv(self):
        with open(self.ducats_csv, 'w') as c:
            c.write('"Item","Ducats"\n')
            for prime in self.ducats:
                c.write("{},{}\n".format(prime, self.ducats[prime]))

    def set_prices_progress(self):
        self.gui.update_prices_progress.setValue(len(self.primes))

    def set_ducats_progress(self):
        self.gui.update_ducats_progress.setValue(len(self.ducats))

    def update_prices_sub(self, url_name, item_name):
        if self.exit_now:
            return
        response = requests.get("{}/{}/orders".format(self.api_str, url_name), headers=self.headers)
        if self.exit_now:
            return
        json_response = response.json()

        orders = json_response['payload']['orders']
        selling = [x for x in orders if x["user"]["status"] == "ingame" and x["order_type"] == "sell"]
        status = "Online"
        price = 0
        if len(selling) == 0:
            selling = [x for x in orders if x["order_type"] == "sell"]
            status = "Offline"
        if len(selling) == 0:
            selling = [x for x in orders if x["order_type"] == "buy"]
            if len(selling) == 0:
                status = "Unlisted"
            else:
                price = max([x["platinum"] for x in selling])
                status = "Buying"
        else:
            price = min([x["platinum"] for x in selling]) - 1
        price = int(price)
        self.primes.append((item_name, price, status))
        if self.gui is None:
            print("{}/{}: {},{},{}".format(len(self.primes), len(self.prime_items), item_name, price, status))
        elif len(self.primes) % int(len(self.prime_items) / 100) == 0:
            self.set_prices_progress()

    def update_prices(self):
        self.get_prime_items()
        self.primes = []
        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            for prime in self.prime_items:
                ex.submit(self.update_prices_sub, prime['url_name'], prime['item_name'])
            ex.shutdown(wait=True)
        self.update_prices_csv()
        if self.ocr is not None:
            self.ocr.prices = {prime[0]: self.safe_cast(prime[1], int, 0) for prime in self.primes}
            self.ocr.prices["Forma Blueprint"] = 0
        self.update_prices_csv()
        if self.gui is not None:
            self.gui.finished_update_progress()
            self.gui.update_prices_time()

    def update_prices_csv(self):
        with open(self.price_csv, 'w') as c:
            c.write('"Item","Plat","Status"\n')
            for prime in self.primes:
                c.write("{},{},{}\n".format(prime[0],prime[1],prime[2]))

    def set_num_threads(self, val):
        self.threads = val

    def safe_cast(self, val, to_type, default=None):
        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default


if __name__ == "__main__":
    reader = MarketReader()
    reader.update_ducats()
    reader.exit_now = True
