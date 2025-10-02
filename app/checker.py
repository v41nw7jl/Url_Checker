# FILE: app/checker.py

"""
Core URL Checking Logic for URL Monitor
Uses concurrent requests to efficiently check multiple URLs.
"""

import requests
import logging
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from app.database import URLRecord, get_database
from app.config import get_config

logger = logging.getLogger(__name__)

def check_single_url(url_record: URLRecord) -> Dict[str, Any]:
    """
    Checks a single URL and returns a result dictionary.

    Args:
        url_record: The URLRecord object from the database.

    Returns:
        A dictionary containing the check results.
    """
    config = get_config()
    result = {
        'url_id': url_record.id,
        'is_up': False,
        'status_code': None,
        'response_time': None,
        'error_message': None
    }

    headers = {'User-Agent': config.get('checker.user_agent', 'URLMonitor/1.0')}
    timeout = url_record.timeout or config.get('checker.request_timeout', 10)

    start_time = perf_counter()
    try:
        response = requests.get(
            url_record.url,
            timeout=timeout,
            headers=headers,
            verify=config.get('checker.verify_ssl', True),
            allow_redirects=config.get('checker.follow_redirects', True)
        )
        result['status_code'] = response.status_code
        # Consider any 2xx or 3xx status code as "up"
        if 200 <= response.status_code < 400:
            result['is_up'] = True
        else:
            result['error_message'] = f"HTTP Status {response.status_code}"

    except requests.exceptions.Timeout:
        result['error_message'] = "Request timed out"
    except requests.exceptions.RequestException as e:
        result['error_message'] = f"Connection error: {type(e).__name__}"
    except Exception as e:
        result['error_message'] = f"An unexpected error occurred: {e}"
    finally:
        end_time = perf_counter()
        result['response_time'] = round((end_time - start_time) * 1000, 2) # in milliseconds

    logger.debug(f"Checked {url_record.url}: UP={result['is_up']}, RT={result['response_time']}ms")
    return result

def run_all_checks() -> int:
    """
    Retrieves all active URLs from the database and checks them concurrently.
    Saves the results back to the database.

    Returns:
        The number of URLs that were checked.
    """
    logger.info("Starting URL check cycle...")
    config = get_config()
    db = get_database()
    
    urls_to_check = db.list_urls(active_only=True)
    if not urls_to_check:
        logger.info("No active URLs to check.")
        return 0

    checked_count = 0
    max_workers = config.get('checker.concurrent_limit', 10)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(check_single_url, url): url for url in urls_to_check}

        for future in as_completed(future_to_url):
            url_record = future_to_url[future]
            try:
                result = future.result()
                db.save_check_result(
                    url_id=result['url_id'],
                    status_code=result['status_code'],
                    response_time=result['response_time'],
                    is_up=result['is_up'],
                    error_message=result['error_message']
                )
                checked_count += 1
            except Exception as e:
                logger.error(f"Error processing check result for {url_record.url}: {e}")

    logger.info(f"URL check cycle finished. Checked {checked_count} URLs.")
    
    # Perform database cleanup if enabled
    if config.get('database.auto_cleanup', True):
        retention_days = config.get('database.retention_days', 30)
        logger.info(f"Running automatic cleanup of records older than {retention_days} days.")
        deleted_count = db.cleanup_old_records(retention_days)
        logger.info(f"Cleanup complete. Removed {deleted_count} old records.")
        
    return checked_count