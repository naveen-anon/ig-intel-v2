from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MonitoredTarget(Base):
    __tablename__ = "monitored_targets"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    last_checked = Column(DateTime, default=datetime.utcnow)
    follower_count_cache = Column(Integer, default=0)

# डेटाबेस टेबल्स बनाने के लिए यूटिलिटी
def init_pg_db():
    Base.metadata.create_all(bind=engine)
  
