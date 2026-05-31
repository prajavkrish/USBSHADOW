const summary = window.usbshadowThreatSummary || {};
const ctx = document.getElementById("threatChart");
new Chart(ctx, {
  type: "doughnut",
  data: {
    labels: Object.keys(summary).length ? Object.keys(summary) : ["No Incidents"],
    datasets: [{
      data: Object.values(summary).length ? Object.values(summary) : [1],
      backgroundColor: ["#00ff9c", "#ffd166", "#ff3d71", "#1e3a48"],
      borderColor: "#0b131a",
      borderWidth: 2,
      hoverOffset: 3
    }]
  },
  options: {
    maintainAspectRatio: false,
    cutout: "68%",
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          boxWidth: 10,
          color: "#eaf7ff",
          padding: 14
        }
      }
    }
  }
});
