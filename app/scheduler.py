import time
import random
from apscheduler.schedulers.background import BackgroundScheduler
from app.database.postgres import SessionLocal, MonitoredTarget
from app.database.neo4j_db import neo4j_manager
from app.analytics.network_core import run_networkx_analysis
from app.config import settings
import requests

scheduler = BackgroundScheduler()

def send_live_alert(message: str):
    """Telegram या किसी अन्य चैनल पर तुरंत अलर्ट भेजना"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": settings.TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Alert Dispatch Error: {e}")

def scrape_instagram_mock(username: str):
    """यहाँ आपका मुख्य Scraper/Playwright/Instaloader लॉजिक इम्प्लीमेंट होगा"""
    # सिमुलेशन के लिए डमी डेटा (इसे अपने असली स्क्रैपर से बदलें)
    time.sleep(2)  # Network delay Simulation
    return {
        "followers": [f"user_{random.randint(1, 20)}" for _ in range(5)] + ["new_premium_target"]
    }

def execute_monitoring_job():
    """यह फंक्शन हर 15 मिनट में सभी एक्टिव टारगेट्स को स्कैन करेगा"""
    db_pg = SessionLocal()
    try:
        active_targets = db_pg.query(MonitoredTarget).filter(MonitoredTarget.is_active == True).all()
        
        for target in active_targets:
            print(f"🔍 Live Monitoring Intel for: @{target.username}")
            
            # 1. इंस्टाग्राम से लाइव डेटा स्क्रैप करें
            live_data = scrape_instagram_mock(target.username)
            
            # 2. Neo4j में सिंक करें और 'नए कनेक्शन्स' का पता लगाएं
            new_followers = neo4j_manager.update_connections_and_get_new(target.username, live_data["followers"])
            
            # 3. अगर कोई नया कनेक्शन मिला है तो तुरंत अलर्ट भेजें
            if new_followers:
                alert_msg = f"🚨 [IG-INTEL ALERT]\nTarget: @{target.username}\n⚠️ New Followers Detected: {', '.join(new_followers)}"
                send_live_alert(alert_msg)
                
                # 4. NetworkX एनालिसिस ट्रिगर करें क्योंकि नेटवर्क बदल गया है
                graph_intel = run_networkx_analysis(target.username)
                analysis_msg = f"📊 [Graph Intel Update]\nTotal Associated Nodes: {graph_intel['total_nodes']}\nMost Central Node: {graph_intel['highest_influence_node']}"
                send_live_alert(analysis_msg)
            
            # 5. Postgres में टाइमस्टैम्प अपडेट करें
            target.last_checked = datetime.utcnow()
            db_pg.commit()
            
            # Anti-Ban delay (हर टारगेट के बीच थोड़ा गैप)
            time.sleep(random.randint(10, 30))
            
    except Exception as e:
        print(f"💥 Scheduler Error: {e}")
    finally:
        db_pg.close()

def start_scheduler():
    scheduler.add_job(
        execute_monitoring_job,
        'interval',
        minutes=settings.MONITOR_INTERVAL_MINUTES,
        id='ig_live_monitor_job',
        replace_existing=True
    )
    scheduler.start()
  
