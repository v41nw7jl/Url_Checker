#!/usr/bin/env python3
"""
URL Monitor - Main Application Entry Point
Command-line interface and application bootstrapping
"""

import sys
import os
import argparse
import logging
import threading
from pathlib import Path
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import get_config, get_database, __version__
from app.config import create_default_config
from app.checker import run_all_checks
from app.scheduler import start_scheduler
from app.dashboard import create_app


def setup_logging():
    """Setup application logging"""
    config = get_config()
    log_level = getattr(logging, config.get('logging.level', 'INFO').upper())
    log_format = config.get('logging.format')
    
    log_file = config.get('logging.file', 'logs/monitor.log')
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Silence noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.INFO)
    
    return logging.getLogger(__name__)


def validate_url(url):
    """Basic URL validation"""
    import re
    pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return bool(pattern.match(url))


def cmd_init(args):
    """Initialize the application"""
    logger = setup_logging()
    
    try:
        config_file = get_config().config_file
        if not Path(config_file).exists() or args.force:
            if create_default_config(config_file):
                logger.info(f"Created configuration: {config_file}")
            else:
                logger.error(f"Failed to create config: {config_file}")
                return 1
        
        db = get_database()
        if db.initialize():
            logger.info("Database initialized")
            config = get_config() # Re-read config in case it was just created
            Path(config.get('logging.file')).parent.mkdir(parents=True, exist_ok=True)
            Path(config.get('database.path')).parent.mkdir(parents=True, exist_ok=True)
            
            print("✓ URL Monitor initialized successfully.")
            print(f"  Config:   {config_file}")
            print(f"  Database: {config.get('database.path')}")
            print("\nNext steps:")
            print("  1. Add a URL: python main.py --add-url https://example.com")
            print("  2. Run a manual check: python main.py --run-check")
            print("  3. View status: python main.py --status")
            return 0
        else:
            logger.error("Database initialization failed")
            return 1
            
    except Exception as e:
        logger.error(f"Initialization error: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1


def cmd_add_url(args):
    """Add URL to monitoring"""
    logger = setup_logging()
    
    url = args.url.strip()
    if not validate_url(url):
        print(f"Error: Invalid URL format provided: {url}")
        return 1
    
    try:
        db = get_database()
        url_id = db.add_url(url, args.name, args.timeout, args.active)
        
        if url_id:
            print(f"✓ Added URL (ID: {url_id}): {url}")
            if args.name:
                print(f"  Name: {args.name}")
            return 0
        else:
            print(f"Failed to add URL. It might already exist.")
            return 1
            
    except Exception as e:
        logger.error(f"Error adding URL: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1


def cmd_list_urls(args):
    """List all URLs"""
    setup_logging()
    
    try:
        db = get_database()
        urls = db.list_urls(active_only=args.active_only)
        
        if not urls:
            print("No URLs have been configured yet.")
            return 0
        
        if args.format == 'JSON':
            import json
            url_data = [{'id': u.id, 'url': u.url, 'name': u.name, 'active': u.is_active, 'timeout': u.timeout} for u in urls]
            print(json.dumps(url_data, indent=2))
        else:
            print(f"\n--- {'Active' if args.active_only else 'All'} Monitored URLs ---")
            for url in urls:
                status = "✓ Active" if url.is_active else "✗ Inactive"
                name = f" ({url.name})" if url.name else ""
                print(f"[{url.id: >3}] {status:<10} | {url.url}{name}")
            print(f"--------------------------\nTotal: {len(urls)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error listing URLs: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1


def cmd_remove_url(args):
    """Remove URL from monitoring"""
    logger = setup_logging()
    
    try:
        db = get_database()
        url_input = args.url.strip()
        
        try:
            url_id = int(url_input)
            url_record = db.get_url(url_id)
            if url_record:
                success = db.delete_url(url_id)
                identifier = f"ID {url_id} ({url_record.url})"
            else:
                success = False
        except ValueError:
            success = db.delete_url_by_address(url_input)
            identifier = url_input
        
        if success:
            print(f"✓ Removed: {identifier}")
            return 0
        else:
            print(f"Error: URL not found: {url_input}")
            return 1
            
    except Exception as e:
        logger.error(f"Error removing URL: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1


def cmd_status(args):
    """Show URL status"""
    setup_logging()
    
    try:
        db = get_database()
        all_status = db.get_all_status()
        
        if not all_status:
            print("No URLs configured. Add one with --add-url.")
            return 0
        
        if args.format == 'JSON':
            import json
            print(json.dumps(all_status, indent=2, default=str))
        else:
            print(f"\n--- Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
            for status in all_status:
                if not args.show_all and not status.get('is_active'):
                    continue
                
                url = status['url'][:60].ljust(60)
                if status.get('is_up'):
                    resp_time = f"{status['response_time']:.2f}ms".rjust(10)
                    print(f"✓ UP     | {url} | {resp_time}")
                elif status.get('checked_at'):
                    error = (status.get('error_message') or 'Unknown Error')[:20].rjust(20)
                    print(f"✗ DOWN   | {url} | {error}")
                else:
                    print(f"? PEND   | {url} | {'Not checked yet'.rjust(20)}")
            print("--------------------------------------------------")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1

def cmd_run_check(args):
    """Manually trigger a check of all active URLs"""
    logger = setup_logging()
    print("Starting manual check of all active URLs...")
    checked_count = run_all_checks()
    print(f"✓ Check complete. {checked_count} URLs were processed.")
    return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description=f"URL Monitor v{__version__}")
    
    # Global options
    parser.add_argument('--config', help='Path to custom config file')
    parser.add_argument('--version', action='version', version=f"URL Monitor v{__version__}")
    
    # Sub-commands (emulated with argument groups)
    action_group = parser.add_argument_group('actions')
    action_group.add_argument('--init', action='store_true', help='Initialize config and database')
    action_group.add_argument('--force', action='store_true', help='Force re-initialization, overwriting existing config')
    
    action_group.add_argument('--add-url', metavar='URL', help='Add a new URL to monitor')
    action_group.add_argument('--list-urls', action='store_true', help='List all monitored URLs')
    action_group.add_argument('--remove-url', metavar='ID_OR_URL', help='Remove a URL by its ID or full address')
    
    action_group.add_argument('--status', action='store_true', help='Show the current status of all URLs')
    action_group.add_argument('--run-check', action='store_true', help='Run a manual check cycle on all active URLs')
    action_group.add_argument('--schedule', action='store_true', help='Start the scheduler to run checks automatically (blocking)')
    action_group.add_argument('--dashboard', action='store_true', help='Start the web dashboard (blocking)')

    # Options for adding/modifying URLs
    add_url_group = parser.add_argument_group('url options')
    add_url_group.add_argument('--name', help='A friendly name for the URL')
    add_url_group.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    add_url_group.add_argument('--active', action='store_true', default=True, help='Set the URL as active (default)')
    
    # Options for listing/status
    display_group = parser.add_argument_group('display options')
    display_group.add_argument('--active-only', action='store_true', help='Show only active URLs when listing')
    display_group.add_argument('--show-all', action='store_true', help='Show inactive URLs in status report')
    display_group.add_argument('--format', choices=['TABLE', 'JSON'], default='TABLE', help='Output format for lists and status')

    args = parser.parse_args()
    
    # Handle combined dashboard and schedule command
    if args.dashboard and args.schedule:
        setup_logging()
        logging.info("Starting dashboard and scheduler in combined mode.")
        scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()
        
        app = create_app()
        config = get_config()
        app.run(host=config.get('dashboard.host'), port=config.get('dashboard.port'))
        return 0

    # Handle single action commands
    if args.init: return cmd_init(args)
    if args.add_url:
        args.url = args.add_url
        return cmd_add_url(args)
    if args.list_urls: return cmd_list_urls(args)
    if args.remove_url:
        args.url = args.remove_url
        return cmd_remove_url(args)
    if args.status: return cmd_status(args)
    if args.run_check: return cmd_run_check(args)
    if args.schedule:
        setup_logging()
        return start_scheduler()
    if args.dashboard:
        setup_logging()
        app = create_app()
        config = get_config()
        app.run(host=config.get('dashboard.host'), port=config.get('dashboard.port'), debug=config.get('dashboard.debug'))
        return 0

    parser.print_help()
    return 0

if __name__ == '__main__':
    # Ensure we are in the project root directory
    os.chdir(Path(__file__).parent.resolve())
    sys.exit(main())