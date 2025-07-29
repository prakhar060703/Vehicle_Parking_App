document.addEventListener("DOMContentLoaded", () => {
  const jsonData = document.getElementById("summary-data");
  if (!jsonData) return;

  const { lots, users, reservations } = JSON.parse(jsonData.textContent);

  renderSummaryChart(lots, users, reservations);
});

function renderSummaryChart(lotCount, userCount, reservationCount) {
  const ctx = document.getElementById("summaryChart").getContext("2d");

  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Parking Lots', 'Users', 'Reservations'],
      datasets: [{
        data: [lotCount, userCount, reservationCount],
        backgroundColor: ['#4caf50', '#2196f3', '#ff9800'],
        borderWidth: 1
      }]
    },
    options: {
      responsive: false,
      plugins: {
        legend: {
          position: 'bottom'
        },
        title: {
          display: true,
          text: 'System Summary'
        }
      }
    }
  });
}
