from flask import Flask, render_template, jsonify, request

from kernel.stock import StockTracker, search_market

app = Flask(__name__)


@app.route('/')
def index():
    stocks = StockTracker().fetch_holdings()

    mkt = search_market([s['symbol'] for s in stocks])
    for s in stocks:
        df = mkt[s.get('symbol')]
        s['close'] = df['close']
        s['rate'] = (s['close'] - s['price']) / s['price']

    return render_template('index.html', stocks=stocks)


@app.route('/transaction', methods=["POST", "GET"])
def transaction():
    msg = 'er'
    tracker = StockTracker()
    if request.method == 'POST':
        symbol = request.form['symbol']
        volume = request.form['volume']
        price = request.form['price']
        status = request.form['status']

        if status == 'sell':
            res = tracker.sell(symbol, int(volume), float(price))
            msg = 'ok' if res else 'er'
        else:
            tracker.buy(symbol, int(volume), float(price))
            msg = 'ok'

    return jsonify(msg)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
