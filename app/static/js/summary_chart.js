document.addEventListener("DOMContentLoaded", function () {
  const dataElement = document.getElementById("summary-data");
  if (!dataElement) return;

  const rawData = JSON.parse(dataElement.textContent);

  const labels = rawData.spot_summary.map(item => item.lot);
  const availableData = rawData.spot_summary.map(item => item.available);
  const occupiedData = rawData.spot_summary.map(item => item.occupied);

  const ctx = document.getElementById("summaryChart").getContext("2d");

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Available Spots",
          data: availableData,
          backgroundColor: "green"
        },
        {
          label: "Occupied Spots",
          data: occupiedData,
          backgroundColor: "red"
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: "Parking Spot Status per Lot"
        }
      },
      scales: {
        x: {
          stacked: true
        },
        y: {
          beginAtZero: true,
          stacked: true,
          title: {
            display: true,
            text: "Number of Spots"
          }
        }
      }
    }
  });
});
