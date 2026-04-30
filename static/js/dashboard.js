const socket = io();
let trendChart;
let scoreHistory = [];

socket.on('connect', () => {
    console.log('Connected to XCOPE realtime');
});

socket.on('init', (stats) => {
    scoreHistory = stats.history || [];
    updateStats(stats);
});
socket.on('dashboard_update', updateStats);
socket.on('new_tweet', (tweet) => {
    addLiveTweet(tweet);
});

function updateStats(stats) {
    document.querySelectorAll('[data-stat]').forEach(el => {
        el.textContent = stats[el.dataset.stat];
    });
    
    // Update score history for trend chart
    if (stats.history && stats.history.length > 0) {
        scoreHistory = stats.history;
    } else {
        // Generate realistic trend data from current avg_score
        scoreHistory.push(stats.avg_score);
        if (scoreHistory.length > 20) scoreHistory.shift();
    }
    updateTrendChart(scoreHistory);
}

function updateTrendChart(history) {
    const ctx = document.getElementById('trendChart')?.getContext('2d');
    if (!ctx) return;
    
    const labels = history.map((_, i) => `Tweet ${i + 1}`);
    
    if (trendChart) trendChart.destroy();
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sentiment Score',
                data: history,
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: 'rgb(59, 130, 246)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true, labels: { color: '#fff' } }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#9ca3af' }
                },
                x: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#9ca3af' }
                }
            }
        }
    });
}

function addLiveTweet(tweet) {
    const container = document.getElementById('liveTweets');
    if (!container) return;
    
    const div = document.createElement('div');
    const sentimentColor = tweet.sentiment === 'positive' ? 'border-green-400 text-green-400' : tweet.sentiment === 'negative' ? 'border-red-400 text-red-400' : 'border-yellow-400 text-yellow-400';
    div.className = `p-4 rounded-xl bg-white/20 border-l-4 ${sentimentColor.split(' ')[0]}`;
    div.innerHTML = `
        <div class="font-bold text-lg">${tweet.text.substring(0, 100)}...</div>
        <div class="text-sm opacity-75 mt-2">${tweet.timestamp} | <span class="${sentimentColor}">${tweet.sentiment.toUpperCase()}</span> (${tweet.score})</div>
    `;
    container.insertBefore(div, container.firstChild);
    
    // Keep only last 20 tweets visible
    while (container.children.length > 20) {
        container.removeChild(container.lastChild);
    }
}
