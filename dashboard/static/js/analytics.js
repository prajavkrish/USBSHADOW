async function loadSummary() {
  const response = await fetch("/api/analytics/summary");
  return response.json();
}

function chart(id, label, values, colors) {
  new Chart(document.getElementById(id), {
    type: "bar",
    data: {
      labels: Object.keys(values),
      datasets: [{ label, data: Object.values(values), backgroundColor: colors }]
    },
    options: {
      scales: {
        x: { ticks: { color: "#e9eef3" }, grid: { color: "#2b3540" } },
        y: { ticks: { color: "#e9eef3" }, grid: { color: "#2b3540" }, beginAtZero: true }
      },
      plugins: { legend: { labels: { color: "#e9eef3" } } }
    }
  });
}

loadSummary().then((data) => {
  chart("threats", "Incidents", data.threats, ["#00ff9c", "#ffd166", "#ff3d71"]);
  chart("platforms", "Devices", data.platforms, ["#00d8ff"]);
  chart("events", "Events", data.events, ["#9b7cff"]);
});
