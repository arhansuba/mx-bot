# MultiversX AI Twitter Bot - Enterprise Edition

A comprehensive Twitter bot system that monitors tweets about MultiversX, analyzes them using advanced AI, fetches blockchain data, and responds with intelligent, context-aware information. Includes a complete web dashboard, admin interface, analytics, and proactive monitoring.

## Features

### Core Functionality
- **Intelligent Tweet Monitoring:** Scrapes tweets mentioning "MultiversX" and analyzes them in real-time
- **Gemini AI Integration:** Uses Google's advanced Gemini AI for natural language processing
- **Advanced Blockchain Integration:** Retrieves comprehensive data from the MultiversX blockchain
- **Smart Response System:** Generates personalized, context-aware responses

### Enhanced AI Capabilities
- **Sentiment Analysis:** Analyzes tweet sentiment to craft emotionally appropriate responses
- **NLP Tweet Generation:** Creates varied, natural-sounding tweets across multiple categories
- **Intent Classification:** Accurately identifies the purpose behind each tweet
- **MultiversX Knowledge Base:** Built-in understanding of the MultiversX ecosystem

### Proactive Features
- **Blockchain Monitoring:** Automatically detects and tweets about significant blockchain events
- **Price Change Alerts:** Notifies followers about major EGLD price movements
- **Large Transaction Detection:** Highlights noteworthy transactions on the network
- **Scheduled Tweets:** Plans and posts tweets based on customizable schedules

### Analytics & Insights
- **ML-Powered Analytics:** Machine learning algorithms analyze interaction patterns
- **User Segmentation:** Identifies and categorizes different types of followers
- **Content Effectiveness Analysis:** Measures which responses generate the most engagement
- **Automated Reporting:** Generates daily performance reports with actionable insights

### Management & Administration
- **Web Dashboard:** Complete browser-based monitoring and control system
- **Admin Interface:** Manage settings, tweet schedules, and bot behavior
- **Configuration Management:** Easily customize all aspects of the bot
- **Real-time Logs:** Monitor bot activity and troubleshoot issues

### Deployment Options
- **Docker Support:** Simple containerized deployment
- **CI/CD Integration:** Automated deployment scripts
- **Systemd Service:** Run as a system service on Linux
- **Comprehensive Testing:** Unit tests ensure reliability

## Architecture

```
multiversx-ai-bot/
├── src/
│   ├── main.py                      # Entry point: Runs the bot's main loop
│   ├── bot_controller.py            # Central control system for all components
│   ├── twitter_scraper.py           # Scrapes tweets mentioning "MultiversX"
│   ├── ai_analyzer.py               # Classifies tweet intent using Gemini AI
│   ├── blockchain_fetcher.py        # Fetches blockchain data from API
│   ├── response_generator.py        # Generates AI-powered responses
│   ├── twitter_poster.py            # Posts replies to Twitter
│   ├── tweet_analytics.py           # Tracks and analyzes interactions
│   ├── sentiment_analyzer.py        # Analyzes tweet sentiment
│   ├── blockchain_monitor.py        # Monitors blockchain for notable events
│   ├── tweet_scheduler.py           # Manages scheduled tweets
│   ├── nlp_tweet_generator.py       # Advanced AI tweet generation
│   ├── ml_analytics.py              # ML-driven analytics and insights
│   ├── multiversx_sdk_integration.py # Advanced blockchain interactions
│   ├── admin_interface.py           # Admin interface for the dashboard
│   ├── web_dashboard.py             # Web-based monitoring interface
│   ├── templates/                   # HTML templates for the dashboard
│   ├── static/                      # Static assets for the dashboard
│   └── utils/
│       ├── __init__.py              # Utils package initialization
│       └── retry_utils.py           # Retry mechanisms for API calls
├── data/
│   ├── interactions.json            # Stored interaction data
│   ├── analytics/                   # Generated reports and charts
│   ├── monitor/                     # Blockchain monitoring data
│   ├── templates/                   # Tweet templates
│   └── scheduler/                   # Scheduled tweets data
├── tests/
│   └── test_blockchain_fetcher.py   # Unit tests for components
├── .env                             # Stores sensitive data (API keys)
├── requirements.txt                 # Lists Python dependencies
├── setup.py                         # Automates environment setup
├── deploy.py                        # CI/CD deployment automation
├── Dockerfile                       # Container definition
└── docker-compose.yml               # Multi-container setup
```

## Setup

### Prerequisites

- Python 3.8 or higher
- Google Chrome installed
- A Gemini AI API key
- A Twitter account for the bot

### Installation

#### Standard Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/multiversx-ai-bot.git
   cd multiversx-ai-bot
   ```

2. Run the automated deployment script:
   ```
   python deploy.py --deploy --interactive
   ```

3. Start the bot:
   ```
   python deploy.py --start
   ```

#### Docker Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/multiversx-ai-bot.git
   cd multiversx-ai-bot
   ```

2. Create an `.env` file with your API keys and settings.

3. Build and start the containers:
   ```
   docker-compose up -d
   ```

## Usage

### Web Dashboard

Access the web dashboard at `http://localhost:5000` to monitor and control the bot.

Key sections:
- **Dashboard:** Overview of bot activity and metrics
- **Interactions:** View all tweet interactions 
- **Reports:** Access analytics reports and insights
- **Admin:** Configure bot settings and behavior
- **Control Panel:** Start, stop, or restart the bot

### Command Line Control

The bot can be controlled via the `deploy.py` script:

```
# Start the bot
python deploy.py --start

# Stop the bot
python deploy.py --stop

# Deploy with specific options
python deploy.py --deploy --backup --test --with-sdk
```

### Customizing Bot Behavior

- **Configuration:** Edit settings via the admin interface
- **Tweet Templates:** Add custom templates for different tweet categories
- **Monitoring Thresholds:** Set custom alerts for blockchain events
- **Scheduled Tweets:** Create regular automated tweets

## Advanced Features

### Adding Custom Tweet Templates

1. Access the admin interface
2. Navigate to "Tweet Templates"
3. Add templates for different categories (educational, news, stats, etc.)

### Setting Up Blockchain Monitoring

1. Access the admin interface
2. Navigate to "Monitoring"
3. Set thresholds for price changes, transaction volumes, etc.
4. Enable/disable different monitoring features

### Using ML Analytics

The ML analytics system automatically processes interaction data to generate insights. Access these through:

1. The dashboard "Insights" tab
2. Daily generated reports in the admin section
3. The `/analytics/ml-report` endpoint

## Extending the Bot

The modular architecture makes it easy to extend the bot's capabilities:

1. **New AI Models:** Implement additional AI providers in `src/ai_analyzer.py`
2. **Additional Blockchain Data:** Extend `src/blockchain_fetcher.py` 
3. **Custom Analytics:** Add new metrics to `src/ml_analytics.py`
4. **New Dashboard Features:** Modify the templates in `src/templates/`

## Running Tests

Run the test suite to verify functionality:

```
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_blockchain_fetcher.py
```

## License

MIT

## Disclaimer

This project is for educational purposes. When deploying to production, ensure compliance with Twitter's terms of service, API usage policies, and applicable data privacy regulations.#   m x - b o t  
 