"""
Automated cleanup scheduler for ETL Processor
Handles automatic cleanup of expired NLQ sessions
"""

import schedule
import time
import threading
import logging
import asyncio
from datetime import datetime
from database import DatabaseManager

logger = logging.getLogger(__name__)

class CleanupScheduler:
    """Manages automated cleanup of expired sessions"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.running = False
        self.thread = None
    
    def cleanup_expired_sessions(self):
        """Execute cleanup of expired sessions"""
        try:
            logger.info("Starting automated cleanup of expired sessions...")
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Call the PostgreSQL function to cleanup expired sessions
                    cursor.execute("SELECT cleanup_expired_sessions()")
                    cleanup_count = cursor.fetchone()[0]
                    conn.commit()
                    
                    if cleanup_count > 0:
                        logger.info(f"Successfully cleaned up {cleanup_count} expired sessions")
                    else:
                        logger.debug("No expired sessions found for cleanup")
                        
        except Exception as e:
            logger.error(f"Error during automated cleanup: {e}")
    
    def start_scheduler(self):
        """Start the cleanup scheduler"""
        if self.running:
            logger.warning("Cleanup scheduler is already running")
            return
        
        logger.info("Starting cleanup scheduler...")
        
        # Schedule cleanup every hour
        schedule.every().hour.do(self.cleanup_expired_sessions)
        
        # Also schedule a daily cleanup at 2 AM
        schedule.every().day.at("02:00").do(self.cleanup_expired_sessions)
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("Cleanup scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the cleanup scheduler"""
        if not self.running:
            logger.warning("Cleanup scheduler is not running")
            return
        
        logger.info("Stopping cleanup scheduler...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        schedule.clear()
        logger.info("Cleanup scheduler stopped")
    
    def _run_scheduler(self):
        """Internal method to run the scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Continue running even if there's an error
    
    def force_cleanup(self):
        """Force immediate cleanup (for testing/manual trigger)"""
        logger.info("Forcing immediate cleanup of expired sessions...")
        self.cleanup_expired_sessions()

# Global scheduler instance
cleanup_scheduler = CleanupScheduler()

def start_cleanup_scheduler():
    """Start the global cleanup scheduler"""
    cleanup_scheduler.start_scheduler()

def stop_cleanup_scheduler():
    """Stop the global cleanup scheduler"""
    cleanup_scheduler.stop_scheduler()

def force_cleanup():
    """Force immediate cleanup"""
    cleanup_scheduler.force_cleanup()
