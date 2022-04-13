from flask import Flask, render_template, jsonify, request, session, redirect, url_for

from kernel.auth import login_required, generate_password
from kernel.stock import StockTracker, search_market

app = Flask(__name__)
app.secret_key = generate_password(9)


@app.before_first_request
def before_first_request():
    global PASSWORD
    PASSWORD = generate_password(6)
    print("SECRET: {}".format(PASSWORD))


@app.route('/login', methods=["POST", "GET"])
def login():
    error = False
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            session['password'] = PASSWORD
            return redirect(url_for('index'))
        else:
            error = True

    return render_template('login.html', error=error)


@app.route('/')
@login_required
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
