import os
import json
import logging
import datetime
from pathlib import Path
import flask
from flask import Flask, render_template, jsonify, request, send_from_directory
import threading
import webbrowser
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebDashboard:
    def __init__(self, data_dir="data", port=5000):
        """
        Initialize the web dashboard
        
        Args:
            data_dir (str): Directory with analytics data
            port (int): Port to run the dashboard on
        """
        self.data_dir = data_dir
        self.analytics_dir = os.path.join(data_dir, "analytics")
        self.port = port
        self.app = Flask(__name__, 
                         template_folder=os.path.join(os.path.dirname(__file__), "templates"),
                         static_folder=os.path.join(os.path.dirname(__file__), "static"))
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.analytics_dir, exist_ok=True)
        
        # Create templates and static directories if they don't exist
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(templates_dir, exist_ok=True)
        os.makedirs(static_dir, exist_ok=True)
        
        # Create basic HTML templates
        self._create_templates()
        
        # Register routes
        self._register_routes()
        
        logger.info(f"Web dashboard initialized on port {port}")
    
    def _create_templates(self):
        """Create basic HTML templates if they don't exist"""
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        
        # Base template
        base_template = os.path.join(templates_dir, "base.html")
        if not os.path.exists(base_template):
            with open(base_template, 'w') as f:
                f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MultiversX AI Twitter Bot{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding-top: 60px; }
        .navbar-brand { font-weight: bold; }
        .card { margin-bottom: 20px; }
    </style>
    {% block head %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
        <div class="container">
            <a class="navbar-brand" href="/">MultiversX AI Twitter Bot</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/interactions">Interactions</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/reports">Reports</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>""")
        
        # Dashboard template
        dashboard_template = os.path.join(templates_dir, "dashboard.html")
        if not os.path.exists(dashboard_template):
            with open(dashboard_template, 'w') as f:
                f.write("""{% extends "base.html" %}

{% block title %}Dashboard - MultiversX AI Twitter Bot{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Dashboard</h1>
    </div>
</div>

<div class="row">
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Today's Interactions</h5>
                <h1 class="display-4 text-center">{{ stats.today_interactions }}</h1>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Total Interactions</h5>
                <h1 class="display-4 text-center">{{ stats.total_interactions }}</h1>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Unique Users</h5>
                <h1 class="display-4 text-center">{{ stats.unique_users }}</h1>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Interactions by Day</h5>
                <canvas id="interactionsChart"></canvas>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Classifications</h5>
                <canvas id="classificationsChart"></canvas>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Recent Interactions</h5>
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Username</th>
                                <th>Classification</th>
                                <th>Tweet</th>
                                <th>Response</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for interaction in recent_interactions %}
                            <tr>
                                <td>{{ interaction.timestamp }}</td>
                                <td>{{ interaction.username }}</td>
                                <td>{{ interaction.classification }}</td>
                                <td>{{ interaction.tweet_text|truncate(50) }}</td>
                                <td>{{ interaction.response|truncate(50) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Interactions by day chart
    const interactionsCtx = document.getElementById('interactionsChart').getContext('2d');
    new Chart(interactionsCtx, {
        type: 'line',
        data: {
            labels: {{ chart_data.dates|safe }},
            datasets: [{
                label: 'Interactions',
                data: {{ chart_data.interactions|safe }},
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Classifications chart
    const classificationsCtx = document.getElementById('classificationsChart').getContext('2d');
    new Chart(classificationsCtx, {
        type: 'pie',
        data: {
            labels: {{ chart_data.classification_labels|safe }},
            datasets: [{
                data: {{ chart_data.classification_values|safe }},
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1
            }]
        }
    });
});
</script>
{% endblock %}""")
        
        # Interactions template
        interactions_template = os.path.join(templates_dir, "interactions.html")
        if not os.path.exists(interactions_template):
            with open(interactions_template, 'w') as f:
                f.write("""{% extends "base.html" %}

{% block title %}Interactions - MultiversX AI Twitter Bot{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Interactions</h1>
        
        <div class="card">
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Username</th>
                                <th>Classification</th>
                                <th>Tweet</th>
                                <th>Response</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for interaction in interactions %}
                            <tr>
                                <td>{{ interaction.timestamp }}</td>
                                <td>{{ interaction.username }}</td>
                                <td>{{ interaction.classification }}</td>
                                <td>{{ interaction.tweet_text }}</td>
                                <td>{{ interaction.response }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}""")
        
        # Reports template
        reports_template = os.path.join(templates_dir, "reports.html")
        if not os.path.exists(reports_template):
            with open(reports_template, 'w') as f:
                f.write("""{% extends "base.html" %}

{% block title %}Reports - MultiversX AI Twitter Bot{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Reports</h1>
        
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Available Reports</h5>
                <div class="list-group">
                    {% for report in reports %}
                    <a href="/reports/{{ report.filename }}" class="list-group-item list-group-item-action">
                        {{ report.date }} - {{ report.interactions }} interactions
                    </a>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

{% if report_images %}
<div class="row mt-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Report Charts</h5>
                <div class="row">
                    {% for image in report_images %}
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <img src="/analytics/{{ image }}" class="img-fluid" alt="Chart">
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endif %}
{% endblock %}""")
    
    def _register_routes(self):
        """Register Flask routes"""
        @self.app.route('/')
        def dashboard():
            stats, chart_data, recent_interactions = self._get_dashboard_data()
            return render_template('dashboard.html', 
                                  stats=stats, 
                                  chart_data=chart_data,
                                  recent_interactions=recent_interactions)
        
        @self.app.route('/interactions')
        def interactions():
            interactions = self._load_interactions()
            return render_template('interactions.html', interactions=interactions)
        
        @self.app.route('/reports')
        def reports():
            reports = self._get_available_reports()
            return render_template('reports.html', reports=reports)
        
        @self.app.route('/reports/<filename>')
        def view_report(filename):
            report_data = self._load_report(filename)
            report_images = self._get_report_images(filename.replace('.json', ''))
            return render_template('reports.html', 
                                  reports=self._get_available_reports(),
                                  report_data=report_data,
                                  report_images=report_images)
        
        @self.app.route('/analytics/<path:filename>')
        def analytics_files(filename):
            return send_from_directory(self.analytics_dir, filename)
        
        @self.app.route('/api/stats')
        def api_stats():
            stats, chart_data, _ = self._get_dashboard_data()
            return jsonify({
                'stats': stats,
                'chart_data': chart_data
            })
    
    def _load_interactions(self) -> List[Dict]:
        """
        Load interaction data from file
        
        Returns:
            List[Dict]: List of interaction records
        """
        interactions_file = os.path.join(self.data_dir, "interactions.json")
        if os.path.exists(interactions_file):
            try:
                with open(interactions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading interactions: {e}")
                return []
        return []
    
    def _get_dashboard_data(self):
        """
        Get data for the dashboard
        
        Returns:
            Tuple: (stats, chart_data, recent_interactions)
        """
        interactions = self._load_interactions()
        
        # Basic stats
        today = datetime.datetime.now().date()
        today_interactions = [
            interaction for interaction in interactions
            if datetime.datetime.fromisoformat(interaction["timestamp"]).date() == today
        ]
        
        stats = {
            "today_interactions": len(today_interactions),
            "total_interactions": len(interactions),
            "unique_users": len(set(interaction["username"] for interaction in interactions))
        }
        
        # Chart data
        dates = []
        interactions_by_date = {}
        classifications = {}
        
        # Get data for the last 7 days
        for i in range(7):
            date = (datetime.datetime.now() - datetime.timedelta(days=i)).date()
            date_str = date.strftime("%Y-%m-%d")
            dates.append(date_str)
            interactions_by_date[date_str] = 0
        
        # Count interactions by date and classification
        for interaction in interactions:
            date = datetime.datetime.fromisoformat(interaction["timestamp"]).date()
            date_str = date.strftime("%Y-%m-%d")
            
            if date_str in interactions_by_date:
                interactions_by_date[date_str] += 1
            
            classification = interaction["classification"]
            classifications[classification] = classifications.get(classification, 0) + 1
        
        chart_data = {
            "dates": list(reversed(dates)),
            "interactions": [interactions_by_date[date] for date in reversed(dates)],
            "classification_labels": list(classifications.keys()),
            "classification_values": list(classifications.values())
        }
        
        # Recent interactions (last 10)
        recent_interactions = sorted(interactions, 
                                    key=lambda x: x["timestamp"], 
                                    reverse=True)[:10]
        
        return stats, chart_data, recent_interactions
    
    def _get_available_reports(self) -> List[Dict]:
        """
        Get list of available reports
        
        Returns:
            List[Dict]: List of report info
        """
        reports = []
        
        for filename in os.listdir(self.analytics_dir):
            if filename.startswith('report_') and filename.endswith('.json'):
                try:
                    with open(os.path.join(self.analytics_dir, filename), 'r') as f:
                        report_data = json.load(f)
                        
                    reports.append({
                        'filename': filename,
                        'date': report_data.get('date', filename.replace('report_', '').replace('.json', '')),
                        'interactions': report_data.get('total_interactions', 0)
                    })
                except Exception as e:
                    logger.error(f"Error loading report {filename}: {e}")
        
        return sorted(reports, key=lambda x: x['date'], reverse=True)
    
    def _load_report(self, filename: str) -> Dict:
        """
        Load a specific report
        
        Args:
            filename (str): Report filename
            
        Returns:
            Dict: Report data
        """
        report_path = os.path.join(self.analytics_dir, filename)
        if os.path.exists(report_path):
            try:
                with open(report_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading report {filename}: {e}")
        
        return {}
    
    def _get_report_images(self, report_date: str) -> List[str]:
        """
        Get images associated with a report
        
        Args:
            report_date (str): Report date string
            
        Returns:
            List[str]: List of image filenames
        """
        images = []
        
        for filename in os.listdir(self.analytics_dir):
            if filename.endswith('.png') and report_date in filename:
                images.append(filename)
        
        return images
    
    def start(self, open_browser=True):
        """
        Start the web dashboard
        
        Args:
            open_browser (bool): Whether to open a browser window
        """
        def run_app():
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
        
        # Start Flask in a separate thread
        thread = threading.Thread(target=run_app)
        thread.daemon = True
        thread.start()
        
        if open_browser:
            webbrowser.open(f'http://localhost:{self.port}')
        
        logger.info(f"Web dashboard running at http://localhost:{self.port}")
        
        return thread