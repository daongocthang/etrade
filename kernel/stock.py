import json
from datetime import date
from urllib import request

from kernel.dbase import quote, Table


def cast_date(dt):
    return date.today().strftime('%y-%m-%d') if dt is None else dt


def search_market(symbols):
    res = request.urlopen('https://finfoapi-hn.vndirect.com.vn/stocks/adPrice?symbols={}'.format(','.join(symbols)))
    data = json.loads(res.read())['data']
    if len(data) == 0: return None

    mkt = {}
    for d in data:
        idx = d['symbol']
        mkt[idx] = d

    return mkt


class StockTracker:
    def __init__(self):
        self.tbl = Table('portfolio')
        self.tbl.create_if_not_exists([
            "id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY",
            "symbol VARCHAR(3) NOT NULL",
            "price FLOAT NOT NULL",
            "shares INT NOT NULL",
            "sold FLOAT NULL",
            "date DATE NOT NULL DEFAULT CURRENT_TIMESTAMP"
        ])

    def fetch_holdings(self):
        return self.tbl.where('sold', 'IS', 'NULL').select('*')

    def fetch_all(self):
        return self.tbl.select('*')

    def get(self, symbol):
        self.tbl.where('sold', 'IS', 'NULL')
        self.tbl.where('symbol', '=', quote(symbol))
        self.tbl.limit(1)
        raw = self.tbl.select('*')
        return raw.pop() if raw is not None and len(raw) > 0 else None

    def buy(self, symbol, amount, price, purchase_date=None):
        symbol = symbol.upper()
        cur = self.get(symbol)

        params = {'symbol': symbol,
                  'shares': amount,
                  'price': price,
                  'date': cast_date(purchase_date)}

        if cur is None:
            self.tbl.insert(params)
            return

        params['shares'] += cur['shares']
        params['price'] = (cur['shares'] * cur['price'] + amount * price) / (cur['shares'] + amount)
        self.tbl.where('id', '=', quote(cur['id'])).update(params)

    def sell(self, symbol, amount, price, sale_date=None):
        symbol = symbol.upper()
        cur = self.get(symbol)
        if cur is None: return False

        diff = cur['shares'] - amount
        if diff < 0: return False

        self.tbl.where('id', '=', quote(cur['id']))
        params = {'sold': price, 'date': cast_date(sale_date)} if diff == 0 else {'shares': diff}
        self.tbl.update(params)

        if diff > 0:
            params = {'symbol': symbol,
                      'shares': amount,
                      'price': cur['price'],
                      'sold': price,
                      'date': cast_date(sale_date)}
            self.tbl.insert(params)

        return True


if __name__ == '__main__':
    tracker = StockTracker()
    print(tracker.fetch_holdings())
