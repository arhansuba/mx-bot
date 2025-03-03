import os
import json
import logging
import datetime
import threading
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdminInterface:
    def __init__(self, data_dir="data", bot_controller=None):
        """
        Initialize the admin interface
        
        Args:
            data_dir (str): Directory with data
            bot_controller: Reference to the bot controller
        """
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "bot_config.json")
        self.admin_dir = os.path.join(data_dir, "admin")
        self.bot_controller = bot_controller
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.admin_dir, exist_ok=True)
        
        # Load or create default config
        self.config = self._load_config()
        
        # Blueprint for the admin interface
        self.bp = Blueprint('admin', __name__, url_prefix='/admin')
        
        # Register routes
        self._register_routes()
        
        logger.info("Admin interface initialized")
    
    def _load_config(self) -> Dict:
        """
        Load bot configuration
        
        Returns:
            Dict: Bot configuration
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration
        config = {
            "bot_enabled": True,
            "check_interval": 60,  # seconds
            "tweet_limit": 10,
            "search_terms": ["MultiversX"],
            "network": "devnet",
            "scheduled_tweets": [],
            "blacklisted_users": [],
            "auto_retweet_keywords": [],
            "sentiment_analysis_enabled": False,
            "proactive_monitoring": {
                "enabled": False,
                "price_change_threshold": 5.0,  # percentage
                "transaction_volume_threshold": 1000000,  # in USD
            }
        }
        
        # Save default config
        self._save_config(config)
        return config
    
    def _save_config(self, config: Dict) -> bool:
        """
        Save bot configuration
        
        Args:
            config (Dict): Bot configuration
            
        Returns:
            bool: Success status
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Bot configuration saved")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def _register_routes(self):
        """Register routes for the admin interface"""
        @self.bp.route('/')
        def index():
            return render_template('admin/index.html', config=self.config)
        
        @self.bp.route('/config', methods=['GET', 'POST'])
        def config():
            if request.method == 'POST':
                try:
                    # Update config based on form data
                    self.config['bot_enabled'] = request.form.get('bot_enabled') == 'on'
                    self.config['check_interval'] = int(request.form.get('check_interval', 60))
                    self.config['tweet_limit'] = int(request.form.get('tweet_limit', 10))
                    
                    # Parse search terms as comma-separated list
                    search_terms = request.form.get('search_terms', 'MultiversX')
                    self.config['search_terms'] = [term.strip() for term in search_terms.split(',') if term.strip()]
                    
                    self.config['network'] = request.form.get('network', 'devnet')
                    
                    # Parse blacklisted users
                    blacklisted = request.form.get('blacklisted_users', '')
                    self.config['blacklisted_users'] = [user.strip() for user in blacklisted.split(',') if user.strip()]
                    
                    # Parse auto-retweet keywords
                    auto_retweet = request.form.get('auto_retweet_keywords', '')
                    self.config['auto_retweet_keywords'] = [kw.strip() for kw in auto_retweet.split(',') if kw.strip()]
                    
                    # Feature toggles
                    self.config['sentiment_analysis_enabled'] = request.form.get('sentiment_analysis_enabled') == 'on'
                    self.config['proactive_monitoring']['enabled'] = request.form.get('proactive_monitoring_enabled') == 'on'
                    
                    # Thresholds
                    self.config['proactive_monitoring']['price_change_threshold'] = float(
                        request.form.get('price_change_threshold', 5.0)
                    )
                    self.config['proactive_monitoring']['transaction_volume_threshold'] = float(
                        request.form.get('transaction_volume_threshold', 1000000)
                    )
                    
                    # Save config
                    self._save_config(self.config)
                    
                    # Apply config to running bot if controller exists
                    if self.bot_controller:
                        self.bot_controller.apply_config(self.config)
                    
                    return jsonify({"success": True, "message": "Configuration updated"})
                except Exception as e:
                    logger.error(f"Error updating config: {e}")
                    return jsonify({"success": False, "message": f"Error: {str(e)}"})
            
            return render_template('admin/config.html', config=self.config)
        
        @self.bp.route('/scheduled-tweets', methods=['GET', 'POST'])
        def scheduled_tweets():
            if request.method == 'POST':
                try:
                    action = request.form.get('action')
                    
                    if action == 'add':
                        # Add new scheduled tweet
                        tweet = {
                            'id': str(datetime.datetime.now().timestamp()),
                            'content': request.form.get('content', ''),
                            'schedule': {
                                'type': request.form.get('schedule_type', 'one-time'),
                                'datetime': request.form.get('datetime', ''),
                                'days': request.form.getlist('days'),
                                'time': request.form.get('time', ''),
                                'interval_hours': int(request.form.get('interval_hours', 24))
                            },
                            'enabled': request.form.get('enabled') == 'on'
                        }
                        
                        self.config['scheduled_tweets'].append(tweet)
                        self._save_config(self.config)
                        
                        return jsonify({"success": True, "message": "Scheduled tweet added"})
                    
                    elif action == 'delete':
                        # Delete scheduled tweet
                        tweet_id = request.form.get('id')
                        self.config['scheduled_tweets'] = [
                            t for t in self.config['scheduled_tweets'] if t['id'] != tweet_id
                        ]
                        self._save_config(self.config)
                        
                        return jsonify({"success": True, "message": "Scheduled tweet deleted"})
                    
                    elif action == 'update':
                        # Update scheduled tweet
                        tweet_id = request.form.get('id')
                        for tweet in self.config['scheduled_tweets']:
                            if tweet['id'] == tweet_id:
                                tweet['content'] = request.form.get('content', '')
                                tweet['schedule']['type'] = request.form.get('schedule_type', 'one-time')
                                tweet['schedule']['datetime'] = request.form.get('datetime', '')
                                tweet['schedule']['days'] = request.form.getlist('days')
                                tweet['schedule']['time'] = request.form.get('time', '')
                                tweet['schedule']['interval_hours'] = int(request.form.get('interval_hours', 24))
                                tweet['enabled'] = request.form.get('enabled') == 'on'
                                break
                        
                        self._save_config(self.config)
                        return jsonify({"success": True, "message": "Scheduled tweet updated"})
                    
                except Exception as e:
                    logger.error(f"Error managing scheduled tweets: {e}")
                    return jsonify({"success": False, "message": f"Error: {str(e)}"})
            
            return render_template('admin/scheduled_tweets.html', config=self.config)
        
        @self.bp.route('/control', methods=['GET', 'POST'])
        def control():
            if request.method == 'POST':
                try:
                    action = request.form.get('action')
                    
                    if action == 'start' and self.bot_controller:
                        self.bot_controller.start()
                        return jsonify({"success": True, "message": "Bot started"})
                    
                    elif action == 'stop' and self.bot_controller:
                        self.bot_controller.stop()
                        return jsonify({"success": True, "message": "Bot stopped"})
                    
                    elif action == 'restart' and self.bot_controller:
                        self.bot_controller.restart()
                        return jsonify({"success": True, "message": "Bot restarted"})
                    
                    elif action == 'send_tweet' and self.bot_controller:
                        content = request.form.get('content', '')
                        self.bot_controller.send_manual_tweet(content)
                        return jsonify({"success": True, "message": "Tweet sent"})
                    
                    return jsonify({"success": False, "message": "Bot controller not available"})
                    
                except Exception as e:
                    logger.error(f"Error controlling bot: {e}")
                    return jsonify({"success": False, "message": f"Error: {str(e)}"})
            
            return render_template('admin/control.html', 
                                 running=self.bot_controller.is_running() if self.bot_controller else False)
        
        @self.bp.route('/logs')
        def logs():
            # Get the last N lines of the log file
            log_file = "bot.log"
            line_count = int(request.args.get('lines', 100))
            
            log_lines = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        all_lines = f.readlines()
                        log_lines = all_lines[-line_count:] if len(all_lines) > line_count else all_lines
                except Exception as e:
                    logger.error(f"Error reading log file: {e}")
            
            return render_template('admin/logs.html', log_lines=log_lines)
    
    def register_to_app(self, app):
        """
        Register the admin blueprint to a Flask app
        
        Args:
            app: Flask application
        """
        app.register_blueprint(self.bp)
        
        # Create templates directory and admin templates if they don't exist
        self._create_templates(app)
        
        logger.info("Admin interface registered to Flask app")
    
    def _create_templates(self, app):
        """Create admin templates if they don't exist"""
        template_dir = os.path.join(app.template_folder, 'admin')
        os.makedirs(template_dir, exist_ok=True)
        
        # Define template paths
        templates = {
            'index.html': """{% extends "base.html" %}

{% block title %}Admin - MultiversX AI Twitter Bot{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Admin Dashboard</h1>
    </div>
</div>

<div class="row">
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Bot Status</h5>
                <p class="card-text">
                    Status: 
                    {% if config.bot_enabled %}
                    <span class="badge bg-success">Enabled</span>
                    {% else %}
                    <span class="badge bg-danger">Disabled</span>
                    {% endif %}
                </p>
                <a href="{{ url_for('admin.control') }}" class="btn btn-primary">Control Panel</a>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Configuration</h5>
                <p class="card-text">Manage bot settings and parameters</p>
                <a href="{{ url_for('admin.config') }}" class="btn btn-primary">Configure</a>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Scheduled Tweets</h5>
                <p class="card-text">Manage automated tweet schedules</p>
                <a href="{{ url_for('admin.scheduled_tweets') }}" class="btn btn-primary">Schedule</a>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Logs</h5>
                <p class="card-text">View bot activity logs</p>
                <a href="{{ url_for('admin.logs') }}" class="btn btn-primary">View Logs</a>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Quick Settings</h5>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="toggleBot" {% if config.bot_enabled %}checked{% endif %}>
                    <label class="form-check-label" for="toggleBot">Enable Bot</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="toggleSentiment" {% if config.sentiment_analysis_enabled %}checked{% endif %}>
                    <label class="form-check-label" for="toggleSentiment">Enable Sentiment Analysis</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="toggleMonitoring" {% if config.proactive_monitoring.enabled %}checked{% endif %}>
                    <label class="form-check-label" for="toggleMonitoring">Enable Proactive Monitoring</label>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('toggleBot').addEventListener('change', function() {
    fetch('/admin/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'bot_enabled': this.checked ? 'on' : 'off',
            'check_interval': '{{ config.check_interval }}',
            'tweet_limit': '{{ config.tweet_limit }}',
            'search_terms': '{{ config.search_terms|join(",") }}',
            'network': '{{ config.network }}'
        })
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Bot ' + (this.checked ? 'enabled' : 'disabled'));
        } else {
            alert('Error: ' + data.message);
            this.checked = !this.checked;
        }
    });
});

document.getElementById('toggleSentiment').addEventListener('change', function() {
    fetch('/admin/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'sentiment_analysis_enabled': this.checked ? 'on' : 'off'
        })
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Sentiment Analysis ' + (this.checked ? 'enabled' : 'disabled'));
        } else {
            alert('Error: ' + data.message);
            this.checked = !this.checked;
        }
    });
});

document.getElementById('toggleMonitoring').addEventListener('change', function() {
    fetch('/admin/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'proactive_monitoring_enabled': this.checked ? 'on' : 'off'
        })
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Proactive Monitoring ' + (this.checked ? 'enabled' : 'disabled'));
        } else {
            alert('Error: ' + data.message);
            this.checked = !this.checked;
        }
    });
});
</script>
{% endblock %}""",
            
            'config.html': """{% extends "base.html" %}

{% block title %}Configuration - MultiversX AI Twitter Bot{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Bot Configuration</h1>
        
        <div class="card">
            <div class="card-body">
                <form id="configForm">
                    <div class="mb-3 form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="bot_enabled" name="bot_enabled" {% if config.bot_enabled %}checked{% endif %}>
                        <label class="form-check-label" for="bot_enabled">Enable Bot</label>
                    </div>
                    
                    <div class="mb-3">
                        <label for="network" class="form-label">Blockchain Network</label>
                        <select class="form-select" id="network" name="network">
                            <option value="devnet" {% if config.network == 'devnet' %}selected{% endif %}>Devnet</option>
                            <option value="testnet" {% if config.network == 'testnet' %}selected{% endif %}>Testnet</option>
                            <option value="mainnet" {% if config.network == 'mainnet' %}selected{% endif %}>Mainnet</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label for="check_interval" class="form-label">Check Interval (seconds)</label>
                        <input type="number" class="form-control" id="check_interval" name="check_interval" value="{{ config.check_interval }}">
                    </div>
                    
                    <div class="mb-3">
                        <label for="tweet_limit" class="form-label">Tweet Processing Limit</label>
                        <input type="number" class="form-control" id="tweet_limit" name="tweet_limit" value="{{ config.tweet_limit }}">
                    </div>
                    
                    <div class="mb-3">
                        <label for="search_terms" class="form-label">Search Terms (comma-separated)</label>
                        <input type="text" class="form-control" id="search_terms" name="search_terms" value="{{ config.search_terms|join(',') }}">
                    </div>
                    
                    <div class="mb-3">
                        <label for="blacklisted_users" class="form-label">Blacklisted Users (comma-separated)</label>
                        <input type="text" class="form-control" id="blacklisted_users" name="blacklisted_users" value="{{ config.blacklisted_users|join(',') }}">
                    </div>
                    
                    <div class="mb-3">
                        <label for="auto_retweet_keywords" class="form-label">Auto-Retweet Keywords (comma-separated)</label>
                        <input type="text" class="form-control" id="auto_retweet_keywords" name="auto_retweet_keywords" value="{{ config.auto_retweet_keywords|join(',') }}">
                    </div>
                    
                    <h4 class="mt-4">Feature Configuration</h4>
                    
                    <div class="mb-3 form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="sentiment_analysis_enabled" name="sentiment_analysis_enabled" {% if config.sentiment_analysis_enabled %}checked{% endif %}>
                        <label class="form-check-label" for="sentiment_analysis_enabled">Enable Sentiment Analysis</label>
                    </div>
                    
                    <h5 class="mt-3">Proactive Monitoring</h5>
                    
                    <div class="mb-3 form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="proactive_monitoring_enabled" name="proactive_monitoring_enabled" {% if config.proactive_monitoring.enabled %}checked{% endif %}>
                        <label class="form-check-label" for="proactive_monitoring_enabled">Enable Proactive Monitoring</label>
                    </div>
                    
                    <div class="mb-3">
                        <label for="price_change_threshold" class="form-label">Price Change Alert Threshold (%)</label>
                        <input type="number" step="0.1" class="form-control" id="price_change_threshold" name="price_change_threshold" value="{{ config.proactive_monitoring.price_change_threshold }}">
                    </div>
                    
                    <div class="mb-3">
                        <label for="transaction_volume_threshold" class="form-label">Transaction Volume Alert Threshold ($)</label>
                        <input type="number" class="form-control" id="transaction_volume_threshold" name="transaction_volume_threshold" value="{{ config.proactive_monitoring.transaction_volume_threshold }}">
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Save Configuration</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('configForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    
    fetch('/admin/config', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Configuration saved successfully');
        } else {
            alert('Error: ' + data.message);
        }
    });
});
</script>
{% endblock %}""",
            
            'scheduled_tweets.html': """{% extends "base.html" %}

{% block title %}Scheduled Tweets - MultiversX AI Twitter Bot{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Scheduled Tweets</h1>
        
        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">Add New Scheduled Tweet</h5>
                <form id="newTweetForm">
                    <input type="hidden" name="action" value="add">
                    
                    <div class="mb-3">
                        <label for="content" class="form-label">Tweet Content</label>
                        <textarea class="form-control" id="content" name="content" rows="3" required></textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label for="schedule_type" class="form-label">Schedule Type</label>
                        <select class="form-select" id="schedule_type" name="schedule_type">
                            <option value="one-time">One-time</option>
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="interval">Interval</option>
                        </select>
                    </div>
                    
                    <div id="one-time-options">
                        <div class="mb-3">
                            <label for="datetime" class="form-label">Date & Time</label>
                            <input type="datetime-local" class="form-control" id="datetime" name="datetime">
                        </div>
                    </div>
                    
                    <div id="daily-options" style="display: none;">
                        <div class="mb-3">
                            <label for="time" class="form-label">Time</label>
                            <input type="time" class="form-control" id="time" name="time">
                        </div>
                    </div>
                    
                    <div id="weekly-options" style="display: none;">
                        <div class="mb-3">
                            <label class="form-label">Days of Week</label>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="days" value="0" id="day0">
                                <label class="form-check-label" for="day0">Sunday</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="days" value="1" id="day1">
                                <label class="form-check-label" for="day1">Monday</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="days" value="2" id="day2">
                                <label class="form-check-label" for="day2">Tuesday</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="days" value="3" id="day3">
                                <label class="form-check-label" for="day3">Wednesday</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="days" value="4" id="day4">
                                <label class="form-check-label" for="day4">Thursday</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="days" value="5" id="day5">
                                <label class="form-check-label" for="day5">Friday</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="days" value="6" id="day6">
                                <label class="form-check-label" for="day6">Saturday</label>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label for="weekly_time" class="form-label">Time</label>
                            <input type="time" class="form-control" id="weekly_time" name="time">
                        </div>
                    </div>
                    
                    <div id="interval-options" style="display: none;">
                        <div class="mb-3">
                            <label for="interval_hours" class="form-label">Interval (hours)</label>
                            <input type="number" class="form-control" id="interval_hours" name="interval_hours" value="24">
                        </div>
                    </div>
                    
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="enabled" name="enabled" checked>
                        <label class="form-check-label" for="enabled">Enable This Tweet</label>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Add Scheduled Tweet</button>
                </form>
            </div>
        </div>
        
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Existing Scheduled Tweets</h5>
                
                {% if config.scheduled_tweets %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Content</th>
                                <th>Schedule Type</th>
                                <th>Schedule Details</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for tweet in config.scheduled_tweets %}
                            <tr>
                                <td>{{ tweet.content }}</td>
                                <td>{{ tweet.schedule.type }}</td>
                                <td>
                                    {% if tweet.schedule.type == 'one-time' %}
                                        {{ tweet.schedule.datetime }}
                                    {% elif tweet.schedule.type == 'daily' %}
                                        Every day at {{ tweet.schedule.time }}
                                    {% elif tweet.schedule.type == 'weekly' %}
                                        Every 
                                        {% for day in tweet.schedule.days %}
                                            {% if day == '0' %}Sunday{% elif day == '1' %}Monday{% elif day == '2' %}Tuesday{% elif day == '3' %}Wednesday{% elif day == '4' %}Thursday{% elif day == '5' %}Friday{% elif day == '6' %}Saturday{% endif %}{% if not loop.last %}, {% endif %}
                                        {% endfor %}
                                        at {{ tweet.schedule.time }}
                                    {% elif tweet.schedule.type == 'interval' %}
                                        Every {{ tweet.schedule.interval_hours }} hours
                                    {% endif %}
                                </td>
                                <td>
                                    {% if tweet.enabled %}
                                    <span class="badge bg-success">Enabled</span>
                                    {% else %}
                                    <span class="badge bg-danger">Disabled</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-danger" onclick="deleteTweet('{{ tweet.id }}')">Delete</button>
                                    <button class="btn btn-sm btn-primary" onclick="editTweet('{{ tweet.id }}')">Edit</button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <p>No scheduled tweets yet.</p>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Edit Tweet Modal -->
<div class="modal fade" id="editTweetModal" tabindex="-1" aria-labelledby="editTweetModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="editTweetModalLabel">Edit Scheduled Tweet</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="editTweetForm">
                    <input type="hidden" name="action" value="update">
                    <input type="hidden" id="edit_id" name="id">
                    
                    <div class="mb-3">
                        <label for="edit_content" class="form-label">Tweet Content</label>
                        <textarea class="form-control" id="edit_content" name="content" rows="3" required></textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label for="edit_schedule_type" class="form-label">Schedule Type</label>
                        <select class="form-select" id="edit_schedule_type" name="schedule_type">
                            <option value="one-time">One-time</option>
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="interval">Interval</option>
                        </select>
                    </div>
                    
                    <div id="edit_one-time-options">
                        <div class="mb-3">
                            <label for="edit_datetime" class="form-label">Date & Time</label>
                            <input type="datetime-local" class="form-control" id="edit_datetime" name="datetime">
                        </div>
                    </div>
                    
                    <div id="edit_daily-options" style="display: none;">
                        <div class="mb-3">
                            <label for="edit_time" class="form-label">Time</label>
                            <input type="time" class="form-control" id="edit_time" name="time">
                        </div>
                    </div>
                    
                    <div id="edit_weekly-options" style="display: none;">
                        <div class="mb-3">
                            <label class="form-label">Days of Week</label>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="days" value="0" id="edit_day0">
                                <label class="form-check-label" for="edit_day0">Sunday</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="days" value="1" id="edit_day1">
                                <label class="form-check-label" for="edit_day1">Monday</label>
                            </div>
                            <!-- Repeat for days 2-6 -->
                        </div>
                        <div class="mb-3">
                            <label for="edit_weekly_time" class="form-label">Time</label>
                            <input type="time" class="form-control" id="edit_weekly_time" name="time">
                        </div>
                    </div>
                    
                    <div id="edit_interval-options" style="display: none;">
                        <div class="mb-3">
                            <label for="edit_interval_hours" class="form-label">Interval (hours)</label>
                            <input type="number" class="form-control" id="edit_interval_hours" name="interval_hours" value="24">
                        </div>
                    </div>
                    
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="edit_enabled" name="enabled">
                        <label class="form-check-label" for="edit_enabled">Enable This Tweet</label>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="updateTweet()">Save Changes</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
// Show/hide schedule options based on selected type
document.getElementById('schedule_type').addEventListener('change', function() {
    const type = this.value;
    document.getElementById('one-time-options').style.display = type === 'one-time' ? 'block' : 'none';
    document.getElementById('daily-options').style.display = type === 'daily' ? 'block' : 'none';
    document.getElementById('weekly-options').style.display = type === 'weekly' ? 'block' : 'none';
    document.getElementById('interval-options').style.display = type === 'interval' ? 'block' : 'none';
});

document.getElementById('edit_schedule_type').addEventListener('change', function() {
    const type = this.value;
    document.getElementById('edit_one-time-options').style.display = type === 'one-time' ? 'block' : 'none';
    document.getElementById('edit_daily-options').style.display = type === 'daily' ? 'block' : 'none';
    document.getElementById('edit_weekly-options').style.display = type === 'weekly' ? 'block' : 'none';
    document.getElementById('edit_interval-options').style.display = type === 'interval' ? 'block' : 'none';
});

// Add new tweet
document.getElementById('newTweetForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    
    fetch('/admin/scheduled-tweets', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Scheduled tweet added');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    });
});

// Delete tweet
function deleteTweet(id) {
    if (confirm('Are you sure you want to delete this scheduled tweet?')) {
        const formData = new FormData();
        formData.append('action', 'delete');
        formData.append('id', id);
        
        fetch('/admin/scheduled-tweets', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Scheduled tweet deleted');
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        });
    }
}

// Edit tweet - open modal and populate fields
function editTweet(id) {
    const tweets = {{ config.scheduled_tweets|tojson }};
    const tweet = tweets.find(t => t.id === id);
    
    if (tweet) {
        document.getElementById('edit_id').value = tweet.id;
        document.getElementById('edit_content').value = tweet.content;
        document.getElementById('edit_schedule_type').value = tweet.schedule.type;
        document.getElementById('edit_datetime').value = tweet.schedule.datetime;
        document.getElementById('edit_time').value = tweet.schedule.time;
        document.getElementById('edit_interval_hours').value = tweet.schedule.interval_hours;
        document.getElementById('edit_enabled').checked = tweet.enabled;
        
        // Set weekly days
        if (tweet.schedule.days) {
            const days = tweet.schedule.days;
            for (let i = 0; i < 7; i++) {
                document.getElementById(`edit_day${i}`).checked = days.includes(i.toString());
            }
        }
        
        // Show appropriate options
        const type = tweet.schedule.type;
        document.getElementById('edit_one-time-options').style.display = type === 'one-time' ? 'block' : 'none';
        document.getElementById('edit_daily-options').style.display = type === 'daily' ? 'block' : 'none';
        document.getElementById('edit_weekly-options').style.display = type === 'weekly' ? 'block' : 'none';
        document.getElementById('edit_interval-options').style.display = type === 'interval' ? 'block' : 'none';
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editTweetModal'));
        modal.show();
    }
}

// Update tweet
function updateTweet() {
    const formData = new FormData(document.getElementById('editTweetForm'));
    
    fetch('/admin/scheduled-tweets', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Scheduled tweet updated');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    });
}
</script>
{% endblock %}""",
            
            'control.html': """{% extends "base.html" %}

{% block title %}Control Panel - MultiversX AI Twitter Bot{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Bot Control Panel</h1>
        
        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">Bot Status</h5>
                <p class="card-text">
                    Current Status: 
                    {% if running %}
                    <span class="badge bg-success">Running</span>
                    {% else %}
                    <span class="badge bg-danger">Stopped</span>
                    {% endif %}
                </p>
                
                <div class="btn-group" role="group">
                    <button id="startBtn" class="btn btn-success" {% if running %}disabled{% endif %}>Start Bot</button>
                    <button id="stopBtn" class="btn btn-danger" {% if not running %}disabled{% endif %}>Stop Bot</button>
                    <button id="restartBtn" class="btn btn-warning">Restart Bot</button>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Manual Tweet</h5>
                <p class="card-text">Send a one-time tweet without waiting for the scheduled check.</p>
                
                <form id="manualTweetForm">
                    <input type="hidden" name="action" value="send_tweet">
                    
                    <div class="mb-3">
                        <label for="content" class="form-label">Tweet Content</label>
                        <textarea class="form-control" id="content" name="content" rows="3" required></textarea>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Send Tweet</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('startBtn').addEventListener('click', function() {
    if (confirm('Are you sure you want to start the bot?')) {
        const formData = new FormData();
        formData.append('action', 'start');
        
        fetch('/admin/control', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Bot started');
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        });
    }
});

document.getElementById('stopBtn').addEventListener('click', function() {
    if (confirm('Are you sure you want to stop the bot?')) {
        const formData = new FormData();
        formData.append('action', 'stop');
        
        fetch('/admin/control', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Bot stopped');
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        });
    }
});

document.getElementById('restartBtn').addEventListener('click', function() {
    if (confirm('Are you sure you want to restart the bot?')) {
        const formData = new FormData();
        formData.append('action', 'restart');
        
        fetch('/admin/control', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Bot restarted');
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        });
    }
});

document.getElementById('manualTweetForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    if (confirm('Are you sure you want to send this tweet?')) {
        const formData = new FormData(this);
        
        fetch('/admin/control', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Tweet sent');
                this.reset();
            } else {
                alert('Error: ' + data.message);
            }
        });
    }
});
</script>
{% endblock %}""",
            
            'logs.html': """{% extends "base.html" %}

{% block title %}Logs - MultiversX AI Twitter Bot{% endblock %}

{% block head %}
<style>
    pre {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        white-space: pre-wrap;
        word-wrap: break-word;
        max-height: 600px;
        overflow-y: auto;
    }
    .log-error { color: #dc3545; }
    .log-warning { color: #ffc107; }
    .log-info { color: #0d6efd; }
</style>
{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Bot Logs</h1>
        
        <div class="card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="card-title">Log Output</h5>
                    <div>
                        <div class="btn-group" role="group">
                            <a href="/admin/logs?lines=100" class="btn btn-sm btn-outline-primary">Last 100 lines</a>
                            <a href="/admin/logs?lines=500" class="btn btn-sm btn-outline-primary">Last 500 lines</a>
                            <a href="/admin/logs?lines=1000" class="btn btn-sm btn-outline-primary">Last 1000 lines</a>
                        </div>
                        <button id="refreshBtn" class="btn btn-sm btn-primary ms-2">Refresh</button>
                    </div>
                </div>
                
                <pre id="logOutput">{% for line in log_lines %}{% if 'ERROR' in line %}<span class="log-error">{{ line }}</span>{% elif 'WARNING' in line %}<span class="log-warning">{{ line }}</span>{% elif 'INFO' in line %}<span class="log-info">{{ line }}</span>{% else %}{{ line }}{% endif %}{% endfor %}</pre>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('refreshBtn').addEventListener('click', function() {
    location.reload();
});

// Auto-scroll to bottom of logs
document.addEventListener('DOMContentLoaded', function() {
    const logOutput = document.getElementById('logOutput');
    logOutput.scrollTop = logOutput.scrollHeight;
});
</script>
{% endblock %}"""
        }
        
        # Create template files if they don't exist
        for filename, content in templates.items():
            filepath = os.path.join(template_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    f.write(content)