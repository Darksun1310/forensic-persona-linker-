<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Advanced Forensic Persona Linker</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <style>
        :root {
            --primary-color: #34495e; --secondary-color: #2c3e50; --background-color: #ecf0f1;
            --container-bg-color: #ffffff; --text-color: #2c3e50; --border-color: #bdc3c7;
            --success-color: #27ae60; --error-color: #c0392b;
        }
        body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: var(--background-color); margin: 0; padding: 2rem; color: var(--text-color); }
        .container { max-width: 800px; margin: auto; background: var(--container-bg-color); padding: 2.5rem; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        header h1 { font-size: 1.75rem; font-weight: 600; text-align: center; margin: 0 0 2rem 0; }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2.5rem; }
        .form-group label { display: block; font-weight: 500; margin-bottom: 0.5rem; }
        input[type="text"] { width: 100%; padding: 0.75rem; border-radius: 6px; border: 1px solid var(--border-color); font-size: 1rem; box-sizing: border-box; }
        .submit-button { display: flex; justify-content: center; align-items: center; width: 100%; padding: 1rem; margin-top: 2rem; background-color: var(--primary-color); color: white; border: none; border-radius: 6px; font-size: 1.1rem; font-weight: 500; cursor: pointer; transition: background-color 0.2s; }
        .submit-button:hover { background-color: var(--secondary-color); }
        .submit-button:disabled { background-color: #95a5a6; cursor: not-allowed; }
        .loader { width: 18px; height: 18px; border: 2px solid #fff; border-bottom-color: transparent; border-radius: 50%; display: none; box-sizing: border-box; animation: rotation 1s linear infinite; margin-left: 10px; }
        @keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .result-panel { margin-top: 2.5rem; border: 1px solid #bdc3c7; border-radius: 6px; display: none; }
        .result-header { padding: 1rem 1.5rem; background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7; }
        .result-header .verdict { font-size: 1.5rem; font-weight: 600; margin: 0; }
        .result-header .verdict.match { color: #27ae60; }
        .result-header .verdict.no-match { color: #c0392b; }
        .result-body { padding: 1.5rem; }
        .progress-bar-container { margin-bottom: 1.5rem; }
        .progress-bar-label { display: flex; justify-content: space-between; font-weight: 500; margin-bottom: 0.5rem; }
        .progress-bar { width: 100%; height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; }
        .progress-bar-fill { width: 0%; height: 100%; background-color: #27ae60; border-radius: 10px; transition: width 0.5s ease-in-out; }
        .report-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        .report-table th, .report-table td { text-align: left; padding: 0.75rem; border-bottom: 1px solid #ecf0f1; }
        .report-table th { font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <header><h1>Advanced Forensic Persona Linker</h1></header>
        <form id="analysis-form">
            <div class="form-grid">
                <div class="form-group">
                    <label for="vendor1">Vendor Name 1</label>
                    <input type="text" id="vendor1" name="vendor1" required placeholder="e.g., SnowQueen" autocomplete="off">
                </div>
                <div class="form-group">
                    <label for="vendor2">Vendor Name 2</label>
                    <input type="text" id="vendor2" name="vendor2" required placeholder="e.g., gonz324" autocomplete="off">
                </div>
            </div>
            <button type="submit" id="submit-btn" class="submit-button"><span class="button-text">Analyze</span><div class="loader"></div></button>
        </form>
        <div id="result-panel" class="result-panel">
            <div class="result-header"><p id="result-verdict" class="verdict"></p></div>
            <div class="result-body">
                <div class="progress-bar-container">
                    <div class="progress-bar-label"><span>Confidence Score</span><span id="score-text">0%</span></div>
                    <div class="progress-bar"><div id="score-bar" class="progress-bar-fill"></div></div>
                </div>
                <h3>Analysis Report</h3>
                <table class="report-table">
                    <thead><tr><th>Forensic Marker</th><th>Observation</th></tr></thead>
                    <tbody id="report-body"></tbody>
                </table>
            </div>
        </div>
    </div>

<script>
$(document).ready(function() {
    $('#analysis-form').on('submit', function(event) {
        event.preventDefault();

        if ($('#vendor1').val().trim() === '' || $('#vendor2').val().trim() === '') {
            alert('Please enter both vendor names.');
            return;
        }

        var formData = new FormData(this);
        var $submitBtn = $('#submit-btn');

        $submitBtn.prop('disabled', true).find('.button-text').text('Analyzing...');
        $submitBtn.find('.loader').show();
        $('#result-panel').fadeOut();

        $.ajax({
            type: 'POST', url: 'analyze.php', data: formData, processData: false, contentType: false, dataType: 'json',
            success: function(response) {
                var verdictClass = (response.verdict === 'Potential Match' || response.verdict === 'Match') ? 'match' : 'no-match';
                $('#result-verdict').text(response.verdict).removeClass('match no-match').addClass(verdictClass);
                $('#score-text').text(response.score + '%');
                $('#score-bar').css('width', response.score + '%');
                var $reportBody = $('#report-body').empty();
                if (response.report && Array.isArray(response.report)) {
                    response.report.forEach(function(item) {
                        var row = $('<tr></tr>');
                        row.append($('<td></td>').text(item.feature));
                       row.append($('<td></td>').text(item.reasoning));
                        $reportBody.append(row);
                    });
                }
                $('#result-panel').fadeIn();
            },
            // --- UPGRADED ERROR HANDLING ---
            error: function(jqXHR, textStatus, errorThrown) {
                console.error("AJAX Error: " + textStatus, errorThrown);
                console.error("Server Response:", jqXHR.responseText); // Log the full server response

                // Update the verdict text and style for the error
                $('#result-verdict').text('Server Error').removeClass('match').addClass('no-match');

                // Reset score and provide error details in the report
                $('#score-text').text('0%');
                $('#score-bar').css('width', '0%');
                $('#report-body').html("<tr><td>System Error</td><td>Failed to get a response from the server. Check the browser console (F12) for details.</td></tr>");

                // Show the results panel
                $('#result-panel').fadeIn();
            },
            complete: function() {
                $submitBtn.prop('disabled', false).find('.button-text').text('Analyze');
                $submitBtn.find('.loader').hide();
            }
        });
    });
});
</script>

</body>
</html>