import threading
import time
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional, Tuple

from config import settings


class AlertService:
    def __init__(self) -> None:
        self._alerts: Deque[Dict] = deque(maxlen=settings.MAX_STORED_ALERTS)
        self._last_raised: Dict[Tuple[str, str], float] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def raise_alert(self, alert_type: str, severity: str, message: str, zone: str) -> Optional[Dict]:
        key = (alert_type, zone)
        now = time.monotonic()

        with self._lock:
            last = self._last_raised.get(key)
            if last is not None and now - last < settings.ALERT_COOLDOWN_SECONDS:
                return None

            self._last_raised[key] = now
            alert = {
                "id": self._next_id,
                "type": alert_type,
                "severity": severity,
                "message": message,
                "zone": zone,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            self._next_id += 1
            self._alerts.append(alert)
            return dict(alert)

    def recent(self, limit: int = 10) -> List[Dict]:
        with self._lock:
            items = list(self._alerts)
        return [dict(alert) for alert in reversed(items[-limit:])]