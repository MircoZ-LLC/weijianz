import yfinance as yf
from datetime import datetime

TICKERS = ["TLT", "MSFT", "AMZN", "GOOG", "SNDK", "VOO"]

def fetch_price(ticker):
    t = yf.Ticker(ticker)
    info = t.fast_info
    price = info.last_price
    prev  = info.previous_close or price
    return price, (price - prev) / prev * 100

rows = []
for ticker in TICKERS:
    try:
        price, chg = fetch_price(ticker)
        arrow = "▲" if chg >= 0 else "▼"
        color = "🟢" if chg >= 0 else "🔴"
        rows.append(f"| {ticker} | ${price:,.2f} | {color} {arrow} {abs(chg):.2f}% | — |")
        print(f"{ticker}: ${price:.2f} ({chg:+.2f}%)")
    except Exception as e:
        rows.append(f"| {ticker} | N/A | — | — |")
        print(f"{ticker}: ERROR - {e}")

rows.append("| Pokémon TCG Cards | — | — | — |")

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

lines = [
    "---",
    'title: "Investment"',
    'description: "Market notes, portfolio thoughts, and investment research"',
    "showDate: false",
    "showReadingTime: false",
    "---",
    "",
    "## Current Holdings",
    "",
    "| Ticker / Asset | Price | Day Change | % of Portfolio |",
    "|----------------|-------|------------|---------------|",
] + rows + [
    "",
    f"*Last updated: {now} · Auto-refreshed by GitHub Actions*",
    "",
]

with open("content/investment/_index.md", "w") as f:
    f.write("\n".join(lines))

print("Done")
