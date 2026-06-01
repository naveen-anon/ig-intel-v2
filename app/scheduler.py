import time
import random
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# प्रोजेक्ट के दूसरे मॉड्यूल से इम्पोर्ट्स
from app.config import settings
from app.scraper import instagram_scraper  # नया असली स्क्रैपर इंजन
from app.database.postgres import SessionLocal, MonitoredTarget
from app.database.neo4j_db import neo4j_manager
from app.analytics.network_core import run_networkx_analysis
import requests

# बैकग्राउंड शेड्यूलर ऑब्जेक्ट
scheduler = BackgroundScheduler()

def send_live_alert(message: str):
    """Telegram या किसी अन्य चैनल पर तुरंत लाइव अलर्ट भेजना"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": settings.TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Alert Dispatch Error: {e}")

def execute_monitoring_job():
    """
    यह फंक्शन शेड्यूलर द्वारा हर X मिनट में रन होगा।
    यह Postgres से सभी एक्टिव टारगेट्स को उठाएगा और उनकी लाइव मॉनिटरिंग करेगा।
    """
    db_pg = SessionLocal()
    try:
        # Postgres से केवल उन टारगेट्स को निकालें जिनकी मॉनिटरिंग Active (True) है
        active_targets = db_pg.query(MonitoredTarget).filter(MonitoredTarget.is_active == True).all()
        
        for target in active_targets:
            print(f"🔍 [LIVE MONITOR] Processing Target: @{target.username}")
            
            # 1. असली स्क्रैपर का उपयोग करके इंस्टाग्राम से लाइव फॉलोअर्स की लिस्ट लाएं
            live_followers = instagram_scraper.fetch_followers_live(target.username)
            
            if not live_followers:
                print(f"⚠️ No data fetched or account blocked for @{target.username}. Skipping this loop.")
                continue

            # 2. Neo4j ग्राफ डेटाबेस में सिंक करें और 'नए कनेक्शन्स/फॉलोअर्स' को फिल्टर करें
            new_followers = neo4j_manager.update_connections_and_get_new(target.username, live_followers)
            
            # 3. अगर कोई भी नया फॉलोअर मिलता है, तो तुरंत अलर्ट ट्रिगर करें
            if new_followers:
                alert_msg = (
                    f"🚨 [IG-INTEL LIVE ALERT]\n"
                    f"🎯 Target: @{target.username}\n"
                    f"⚠️ New Followers Detected: {', '.join(new_followers)}"
                )
                send_live_alert(alert_msg)
                
                # 4. चूंकि सोशल ग्राफ बदल गया है, NetworkX से इन-मेमोरी एनालिसिस रन करें
                print(f"📊 Running NetworkX graph analytics for @{target.username}...")
                graph_intel = run_networkx_analysis(target.username)
                
                analysis_msg = (
                    f"📈 [Graph Analytics Update]\n"
                    f"Total Network Nodes: {graph_intel.get('total_nodes', 0)}\n"
                    f"Total Relationships: {graph_intel.get('total_edges', 0)}\n"
                    f"Most Central/Influential Node: @{graph_intel.get('highest_influence_node', 'N/A')}\n"
                    f"Graph Density: {graph_intel.get('graph_density', 0):.4f}"
                )
                send_live_alert(analysis_msg)
            else:
                print(f"✅ No new changes detected for @{target.username} since last check.")
            
            # 5. Postgres में इस टार्गेट का 'last_checked' टाइमस्टैम्प अपडेट करें
            target.last_checked = datetime.utcnow()
            db_pg.commit()
            
            # इंस्टाग्राम बैन (Rate Limit) से बचने के लिए दो टारगेट्स के बीच रैंडम डिले
            anti_ban_delay = random.randint(15, 35)
            print(f"😴 Sleeping for {anti_ban_delay} seconds before next target...")
            time.sleep(anti_ban_delay)
            
    except Exception as e:
        print(f"💥 Critical Error in Monitoring Job Loop: {e}")
    finally:
        db_pg.close()

def start_scheduler():
    """FastAPI स्टार्टअप पर शेड्यूलर इंजन को बैकग्राउंड में फायर करने के लिए"""
    scheduler.add_job(
        execute_monitoring_job,
        'interval',
        minutes=settings.MONITOR_INTERVAL_MINUTES,
        id='ig_live_monitor_job',
        replace_existing=True
    )
    scheduler.start()
    print(f"⏱️ APScheduler Engine Started. Monitoring loop running every {settings.MONITOR_INTERVAL_MINUTES} minutes.")
      
