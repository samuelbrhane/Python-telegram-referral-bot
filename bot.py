import os
import mysql.connector
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

Token = os.getenv("BOT_TOKEN")
bot_username = "your-bot-username"
CHANNEL_USERNAME = "your-telegram-channel-username"
CHANNEL_URL = "your-telegram-channel-url"

# Database configuration
db_config = {
    'host': os.getenv("DB_HOST"), 
    'user': os.getenv("DB_USER"),  
    'password': os.getenv("DB_PASSWORD"),  
    'database': os.getenv("DB_NAME")  
}

db = None
cursor = None
company_name = "Put your company name here"

def create_database_and_tables():
    """Connect to the MySQL database and create necessary tables if they do not exist."""
    global db, cursor 
    try:
        # Connect to the MySQL database
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        # Create the referrals table if it does not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                invite_count INT DEFAULT 0
            )
        ''')

        # Create the referral tracking table if it does not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_tracking (
                referrer_id BIGINT,
                referred_id BIGINT,
                PRIMARY KEY (referrer_id, referred_id)
            )
        ''')

        # Create the referral_temp table for storing temporary referral information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_temp (
                user_id BIGINT PRIMARY KEY,
                referrer_id BIGINT
            )
        ''')

        # Commit the changes and close the connection
        db.commit()
        print("Database and tables created successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
       
       
async def check_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    """Check if the user is subscribed to the channel."""
    try:
        # Fetch the chat member's status
        member_status = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        
        if member_status.status in ["member", "administrator", "creator"]:
            return True
        else:
            return False
        
    except Exception as e:
        print(f"Error in checking subscription: {e}")
        return False
    
    
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    # Use first_name as the username if it doesn't exist
    if not username:
        username = first_name

    # Get the referral link arguments (if present)
    args = context.args

    # Prevent users from referring themselves
    if args and str(user_id) == args[0]:
        await context.bot.send_message(chat_id=user_id, text="You cannot refer yourself!")
        return

    # Store referral info if user comes via a referral link (even if not subscribed)
    if args and str(user_id) != args[0]:
        referrer_id = args[0]
        cursor.execute("REPLACE INTO referral_temp (user_id, referrer_id) VALUES (%s, %s)", (user_id, referrer_id))
        db.commit()

    # Check if the user is subscribed to the channel
    is_subscribed = await check_subscription(user_id, context)

    if not is_subscribed:
        # Ask the user to subscribe to the channel before proceeding
        await context.bot.send_message(
            chat_id=user_id,
            text=f"To use this bot, you must first subscribe to our channel: [{company_name}]({CHANNEL_URL})\n"
                 "After subscribing, click /start again to continue.",
            parse_mode="Markdown"
        )
        return

    # Check if the user is already in the referrals table
    cursor.execute("SELECT * FROM referrals WHERE user_id = %s", (user_id, ))
    result = cursor.fetchone()

    if not result:
        # Insert the user data into the referrals table
        cursor.execute("INSERT INTO referrals (user_id, username, first_name, invite_count) VALUES (%s, %s, %s, %s)", 
                       (user_id, username, first_name, 0))
        db.commit()

    # After subscribing, retrieve referral info from the temporary table
    cursor.execute("SELECT referrer_id FROM referral_temp WHERE user_id = %s", (user_id, ))
    referral_info = cursor.fetchone()

    if referral_info:
        referrer_id = referral_info[0]
        
        # Update the referral relationship and invite count
        new_invite_count = update_referral_count(referrer_id, user_id)
        if new_invite_count:
            await context.bot.send_message(chat_id=int(referrer_id), text=f"Thank you for referring a new user! Total invites: {new_invite_count}")

        # Remove the temporary referral info
        cursor.execute("DELETE FROM referral_temp WHERE user_id = %s", (user_id, ))
        db.commit()

    # Generate the referral link for the current user
    referral_link = f"{CHANNEL_URL}?start={user_id}"

    # Send the welcome message and referral link to the user
    await context.bot.send_message(
        chat_id=user_id,
        text=f"Welcome to {company_name}, {first_name}!\n"
             f"Here is your referral link:\n{referral_link}\n\n"
             "Share this link with others to invite them! To check the leaderboard, use the /board command."
    )


def update_referral_count(referrer_id, referred_id):

    # Ensure the referrer is in the database
    cursor.execute("SELECT * FROM referrals WHERE user_id = %s", (referrer_id,))
    referrer = cursor.fetchone()

    if not referrer:
        return False

    # Check if the referral is already recorded (cross-referral prevention)
    cursor.execute("""
        SELECT * FROM referral_tracking 
        WHERE (referrer_id = %s AND referred_id = %s) OR (referrer_id = %s AND referred_id = %s)
    """, (referrer_id, referred_id, referred_id, referrer_id))

    result = cursor.fetchone()

    if result:
        # If there's already a referral record, don't update the invite count
        return False
    
    else:
        # Update the referrer's invite count
        cursor.execute("SELECT invite_count FROM referrals WHERE user_id = %s", (referrer_id,))
        result = cursor.fetchone()

        if result:
            # Update the invite count if the referrer exists
            new_count = result[0] + 1
            cursor.execute("UPDATE referrals SET invite_count = %s WHERE user_id = %s", (new_count, referrer_id))
            
            # Track the referral by inserting into referral_tracking
            cursor.execute("INSERT INTO referral_tracking (referrer_id, referred_id) VALUES (%s, %s)", (referrer_id, referred_id))
            db.commit()
            return new_count

        return False


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cursor  

    # Query the database for top referrers with invite_count > 0
    cursor.execute("SELECT username, first_name, invite_count FROM referrals WHERE invite_count > 0 ORDER BY invite_count DESC LIMIT 10")
    leaderboard_data = cursor.fetchall()

    # If no referral data exists, notify the user
    if not leaderboard_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No referrals with invites yet!")
        return

    # Create leaderboard message with top referrers
    leaderboard_message = f"📊 Leaderboard - Top Referrers at {company_name}:\n\n"
    rank = 1
    for username, first_name, invite_count in leaderboard_data:
        display_name = username if username and username != 'Unknown' else first_name
        leaderboard_message += f"🏅 {rank}. {display_name}: {invite_count} invites\n"
        rank += 1

    # Send the leaderboard message to the user
    await context.bot.send_message(chat_id=update.effective_chat.id, text=leaderboard_message)
 
    
if __name__ == "__main__":
    print("Bot is running")
  
    create_database_and_tables()
    app = Application.builder().token(Token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("board", leaderboard_command))
    
    app.run_polling()
