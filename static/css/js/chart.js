document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("attendanceChart");
  if (!canvas) return;

  // Get labels and values from data attributes
  const labels = JSON.parse(canvas.dataset.labels || "[]");
  const values = JSON.parse(canvas.dataset.values || "[]");

  if (labels.length === 0) {
    console.warn("No chart data found.");
    return;
  }

  const ctx = canvas.getContext("2d");

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Attendance Percentage",
          data: values,
          backgroundColor: values.map(v =>
            v >= 75
              ? "rgba(76, 175, 80, 0.7)"   // green
              : v >= 50
              ? "rgba(255, 152, 0, 0.7)"  // orange
              : "rgba(244, 67, 54, 0.7)"  // red
          ),
          borderColor: values.map(v =>
            v >= 75
              ? "rgba(76, 175, 80, 1)"
              : v >= 50
              ? "rgba(255, 152, 0, 1)"
              : "rgba(244, 67, 54, 1)"
          ),
          borderWidth: 2,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#333",
          titleFont: { size: 14 },
          bodyFont: { size: 13 },
          callbacks: {
            label: (context) => `${context.parsed.y}% attendance`,
          },
        },
        title: {
          display: true,
          text: "Lecture-wise Attendance Performance",
          font: { size: 16, weight: "bold" },
          color: "#333",
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: { display: true, text: "Attendance (%)" },
          ticks: { stepSize: 25 },
        },
        x: {
          ticks: { color: "#444" },
        },
      },
      animation: {
        duration: 1500,
        easing: "easeOutBounce",
      },
    },
  });
});
