const ctx = document.getElementById('bottleChart').getContext('2d');

var bottleChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['GOOD', 'CRUMPLED'],
        datasets: [{
            data: [
                parseInt(document.getElementById('good-count').textContent),
                parseInt(document.getElementById('crumpled-count').textContent)
            ],
            backgroundColor: ['#00c853', '#d50000']
        }]
    },
    options: {
        responsive: true,
        animation: {
            animateScale: true,
            animateRotate: true
        }
    }
});

function updateChart() {
    bottleChart.data.datasets[0].data = [
        parseInt(document.getElementById('good-count').textContent),
        parseInt(document.getElementById('crumpled-count').textContent)
    ];
    bottleChart.update();
}
