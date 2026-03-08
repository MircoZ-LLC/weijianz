---
title: "Investment"
description: "Market notes, portfolio thoughts, and investment research"
showDate: false
showReadingTime: false
---

## Current Holdings

<div id="holdings-table">
  <p style="color:#94a3b8">Loading prices...</p>
</div>

<script>
const HOLDINGS = [
  { ticker: "TLT",  label: "TLT" },
  { ticker: "MSFT", label: "MSFT" },
  { ticker: "AMZN", label: "AMZN" },
  { ticker: "GOOG", label: "GOOG" },
  { ticker: "SNDK", label: "SNDK" },
  { ticker: "VOO",  label: "VOO" },
  { ticker: null,   label: "Pokémon TCG Cards" },
];

async function fetchPrice(ticker) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1d&range=1d`;
  const proxy = `https://corsproxy.io/?url=${encodeURIComponent(url)}`;
  const res = await fetch(proxy);
  const data = await res.json();
  const meta = data.chart.result[0].meta;
  const price = meta.regularMarketPrice;
  const prev  = meta.chartPreviousClose || meta.previousClose || price;
  const changePct = ((price - prev) / prev * 100);
  return { price, changePct };
}

async function render() {
  const container = document.getElementById("holdings-table");

  const results = await Promise.allSettled(
    HOLDINGS.map(h => h.ticker ? fetchPrice(h.ticker) : Promise.resolve(null))
  );

  const now = new Date().toLocaleString("en-US", {
    timeZone: "America/Los_Angeles",
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  });

  let rows = HOLDINGS.map((h, i) => {
    const result = results[i];
    if (!h.ticker) {
      return `<tr><td>${h.label}</td><td>—</td><td>—</td><td>—</td></tr>`;
    }
    if (result.status === "rejected" || !result.value) {
      return `<tr><td>${h.label}</td><td style="color:#f87171">Error</td><td>—</td><td>—</td></tr>`;
    }
    const { price, changePct } = result.value;
    const up = changePct >= 0;
    const color = up ? "#4ade80" : "#f87171";
    const arrow = up ? "▲" : "▼";
    return `<tr>
      <td><strong>${h.label}</strong></td>
      <td>$${price.toLocaleString("en-US", {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
      <td style="color:${color}">${arrow} ${Math.abs(changePct).toFixed(2)}%</td>
      <td>—</td>
    </tr>`;
  }).join("\n");

  container.innerHTML = `
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="border-bottom:1px solid rgba(255,255,255,0.1);color:#94a3b8;font-size:0.85rem;text-transform:uppercase">
          <th style="text-align:left;padding:8px 12px">Asset</th>
          <th style="text-align:left;padding:8px 12px">Price</th>
          <th style="text-align:left;padding:8px 12px">Day Change</th>
          <th style="text-align:left;padding:8px 12px">% of Portfolio</th>
        </tr>
      </thead>
      <tbody style="font-size:1rem">${rows}</tbody>
    </table>
    <p style="color:#475569;font-size:0.8rem;margin-top:0.75rem">
      Last updated: ${now} · <a href="#" onclick="location.reload();return false" style="color:#22d3ee">Refresh</a>
    </p>`;
}

render().catch(err => {
  document.getElementById("holdings-table").innerHTML =
    `<p style="color:#f87171">Failed to load prices: ${err.message}</p>`;
});
</script>
