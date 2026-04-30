from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
from textblob import TextBlob
import random
import time
import threading
import csv
import io
from datetime import datetime
from collections import deque
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xc0pe-s3cr3t-v2!2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Big data storage (scales to 10k+ tweets)
tweets = []
sentiment_history = deque(maxlen=50)
rolling_tweets = deque(maxlen=500)  # Larger for demo

# Expanded tweet dataset for realistic big data simulation
TWEET_SAMPLES = [
    "Loving the new AI features in XCOPE! Game changer for analytics #DataScience",
    "App crashes frequently, poor performance on mobile #Buggy",
    "Excellent real-time dashboard, perfect for sentiment tracking",
    "UI is outdated, needs modern redesign #UXFail",
    "Best tool for big data visualization I've used ⭐⭐⭐⭐⭐",
    "Slow data processing, not suitable for production",
    "Revolutionary sentiment analysis engine!",
    "Limited filtering options, add more advanced queries",
    "Outstanding customer support and updates",
    "Overpriced for the features offered",
    "Transforming our social media monitoring workflow",
    "Bugs in pagination, history page broken",
    # Add 1000+ more via loop in production, truncated here
] * 100  # Scales to big data demo

def generate_tweet():
    text = random.choice(TWEET_SAMPLES)
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    sentiment = 'positive' if polarity > 0.1 else 'negative' if polarity < -0.1 else 'neutral'
    tweet = {
        'id': len(tweets) + 1,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'text': text,
        'sentiment': sentiment,
        'score': round(polarity, 3)
    }
    return tweet

def tweet_stream():
    while True:
        tweet = generate_tweet()
        tweets.append(tweet)
        rolling_tweets.append(tweet)
        sentiment_history.append(tweet['score'])
        socketio.emit('new_tweet', tweet)
        socketio.emit('dashboard_update', get_dashboard_stats())
        time.sleep(1 + random.uniform(-0.3, 0.5))

def get_dashboard_stats():
    pos = sum(1 for t in rolling_tweets if t['sentiment'] == 'positive')
    neg = sum(1 for t in rolling_tweets if t['sentiment'] == 'negative')
    neut = len(rolling_tweets) - pos - neg
    avg_score = sum(sentiment_history) / len(sentiment_history) if sentiment_history else 0
    # Get sentiment score history for trend chart
    history = list(sentiment_history)
    return {
        'positive': pos, 'negative': neg, 'neutral': neut,
        'total': len(rolling_tweets), 'avg_score': round(avg_score, 3),
        'history': history
    }

@app.route('/dashboard')
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/')
def index():
    """Home page with Hero section, feature cards, CTAs"""
    return render_template('index.html')


@app.route('/api/stats')
def api_stats():
    return jsonify(get_dashboard_stats())

@app.route('/history')
def history():
    page = request.args.get('page', 1, type=int)
    sentiment_filter = request.args.get('sentiment', 'all')
    search_query = request.args.get('search', '')
    filtered_tweets = tweets.copy()
    if sentiment_filter != 'all':
        filtered_tweets = [t for t in filtered_tweets if t['sentiment'] == sentiment_filter]
    if search_query:
        filtered_tweets = [t for t in filtered_tweets if search_query.lower() in t['text'].lower()]
    per_page = 20
    start = (page - 1) * per_page
    paginated = filtered_tweets[start:start + per_page]
    return render_template('history.html',
                          tweets=paginated, page=page, total=len(filtered_tweets),
                          per_page=per_page, sentiment_filter=sentiment_filter, search_query=search_query)

@app.route('/export')
def export_csv():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id', 'timestamp', 'text', 'sentiment', 'score'])
    writer.writeheader()
    writer.writerows(tweets[-1000:])  # Last 1000 for big data export
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='xcopc_sentiment_data.csv')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@socketio.on('connect')
def handle_connect():
    emit('init', get_dashboard_stats())

if __name__ == '__main__':
    os.makedirs('static/data', exist_ok=True)
    threading.Thread(target=tweet_stream, daemon=True).start()
    print("🚀 XCOPE Professional Dashboard v2.0 starting...")
    print("📱 Dashboard: http://localhost:5000")
    print("📊 Export: http://localhost:5000/export")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
