from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.postgres import init_pg_db, SessionLocal, MonitoredTarget
from app.scheduler import start_scheduler
from datetime import datetime

app = FastAPI(title="IG-Intel Live Monitoring OSINT API", version="2.0")

# स्टार्टअप पर DB और शेड्यूलर शुरू करें
@app.on_event("startup")
def startup_event():
    init_pg_db()       # Postgres टेबल्स बनाना
    start_scheduler()  # बैकग्राउंड लाइव मॉनिटर शुरू करना
    print("🚀 IG-Intel V2 System Engine Online & Monitoring Live...")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/monitor/add/{username}")
def add_target_to_monitor(username: str, db: Session = Depends(get_db)):
    """नया टारगेट लाइव मॉनिटरिंग लिस्ट में जोड़ने के लिए"""
    existing = db.query(MonitoredTarget).filter(MonitoredTarget.username == username).first()
    if existing:
        if existing.is_active:
            return {"message": f"@{username} is already being monitored live."}
        existing.is_active = True
        db.commit()
        return {"message": f"Live monitoring re-activated for @{username}."}
        
    new_target = MonitoredTarget(username=username, is_active=True, last_checked=datetime.utcnow())
    db.add(new_target)
    db.commit()
    return {"status": "success", "message": f"@{username} added to 24/7 Live Monitoring Queue."}

@app.post("/monitor/stop/{username}")
def stop_monitoring(username: str, db: Session = Depends(get_db)):
    """टार्गेट की लाइव मॉनिटरिंग रोकने के लिए"""
    target = db.query(MonitoredTarget).filter(MonitoredTarget.username == username).first()
    if not target:
        raise HTTPException(status_with=404, detail="Target not found in monitoring list.")
    target.is_active = False
    db.commit()
    return {"message": f"Live monitoring stopped for @{username}."}
      
