import json
import sqlite3
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from models.attendance import AttendanceRecord, TeacherAttendance
from models.assessment import Score
from models.student import Student
from models.communication import Message, BehaviorReport

class OfflineSyncService:
    """Service for handling offline data synchronization"""
    
    def __init__(self, offline_db_path: str = "offline_data.db"):
        self.offline_db_path = offline_db_path
        self.init_offline_database()
    
    def init_offline_database(self):
        """Initialize SQLite database for offline storage"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        # Create tables for offline data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                session_name TEXT,
                status TEXT NOT NULL,
                period_id INTEGER,
                subject_id INTEGER,
                notes TEXT,
                marked_by INTEGER NOT NULL,
                marked_at TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                location_verified INTEGER DEFAULT 0,
                school_id INTEGER NOT NULL,
                sync_status TEXT DEFAULT 'pending',
                created_offline_at TEXT NOT NULL,
                conflict_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_teacher_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                clock_in_time TEXT,
                clock_out_time TEXT,
                status TEXT NOT NULL,
                notes TEXT,
                clock_in_latitude REAL,
                clock_in_longitude REAL,
                clock_out_latitude REAL,
                clock_out_longitude REAL,
                location_verified INTEGER DEFAULT 0,
                school_id INTEGER NOT NULL,
                sync_status TEXT DEFAULT 'pending',
                created_offline_at TEXT NOT NULL,
                conflict_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                score REAL NOT NULL,
                remarks TEXT,
                recorded_by INTEGER NOT NULL,
                recorded_at TEXT NOT NULL,
                school_id INTEGER NOT NULL,
                sync_status TEXT DEFAULT 'pending',
                created_offline_at TEXT NOT NULL,
                conflict_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_behavior_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                reported_by INTEGER NOT NULL,
                incident_date TEXT NOT NULL,
                incident_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT,
                witnesses TEXT,
                action_taken TEXT,
                follow_up_required INTEGER DEFAULT 0,
                follow_up_date TEXT,
                school_id INTEGER NOT NULL,
                sync_status TEXT DEFAULT 'pending',
                created_offline_at TEXT NOT NULL,
                conflict_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'direct',
                priority TEXT DEFAULT 'normal',
                parent_message_id INTEGER,
                school_id INTEGER NOT NULL,
                sync_status TEXT DEFAULT 'pending',
                created_offline_at TEXT NOT NULL,
                conflict_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type TEXT NOT NULL,
                sync_direction TEXT NOT NULL,
                records_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                errors TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT DEFAULT 'running'
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_offline_attendance_sync ON offline_attendance(sync_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_offline_teacher_attendance_sync ON offline_teacher_attendance(sync_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_offline_scores_sync ON offline_scores(sync_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_offline_behavior_reports_sync ON offline_behavior_reports(sync_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_offline_messages_sync ON offline_messages(sync_status)')
        
        conn.commit()
        conn.close()
    
    def store_attendance_offline(
        self,
        student_id: int,
        date: str,
        status: str,
        marked_by: int,
        school_id: int,
        session_name: Optional[str] = None,
        period_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        notes: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_verified: bool = False
    ) -> int:
        """Store attendance record offline"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO offline_attendance (
                student_id, date, session_name, status, period_id, subject_id,
                notes, marked_by, marked_at, latitude, longitude, location_verified,
                school_id, created_offline_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id, date, session_name, status, period_id, subject_id,
            notes, marked_by, datetime.utcnow().isoformat(), latitude, longitude,
            int(location_verified), school_id, datetime.utcnow().isoformat()
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def store_teacher_attendance_offline(
        self,
        teacher_id: int,
        date: str,
        status: str,
        school_id: int,
        clock_in_time: Optional[str] = None,
        clock_out_time: Optional[str] = None,
        notes: Optional[str] = None,
        clock_in_latitude: Optional[float] = None,
        clock_in_longitude: Optional[float] = None,
        clock_out_latitude: Optional[float] = None,
        clock_out_longitude: Optional[float] = None,
        location_verified: bool = False
    ) -> int:
        """Store teacher attendance record offline"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO offline_teacher_attendance (
                teacher_id, date, clock_in_time, clock_out_time, status, notes,
                clock_in_latitude, clock_in_longitude, clock_out_latitude, clock_out_longitude,
                location_verified, school_id, created_offline_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            teacher_id, date, clock_in_time, clock_out_time, status, notes,
            clock_in_latitude, clock_in_longitude, clock_out_latitude, clock_out_longitude,
            int(location_verified), school_id, datetime.utcnow().isoformat()
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def store_score_offline(
        self,
        assessment_id: int,
        student_id: int,
        score: float,
        recorded_by: int,
        school_id: int,
        remarks: Optional[str] = None
    ) -> int:
        """Store score record offline"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO offline_scores (
                assessment_id, student_id, score, remarks, recorded_by,
                recorded_at, school_id, created_offline_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment_id, student_id, score, remarks, recorded_by,
            datetime.utcnow().isoformat(), school_id, datetime.utcnow().isoformat()
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def store_behavior_report_offline(
        self,
        student_id: int,
        reported_by: int,
        incident_date: str,
        incident_type: str,
        severity: str,
        title: str,
        description: str,
        school_id: int,
        location: Optional[str] = None,
        witnesses: Optional[str] = None,
        action_taken: Optional[str] = None,
        follow_up_required: bool = False,
        follow_up_date: Optional[str] = None
    ) -> int:
        """Store behavior report offline"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO offline_behavior_reports (
                student_id, reported_by, incident_date, incident_type, severity,
                title, description, location, witnesses, action_taken,
                follow_up_required, follow_up_date, school_id, created_offline_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id, reported_by, incident_date, incident_type, severity,
            title, description, location, witnesses, action_taken,
            int(follow_up_required), follow_up_date, school_id, datetime.utcnow().isoformat()
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_pending_sync_records(self, table_name: str) -> List[Dict[str, Any]]:
        """Get records pending synchronization"""
        
        conn = sqlite3.connect(self.offline_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT * FROM {table_name} 
            WHERE sync_status = 'pending' 
            ORDER BY created_offline_at ASC
        ''')
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records
    
    def mark_record_synced(self, table_name: str, record_id: int, online_id: Optional[int] = None):
        """Mark a record as successfully synced"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        update_data = {'sync_status': 'synced', 'synced_at': datetime.utcnow().isoformat()}
        if online_id:
            update_data['online_id'] = online_id
        
        set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values()) + [record_id]
        
        cursor.execute(f'''
            UPDATE {table_name} 
            SET {set_clause}
            WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()
    
    def mark_record_conflict(self, table_name: str, record_id: int, conflict_data: Dict[str, Any]):
        """Mark a record as having a sync conflict"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            UPDATE {table_name} 
            SET sync_status = 'conflict', conflict_data = ?
            WHERE id = ?
        ''', (json.dumps(conflict_data), record_id))
        
        conn.commit()
        conn.close()
    
    def mark_record_error(self, table_name: str, record_id: int, error_message: str):
        """Mark a record as having a sync error"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            UPDATE {table_name} 
            SET sync_status = 'error', error_message = ?
            WHERE id = ?
        ''', (error_message, record_id))
        
        conn.commit()
        conn.close()
    
    async def sync_attendance_records(self, db: Session) -> Dict[str, Any]:
        """Sync offline attendance records to online database"""
        
        sync_log_id = self.start_sync_log("attendance", "upload")
        
        try:
            pending_records = self.get_pending_sync_records("offline_attendance")
            
            success_count = 0
            error_count = 0
            errors = []
            
            for record in pending_records:
                try:
                    # Check for existing record (conflict detection)
                    existing = db.query(AttendanceRecord).filter(
                        AttendanceRecord.student_id == record['student_id'],
                        AttendanceRecord.date == record['date'],
                        AttendanceRecord.session_name == record['session_name'],
                        AttendanceRecord.period_id == record['period_id']
                    ).first()
                    
                    if existing:
                        # Handle conflict
                        conflict_data = {
                            "existing_status": existing.status,
                            "offline_status": record['status'],
                            "existing_marked_at": existing.marked_at.isoformat() if existing.marked_at else None,
                            "offline_marked_at": record['marked_at']
                        }
                        self.mark_record_conflict("offline_attendance", record['id'], conflict_data)
                        continue
                    
                    # Create new attendance record
                    db_attendance = AttendanceRecord(
                        student_id=record['student_id'],
                        date=datetime.fromisoformat(record['date']).date(),
                        session_name=record['session_name'],
                        status=record['status'],
                        period_id=record['period_id'],
                        subject_id=record['subject_id'],
                        notes=record['notes'],
                        marked_by=record['marked_by'],
                        marked_at=datetime.fromisoformat(record['marked_at']),
                        latitude=record['latitude'],
                        longitude=record['longitude'],
                        location_verified=bool(record['location_verified']),
                        school_id=record['school_id']
                    )
                    
                    db.add(db_attendance)
                    db.flush()
                    
                    self.mark_record_synced("offline_attendance", record['id'], db_attendance.id)
                    success_count += 1
                    
                except Exception as e:
                    error_message = str(e)
                    errors.append(f"Record {record['id']}: {error_message}")
                    self.mark_record_error("offline_attendance", record['id'], error_message)
                    error_count += 1
            
            db.commit()
            
            result = {
                "total_records": len(pending_records),
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors
            }
            
            self.complete_sync_log(sync_log_id, success_count, error_count, errors)
            
            return result
            
        except Exception as e:
            self.complete_sync_log(sync_log_id, 0, 0, [str(e)], status="failed")
            raise
    
    async def sync_teacher_attendance_records(self, db: Session) -> Dict[str, Any]:
        """Sync offline teacher attendance records to online database"""
        
        sync_log_id = self.start_sync_log("teacher_attendance", "upload")
        
        try:
            pending_records = self.get_pending_sync_records("offline_teacher_attendance")
            
            success_count = 0
            error_count = 0
            errors = []
            
            for record in pending_records:
                try:
                    # Check for existing record
                    existing = db.query(TeacherAttendance).filter(
                        TeacherAttendance.teacher_id == record['teacher_id'],
                        TeacherAttendance.date == record['date']
                    ).first()
                    
                    if existing:
                        # Update existing record with clock out time if provided
                        if record['clock_out_time'] and not existing.clock_out_time:
                            existing.clock_out_time = datetime.fromisoformat(record['clock_out_time'])
                            existing.clock_out_latitude = record['clock_out_latitude']
                            existing.clock_out_longitude = record['clock_out_longitude']
                            
                            # Calculate total hours
                            if existing.clock_in_time:
                                delta = existing.clock_out_time - existing.clock_in_time
                                existing.total_hours = delta.total_seconds() / 3600
                            
                            self.mark_record_synced("offline_teacher_attendance", record['id'], existing.id)
                            success_count += 1
                        else:
                            # Conflict - both have same type of record
                            conflict_data = {
                                "existing_clock_in": existing.clock_in_time.isoformat() if existing.clock_in_time else None,
                                "offline_clock_in": record['clock_in_time'],
                                "existing_clock_out": existing.clock_out_time.isoformat() if existing.clock_out_time else None,
                                "offline_clock_out": record['clock_out_time']
                            }
                            self.mark_record_conflict("offline_teacher_attendance", record['id'], conflict_data)
                        continue
                    
                    # Create new teacher attendance record
                    db_attendance = TeacherAttendance(
                        teacher_id=record['teacher_id'],
                        date=datetime.fromisoformat(record['date']).date(),
                        clock_in_time=datetime.fromisoformat(record['clock_in_time']) if record['clock_in_time'] else None,
                        clock_out_time=datetime.fromisoformat(record['clock_out_time']) if record['clock_out_time'] else None,
                        status=record['status'],
                        notes=record['notes'],
                        clock_in_latitude=record['clock_in_latitude'],
                        clock_in_longitude=record['clock_in_longitude'],
                        clock_out_latitude=record['clock_out_latitude'],
                        clock_out_longitude=record['clock_out_longitude'],
                        location_verified=bool(record['location_verified']),
                        school_id=record['school_id']
                    )
                    
                    # Calculate total hours if both times available
                    if db_attendance.clock_in_time and db_attendance.clock_out_time:
                        delta = db_attendance.clock_out_time - db_attendance.clock_in_time
                        db_attendance.total_hours = delta.total_seconds() / 3600
                    
                    db.add(db_attendance)
                    db.flush()
                    
                    self.mark_record_synced("offline_teacher_attendance", record['id'], db_attendance.id)
                    success_count += 1
                    
                except Exception as e:
                    error_message = str(e)
                    errors.append(f"Record {record['id']}: {error_message}")
                    self.mark_record_error("offline_teacher_attendance", record['id'], error_message)
                    error_count += 1
            
            db.commit()
            
            result = {
                "total_records": len(pending_records),
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors
            }
            
            self.complete_sync_log(sync_log_id, success_count, error_count, errors)
            
            return result
            
        except Exception as e:
            self.complete_sync_log(sync_log_id, 0, 0, [str(e)], status="failed")
            raise
    
    async def sync_score_records(self, db: Session) -> Dict[str, Any]:
        """Sync offline score records to online database"""
        
        sync_log_id = self.start_sync_log("scores", "upload")
        
        try:
            pending_records = self.get_pending_sync_records("offline_scores")
            
            success_count = 0
            error_count = 0
            errors = []
            
            for record in pending_records:
                try:
                    # Check for existing score
                    existing = db.query(Score).filter(
                        Score.assessment_id == record['assessment_id'],
                        Score.student_id == record['student_id']
                    ).first()
                    
                    if existing:
                        # Conflict - score already exists
                        conflict_data = {
                            "existing_score": existing.score,
                            "offline_score": record['score'],
                            "existing_recorded_at": existing.recorded_at.isoformat() if existing.recorded_at else None,
                            "offline_recorded_at": record['recorded_at']
                        }
                        self.mark_record_conflict("offline_scores", record['id'], conflict_data)
                        continue
                    
                    # Create new score record
                    db_score = Score(
                        assessment_id=record['assessment_id'],
                        student_id=record['student_id'],
                        score=record['score'],
                        remarks=record['remarks'],
                        recorded_by=record['recorded_by'],
                        recorded_at=datetime.fromisoformat(record['recorded_at']),
                        school_id=record['school_id']
                    )
                    
                    db.add(db_score)
                    db.flush()
                    
                    self.mark_record_synced("offline_scores", record['id'], db_score.id)
                    success_count += 1
                    
                except Exception as e:
                    error_message = str(e)
                    errors.append(f"Record {record['id']}: {error_message}")
                    self.mark_record_error("offline_scores", record['id'], error_message)
                    error_count += 1
            
            db.commit()
            
            result = {
                "total_records": len(pending_records),
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors
            }
            
            self.complete_sync_log(sync_log_id, success_count, error_count, errors)
            
            return result
            
        except Exception as e:
            self.complete_sync_log(sync_log_id, 0, 0, [str(e)], status="failed")
            raise
    
    async def sync_all_offline_data(self, db: Session) -> Dict[str, Any]:
        """Sync all types of offline data"""
        
        results = {}
        
        # Sync attendance records
        try:
            results["attendance"] = await self.sync_attendance_records(db)
        except Exception as e:
            results["attendance"] = {"error": str(e)}
        
        # Sync teacher attendance records
        try:
            results["teacher_attendance"] = await self.sync_teacher_attendance_records(db)
        except Exception as e:
            results["teacher_attendance"] = {"error": str(e)}
        
        # Sync score records
        try:
            results["scores"] = await self.sync_score_records(db)
        except Exception as e:
            results["scores"] = {"error": str(e)}
        
        # Add more sync operations as needed
        
        return results
    
    def start_sync_log(self, sync_type: str, sync_direction: str) -> int:
        """Start a sync log entry"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sync_log (sync_type, sync_direction, started_at)
            VALUES (?, ?, ?)
        ''', (sync_type, sync_direction, datetime.utcnow().isoformat()))
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return log_id
    
    def complete_sync_log(
        self,
        log_id: int,
        success_count: int,
        error_count: int,
        errors: List[str],
        status: str = "completed"
    ):
        """Complete a sync log entry"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sync_log 
            SET completed_at = ?, success_count = ?, error_count = ?, 
                errors = ?, status = ?
            WHERE id = ?
        ''', (
            datetime.utcnow().isoformat(),
            success_count,
            error_count,
            json.dumps(errors),
            status,
            log_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_sync_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get sync history"""
        
        conn = sqlite3.connect(self.offline_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sync_log 
            ORDER BY started_at DESC 
            LIMIT ?
        ''', (limit,))
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records
    
    def get_conflict_records(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get records with sync conflicts"""
        
        conn = sqlite3.connect(self.offline_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if table_name:
            cursor.execute(f'''
                SELECT * FROM {table_name} 
                WHERE sync_status = 'conflict'
                ORDER BY created_offline_at DESC
            ''')
        else:
            # Get conflicts from all tables
            tables = [
                "offline_attendance",
                "offline_teacher_attendance", 
                "offline_scores",
                "offline_behavior_reports",
                "offline_messages"
            ]
            
            all_conflicts = []
            for table in tables:
                cursor.execute(f'''
                    SELECT *, '{table}' as table_name FROM {table} 
                    WHERE sync_status = 'conflict'
                    ORDER BY created_offline_at DESC
                ''')
                all_conflicts.extend([dict(row) for row in cursor.fetchall()])
            
            conn.close()
            return all_conflicts
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records
    
    def resolve_conflict(
        self,
        table_name: str,
        record_id: int,
        resolution: str,
        resolved_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Resolve a sync conflict"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        if resolution == "use_offline":
            # Mark as pending to retry sync
            cursor.execute(f'''
                UPDATE {table_name} 
                SET sync_status = 'pending', conflict_data = NULL
                WHERE id = ?
            ''', (record_id,))
        elif resolution == "use_online":
            # Mark as resolved, don't sync
            cursor.execute(f'''
                UPDATE {table_name} 
                SET sync_status = 'resolved_online', conflict_data = NULL
                WHERE id = ?
            ''', (record_id,))
        elif resolution == "merge" and resolved_data:
            # Update record with merged data and mark as pending
            set_clauses = []
            values = []
            for key, value in resolved_data.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            set_clauses.append("sync_status = 'pending'")
            set_clauses.append("conflict_data = NULL")
            values.append(record_id)
            
            cursor.execute(f'''
                UPDATE {table_name} 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            ''', values)
        
        conn.commit()
        conn.close()
        
        return True
    
    def cleanup_synced_records(self, days_old: int = 30) -> int:
        """Clean up old synced records"""
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        tables = [
            "offline_attendance",
            "offline_teacher_attendance",
            "offline_scores", 
            "offline_behavior_reports",
            "offline_messages"
        ]
        
        total_deleted = 0
        
        for table in tables:
            cursor.execute(f'''
                DELETE FROM {table} 
                WHERE sync_status = 'synced' 
                AND synced_at < ?
            ''', (cutoff_date,))
            
            total_deleted += cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return total_deleted
    
    def get_offline_stats(self) -> Dict[str, Any]:
        """Get offline data statistics"""
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        tables = {
            "attendance": "offline_attendance",
            "teacher_attendance": "offline_teacher_attendance",
            "scores": "offline_scores",
            "behavior_reports": "offline_behavior_reports",
            "messages": "offline_messages"
        }
        
        for name, table in tables.items():
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN sync_status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN sync_status = 'synced' THEN 1 ELSE 0 END) as synced,
                    SUM(CASE WHEN sync_status = 'conflict' THEN 1 ELSE 0 END) as conflicts,
                    SUM(CASE WHEN sync_status = 'error' THEN 1 ELSE 0 END) as errors
                FROM {table}
            ''')
            
            result = cursor.fetchone()
            stats[name] = {
                "total": result[0],
                "pending": result[1],
                "synced": result[2],
                "conflicts": result[3],
                "errors": result[4]
            }
        
        conn.close()
        
        return stats
