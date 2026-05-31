import urllib.request, json

stocks = ["600519", "000858", "000001", "002115", "300750", "601318"]
strategies = ["ma_cross", "volume_breakout", "dragon_follow"]

print(f"{'Stock':<8} {'Strategy':<20} {'Trades':>6} {'Win%':>6} {'Return':>8} {'Sharpe':>7} {'MaxDD':>7} {'AvgPnL':>8}")
print("-" * 80)

for sym in stocks:
    for strat in strategies:
        try:
            url = f"http://localhost:8005/api/analysis/backtest?symbol={sym}&strategy={strat}&initial_capital=500000"
            req = urllib.request.Request(url, method="POST")
            resp = urllib.request.urlopen(req, timeout=30)
            d = json.loads(resp.read())
            m = d["metrics"]
            print(f"{sym:<8} {strat:<20} {m['total_trades']:>6} {m['win_rate']*100:>5.1f}% {m['total_return']*100:>+7.2f}% {m['sharpe_ratio']:>7.2f} {m['max_drawdown']*100:>6.2f}% {m['avg_pnl']*100:>+7.2f}%")
        except Exception as e:
            print(f"{sym:<8} {strat:<20} ERROR: {str(e)[:40]}")
