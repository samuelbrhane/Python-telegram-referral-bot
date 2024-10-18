# Python-telegram-referral-bot
## Telegram Referral Bot
## Description
This repository contains a general-purpose **Telegram Referral Bot** designed to help organizations or communities grow their audience through a referral system. Users can generate unique referral links, track their referrals, and view referral statistics. This bot ensures users are subscribed to a specific Telegram channel before they can use the bot’s features.

### Key Features:
- **Referral Generation:** Users can generate and share unique referral links.
- **Subscription Check:** Ensures users are subscribed to a specific Telegram channel before proceeding with the referral system.
- **Referral Tracking:** Tracks successful referrals and updates invite counts for the referrers.
- **Leaderboard:** Displays a leaderboard of top referrers with invites.
- **Hosted on AWS:** The bot is designed to run continuously using AWS services like EC2 and RDS.

## Getting Started

### Prerequisites:
- Python 3.x
- MySQL (or another compatible database for referral tracking)
- A Telegram Bot API Token (obtained from [BotFather](https://t.me/BotFather))
- A Telegram channel where users need to subscribe

### Installation:

1. Clone the repository:
    ```bash
    git clone https://github.com/samuelbrhane/Python-telegram-referral-bot.git
    cd Python-telegram-referral-bot
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up environment variables:
   You need to set environment variables for the bot to access sensitive data like the API token and database credentials. You can add these in your shell, or configure them in AWS if you're using EC2.
   
    Example:
    ```bash
    export BOT_TOKEN='your-telegram-bot-token'
    export DB_HOST='your-database-host'
    export DB_USER='your-database-user'
    export DB_PASSWORD='your-database-password'
    export DB_NAME='your-database-name'
    export bot_username='your-bot-user'
    export CHANNEL_USERNAME='your-telegram-channel-name'
    export CHANNEL_URL='your-telegram-channel-url'
    ```

4. Start the bot:
    ```bash
    python bot.py
    ```

### AWS Setup (Optional):
The bot is designed to run continuously, so you may want to host it on AWS EC2 with an RDS MySQL instance for database operations.

- Set up an EC2 instance for running the bot.
- Set up an RDS MySQL instance for storing referral data.

### Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
