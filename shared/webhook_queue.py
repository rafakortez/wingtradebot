"""Webhook queue for processing webhooks asynchronously"""
import asyncio
import time
from typing import Dict, Any, Optional, Set
from collections import deque
import logging

logger = logging.getLogger(__name__)

class WebhookJob:
    """Webhook job data structure"""
    def __init__(self, job_id: str, data: Dict[str, Any], account_number: str):
        self.id = job_id
        self.data = data
        self.timestamp = int(time.time() * 1000)
        self.retries = 0
        self.account_number = account_number

class WebhookQueue:
    """Queue for processing webhooks asynchronously"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0, duplicate_window: int = 30000):
        self.queue: deque = deque()
        self.processing = False
        self.processed_ids: Set[str] = set()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.duplicate_window = duplicate_window  # 30 seconds
        self.processor_callback = None
        self._load_processed_ids()
    
    def _load_processed_ids(self):
        """Load processed IDs from database"""
        try:
            from shared.database import get_db
            db = get_db()
            cursor = db.execute(
                "SELECT alert_id, account_number FROM processed_webhook_ids"
            )
            rows = cursor.fetchall()
            for row in rows:
                key = f"{row['alert_id']}_{row['account_number']}"
                self.processed_ids.add(key)
            logger.info(f"Loaded {len(self.processed_ids)} processed webhook IDs from database")
        except Exception as e:
            logger.error(f"Failed to load processed IDs: {e}")
            self.processed_ids = set()
    
    async def add(self, data: Dict[str, Any], account_number: str) -> str:
        """Add webhook to queue"""
        alert_id = data.get('id') or data.get('id', f"{int(time.time() * 1000)}_{hash(str(data))}")
        job_id = f"{alert_id}_{account_number}_{int(time.time() * 1000)}"
        
        job = WebhookJob(job_id, data, account_number)
        self.queue.append(job)
        
        logger.debug(f"Webhook queued: {job_id}, queue length: {len(self.queue)}")
        
        # Start processing if not already running
        if not self.processing:
            asyncio.create_task(self._process_queue())
        
        return job_id
    
    def check_for_duplicate(self, data: Dict[str, Any], account_number: str) -> bool:
        """Check if webhook is duplicate"""
        now = int(time.time() * 1000)
        alert_id = data.get('id')
        
        # Check processed IDs
        if alert_id:
            key = f"{alert_id}_{account_number}"
            if key in self.processed_ids:
                logger.debug(f"Duplicate detected by processed ID: {key}")
                return True
        
        # Check queue
        for job in self.queue:
            if (job.data.get('id') == alert_id and 
                job.account_number == account_number and
                (now - job.timestamp) < self.duplicate_window):
                return True
        
        return False
    
    def set_processor(self, processor_callback):
        """Set processor callback"""
        self.processor_callback = processor_callback
    
    async def _process_queue(self):
        """Process queue"""
        if self.processing:
            return
        
        self.processing = True
        
        while self.queue:
            job = self.queue.popleft()
            
            try:
                if self.processor_callback:
                    await self.processor_callback(job.data)
                    # Mark as processed
                    alert_id = job.data.get('id')
                    if alert_id:
                        key = f"{alert_id}_{job.account_number}"
                        self.processed_ids.add(key)
                        await self._store_processed_id(alert_id, job.account_number)
            except Exception as e:
                logger.error(f"Error processing webhook {job.id}: {e}")
                job.retries += 1
                
                if job.retries < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    self.queue.append(job)
                else:
                    logger.error(f"Webhook {job.id} failed after {self.max_retries} retries")
            
            # Small delay between jobs
            await asyncio.sleep(0.1)
        
        self.processing = False
    
    async def _store_processed_id(self, alert_id: str, account_number: str):
        """Store processed ID in database"""
        try:
            from shared.database import get_db
            import time
            db = get_db()
            db.execute(
                """INSERT OR IGNORE INTO processed_webhook_ids 
                   (alert_id, account_number, processed_at) 
                   VALUES (?, ?, ?)""",
                (alert_id, account_number, int(time.time() * 1000))
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to store processed ID: {e}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        return {
            "queueLength": len(self.queue),
            "processing": self.processing,
            "processedIdsCount": len(self.processed_ids)
        }


# Global instance
_webhook_queue: Optional[WebhookQueue] = None

def get_webhook_queue() -> WebhookQueue:
    """Get global webhook queue instance"""
    global _webhook_queue
    if _webhook_queue is None:
        _webhook_queue = WebhookQueue()
    return _webhook_queue


