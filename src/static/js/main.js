// Global variables
let charts = {};
let dataTable;
let map;

// Initialize all components when document is ready
$(document).ready(function() {
    // Initialize date range picker
    $('#dateRange').daterangepicker({
        startDate: moment().subtract(29, 'days'),
        endDate: moment(),
        ranges: {
            'Today': [moment(), moment()],
            'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
            'Last 7 Days': [moment().subtract(6, 'days'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'This Month': [moment().startOf('month'), moment().endOf('month')],
            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        }
    });

    // Check client initialization status on page load
    checkClientStatus();
});

// Credentials panel toggle
function toggleCredentials() {
    const panel = $('#credentialsPanel');
    const mainContent = $('.main-content');
    const toggleBtn = $('.credentials-toggle');
    const toggleText = $('.credentials-toggle-text');
    
    if (panel.hasClass('show')) {
        panel.removeClass('show');
        mainContent.removeClass('shifted');
        toggleText.text('Show Credentials');
    } else {
        panel.addClass('show');
        mainContent.addClass('shifted');
        toggleText.text('Hide Credentials');
    }
}

// Client initialization and status checking
function checkClientStatus() {
    $.get('/api/check-status')
        .done(function(response) {
            updateClientStatus(response.initialized);
            if (!response.initialized) {
                toggleCredentials(); // Show credentials panel if not initialized
            }
        })
        .fail(function(error) {
            console.error('Error checking client status:', error);
            showError('Failed to check client status');
            updateClientStatus(false);
        });
}

function updateClientStatus(isConnected) {
    const statusElement = $('.client-status');
    if (isConnected) {
        statusElement.removeClass('status-disconnected').addClass('status-connected');
        statusElement.text('Connected');
    } else {
        statusElement.removeClass('status-connected').addClass('status-disconnected');
        statusElement.text('Disconnected');
    }
}

// Handle credentials form submission
$('#credentialsForm').on('submit', function(e) {
    e.preventDefault();
    const credentials = {
        developer_token: $('#developerToken').val(),
        client_id: $('#clientId').val(),
        client_secret: $('#clientSecret').val(),
        refresh_token: $('#refreshToken').val()
    };

    $.ajax({
        url: '/api/initialize',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(credentials),
        success: function(response) {
            updateClientStatus(true);
            showSuccess('Client initialized successfully');
            toggleCredentials(); // Hide credentials panel after successful initialization
        },
        error: function(error) {
            updateClientStatus(false);
            showError('Failed to initialize client: ' + error.responseText);
        }
    });
});

// Section loading functions
function loadDashboard() {
    if (!validateInputs()) return;
    $('.data-container').hide();
    $('#dashboardData').show();
    
    $.get('/api/dashboard', getQueryParams())
        .done(function(data) {
            $('#totalLeads').text(data.total_leads);
            $('#conversionRate').text(data.conversion_rate + '%');
            // Add more dashboard metrics as needed
        })
        .fail(handleApiError);
}

function loadLeads() {
    if (!validateInputs()) return;
    $('.data-container').hide();
    $('#leadsData').show();
    
    $.get('/api/leads', getQueryParams())
        .done(function(data) {
            displayLeadsTable(data);
        })
        .fail(handleApiError);
}

function loadCampaigns() {
    if (!validateInputs()) return;
    $('.data-container').hide();
    $('#campaignsData').show();
    
    $.get('/api/campaigns', getQueryParams())
        .done(function(data) {
            displayCampaignMetrics(data);
        })
        .fail(handleApiError);
}

function loadGeographic() {
    if (!validateInputs()) return;
    $('.data-container').hide();
    $('#geographicData').show();
    
    $.get('/api/geographic', getQueryParams())
        .done(function(data) {
            initializeMap(data);
        })
        .fail(handleApiError);
}

function loadCompetitive() {
    if (!validateInputs()) return;
    $('.data-container').hide();
    $('#competitiveData').show();
    
    $.get('/api/competitive', getQueryParams())
        .done(function(data) {
            displayCompetitiveMetrics(data);
        })
        .fail(handleApiError);
}

// Helper functions
function validateInputs() {
    const customerId = $('#customerId').val();
    if (!customerId) {
        showError('Please enter a Customer ID');
        return false;
    }
    return true;
}

function getQueryParams() {
    const dateRange = $('#dateRange').data('daterangepicker');
    return {
        customer_id: $('#customerId').val(),
        start_date: dateRange.startDate.format('YYYY-MM-DD'),
        end_date: dateRange.endDate.format('YYYY-MM-DD')
    };
}

function displayLeadsTable(data) {
    const table = $('<table>').addClass('table table-striped');
    const thead = $('<thead>').append(
        $('<tr>').append(
            $('<th>').text('Date'),
            $('<th>').text('Lead Type'),
            $('<th>').text('Status'),
            $('<th>').text('Details')
        )
    );
    
    const tbody = $('<tbody>');
    data.leads.forEach(lead => {
        tbody.append(
            $('<tr>').append(
                $('<td>').text(lead.date),
                $('<td>').text(lead.type),
                $('<td>').text(lead.status),
                $('<td>').text(lead.details)
            )
        );
    });
    
    table.append(thead, tbody);
    $('#leadsTable').empty().append(table);
}

function displayCampaignMetrics(data) {
    const metricsHtml = data.campaigns.map(campaign => `
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">${campaign.name}</h5>
                <p>Leads: ${campaign.leads}</p>
                <p>Cost: $${campaign.cost}</p>
                <p>Conversion Rate: ${campaign.conversion_rate}%</p>
            </div>
        </div>
    `).join('');
    
    $('#campaignMetrics').html(metricsHtml);
}

function initializeMap(data) {
    if (!window.map) {
        window.map = L.map('performanceMap').setView([39.8283, -98.5795], 4);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: ' OpenStreetMap contributors'
        }).addTo(window.map);
    }
    
    // Clear existing markers
    if (window.markers) {
        window.markers.forEach(marker => marker.remove());
    }
    window.markers = [];
    
    // Add new markers
    data.locations.forEach(location => {
        const marker = L.marker([location.lat, location.lng])
            .bindPopup(`
                <b>${location.city}</b><br>
                Leads: ${location.leads}<br>
                Conversion Rate: ${location.conversion_rate}%
            `)
            .addTo(window.map);
        window.markers.push(marker);
    });
}

function displayCompetitiveMetrics(data) {
    const metricsHtml = `
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">Market Position</h5>
                <p>Market Share: ${data.market_share}%</p>
                <p>Competitive Index: ${data.competitive_index}</p>
                <p>Average Position: ${data.avg_position}</p>
            </div>
        </div>
    `;
    
    $('#competitiveMetrics').html(metricsHtml);
}

function exportToCSV() {
    if (!validateInputs()) return;
    
    $.get('/api/export/csv', getQueryParams())
        .done(function(data) {
            const blob = new Blob([data], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'google_ads_report.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        })
        .fail(handleApiError);
}

function exportToPDF() {
    if (!validateInputs()) return;
    
    $.get('/api/export/pdf', getQueryParams())
        .done(function(data) {
            const blob = new Blob([data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'google_ads_report.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        })
        .fail(handleApiError);
}

function handleApiError(error) {
    console.error('API Error:', error);
    showError('Failed to fetch data: ' + error.responseText);
}

function showError(message) {
    // Implement error notification (you can use bootstrap toast or alert)
    alert(message);
}

function showSuccess(message) {
    // Implement success notification
    alert(message);
}
