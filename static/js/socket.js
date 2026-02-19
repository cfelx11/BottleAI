var socket = io();
const USER_ID = {{ user.id if user else 0 }};

socket.on('update_dashboard', function(data){
    if(data.user_id == USER_ID){
        const logContainer = document.getElementById('log-container');
        const newLog = document.createElement('li');
        newLog.textContent = `${data.prediction} at ${new Date().toLocaleTimeString()}`;
        logContainer.prepend(newLog);
        // Update counters
        document.getElementById('good-count').textContent = parseInt(document.getElementById('good-count').textContent) + (data.prediction=='GOOD'?1:0);
        document.getElementById('crumpled-count').textContent = parseInt(document.getElementById('crumpled-count').textContent) + (data.prediction=='CRUMPLED'?1:0);
    }
});

