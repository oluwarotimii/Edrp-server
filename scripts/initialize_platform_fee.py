import os
import sys
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
from models.global_settings import GlobalSetting
from config import settings

def initialize_platform_fee():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    db: Session = SessionLocal()
    try:
        # Check if platform_fee setting already exists
        platform_fee_setting = db.query(GlobalSetting).filter(GlobalSetting.key == "platform_fee").first()
        
        if not platform_fee_setting:
            # If not, create it with a default value (e.g., 100.00 NGN)
            new_setting = GlobalSetting(
                key="platform_fee",
                value="100.0", # Default to 100 NGN
                description="Fixed platform charge added to each transaction"
            )
            db.add(new_setting)
            db.commit()
            print("Platform fee initialized to 100.0 NGN in global settings.")
        else:
            print(f"Platform fee already exists: {platform_fee_setting.value} NGN.")
            
    except Exception as e:
        db.rollback()
        print(f"Error initializing platform fee: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    initialize_platform_fee()