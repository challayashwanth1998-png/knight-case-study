"""
AWS CloudWatch logging integration.
Sends application logs to CloudWatch Logs for centralized monitoring.
"""
import logging
import time
import threading
from collections import deque
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

LOG_GROUP = "/knight-insurance/backend"
LOG_STREAM_PREFIX = "app"
CW_REGION = "us-east-1"

_cw_client = None
_log_stream_name = None
_sequence_token = None
_log_buffer = deque(maxlen=500)
_buffer_lock = threading.Lock()
_flush_thread = None
_initialized = False


def _get_client():
    global _cw_client
    if _cw_client is None:
        _cw_client = boto3.client(
            "logs",
            region_name=CW_REGION,
            config=BotoConfig(retries={"max_attempts": 2, "mode": "adaptive"}),
        )
    return _cw_client


def init_cloudwatch_logging():
    """Initialize CloudWatch log group and stream. Call once at app startup."""
    global _log_stream_name, _initialized, _flush_thread

    if _initialized:
        return

    try:
        client = _get_client()

        # Create log group (ignore if exists)
        try:
            client.create_log_group(logGroupName=LOG_GROUP)
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceAlreadyExistsException":
                raise

        # Create log stream with timestamp
        _log_stream_name = f"{LOG_STREAM_PREFIX}-{int(time.time())}"
        try:
            client.create_log_stream(
                logGroupName=LOG_GROUP,
                logStreamName=_log_stream_name,
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceAlreadyExistsException":
                raise

        _initialized = True

        # Start background flush thread
        _flush_thread = threading.Thread(target=_flush_loop, daemon=True)
        _flush_thread.start()

        logging.getLogger(__name__).info(
            f"CloudWatch logging initialized: {LOG_GROUP}/{_log_stream_name}"
        )

    except Exception as e:
        logging.getLogger(__name__).warning(
            f"CloudWatch init failed (logs will be local only): {e}"
        )


class CloudWatchHandler(logging.Handler):
    """Custom logging handler that buffers and sends logs to CloudWatch."""

    def emit(self, record):
        if not _initialized:
            return
        try:
            msg = self.format(record)
            with _buffer_lock:
                _log_buffer.append({
                    "timestamp": int(record.created * 1000),
                    "message": msg,
                })
        except Exception:
            pass


def _flush_loop():
    """Background thread that flushes log buffer to CloudWatch every 10 seconds."""
    while True:
        time.sleep(10)
        _flush_buffer()


def _flush_buffer():
    """Send buffered logs to CloudWatch."""
    global _sequence_token

    if not _initialized or not _log_buffer:
        return

    with _buffer_lock:
        events = list(_log_buffer)
        _log_buffer.clear()

    if not events:
        return

    # Sort by timestamp (required by CloudWatch)
    events.sort(key=lambda e: e["timestamp"])

    try:
        client = _get_client()
        kwargs = {
            "logGroupName": LOG_GROUP,
            "logStreamName": _log_stream_name,
            "logEvents": events,
        }
        if _sequence_token:
            kwargs["sequenceToken"] = _sequence_token

        response = client.put_log_events(**kwargs)
        _sequence_token = response.get("nextSequenceToken")
    except ClientError as e:
        # Handle token mismatch by retrying
        if e.response["Error"]["Code"] == "InvalidSequenceTokenException":
            token = e.response["Error"]["Message"].split(":")[-1].strip()
            _sequence_token = token
            try:
                kwargs["sequenceToken"] = token
                response = client.put_log_events(**kwargs)
                _sequence_token = response.get("nextSequenceToken")
            except Exception:
                pass
    except Exception:
        pass
