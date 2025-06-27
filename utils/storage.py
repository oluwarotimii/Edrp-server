import os
from sqlalchemy.orm import Session
from models.admission import ApplicationDocument
from config import settings

def get_school_storage_usage(school_id: int, db: Session) -> int:
    """Calculate the total storage used by a school in bytes."""
    total_size_bytes = 0
    
    # Get all ApplicationDocument records for the school
    documents = db.query(ApplicationDocument).filter(
        ApplicationDocument.school_id == school_id
    ).all()
    
    for doc in documents:
        # Sum the file_size from the database record
        if doc.file_size is not None:
            total_size_bytes += doc.file_size
        
        # Optional: Verify file existence and size on disk for consistency
        # This can be resource-intensive for many files
        # full_path = os.path.join(settings.UPLOAD_DIR, doc.file_path) # Assuming file_path is relative to UPLOAD_DIR
        # if os.path.exists(full_path):
        #     total_size_bytes += os.path.getsize(full_path)

    # Convert bytes to MB for consistency with max_storage_mb
    return total_size_bytes // (1024 * 1024)
