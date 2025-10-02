#!/usr/bin/env python3
"""
URL Monitor - Main Application Entry Point
Command-line interface and application bootstrapping
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import get_config, get_database, __version__
from app.config import create_default_config


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
    
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
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
        config_file = args.config or 'config.json'
        if not Path(config_file).exists() or args.force:
            if create_default_config(config_file):
                logger.info(f"Created configuration: {config_file}")
            else:
                logger.error(f"Failed to create config: {config_file}")
                return 1
        
        db = get_database()
        if db.initialize():
            logger.info("Database initialized")
            
            config = get_config()
            Path(config.get('logging.file')).parent.mkdir(parents=True, exist_ok=True)
            Path('data').mkdir(exist_ok=True)
            
            print("✓ URL Monitor initialized")
            print(f"Config: {config_file}")
            print(f"Database: {config.get('database.path')}")
            print("\nNext: python main.py --add-url https://example.com")
            return 0
        else:
            logger.error("Database initialization failed")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_add_url(args):
    """Add URL to monitoring"""
    logger = setup_logging()
    
    url = args.url.strip()
    if not validate_url(url):
        print(f"Invalid URL: {url}")
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
            print(f"Failed to add URL: {url}")
            return 1
            
    except Exception as e:
        logger.error(f"Error adding URL: {e}")
        print(f"Error: {e}")
        return 1


def cmd_list_urls(args):
    """List all URLs"""
    setup_logging()
    
    try:
        db = get_database()
        urls = db.list_urls(active_only=args.active_only)
        
        if not urls:
            print("No URLs configured")
            return 0
        
        if args.format == 'JSON':
            import json
            url_data = [{
                'id': u.id,
                'url': u.url,
                'name': u.name,
                'active': u.is_active,
                'timeout': u.timeout
            } for u in urls]
            print(json.dumps(url_data, indent=2))
        else:
            print(f"\n{'Active' if args.active_only else 'All'} URLs:")
            print("-" * 70)
            for url in urls:
                status = "✓" if url.is_active else "✗"
                name = f" ({url.name})" if url.name else ""
                print(f"[{url.id}] {status} {url.url}{name}")
            print(f"\nTotal: {len(urls)}")
        
        return 0
        
    except Exception as e:
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
            success = db.delete_url(url_id)
            identifier = f"ID {url_id}"
        except ValueError:
            success = db.delete_url_by_address(url_input)
            identifier = url_input
        
        if success:
            print(f"✓ Removed: {identifier}")
            return 0
        else:
            print(f"Not found: {identifier}")
            return 1
            
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        return 1


def cmd_status(args):
    """Show URL status"""
    setup_logging()
    
    try:
        db = get_database()
        all_status = db.get_all_status()
        
        if not all_status:
            print("No URLs configured")
            return 0
        
        if args.format == 'JSON':
            import json
            print(json.dumps(all_status, indent=2, default=str))
        else:
            print(f"\nStatus Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            print("=" * 70)
            
            for status in all_status:
                if not args.show_all and not status.get('is_active'):
                    continue
                
                url = status['url'][:50]
                if status.get('is_up'):
                    print(f"✓ UP   {url}")
                elif status.get('checked_at'):
                    print(f"✗ DOWN {url}")
                else:
                    print(f"? PEND {url}")
            
            print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_verify_db(args):
    """Verify database"""
    setup_logging()
    
    try:
        db = get_database()
        stats = db.get_database_stats()
        
        print("\nDatabase Stats:")
        print(f"  URLs: {stats.get('total_urls', 0)} total, {stats.get('active_urls', 0)} active")
        print(f"  Checks: {stats.get('total_checks', 0)} total")
        print(f"  Size: {stats.get('db_file_size', 0):,} bytes")
        print("\n✓ Database OK")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="URL Monitor")
    
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--version', action='store_true', help='Show version')
    
    parser.add_argument('--init', action='store_true', help='Initialize')
    parser.add_argument('--force', action='store_true', help='Force init')
    parser.add_argument('--add-url', metavar='URL', help='Add URL')
    parser.add_argument('--name', help='URL name')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout')
    parser.add_argument('--active', action='store_true', default=True)
    parser.add_argument('--list-urls', action='store_true', help='List URLs')
    parser.add_argument('--active-only', action='store_true', help='Active only')
    parser.add_argument('--remove-url', metavar='URL', help='Remove URL')
    parser.add_argument('--status', action='store_true', help='Show status')
    parser.add_argument('--verify-db', action='store_true', help='Verify DB')
    parser.add_argument('--format', choices=['TABLE', 'JSON'], default='TABLE')
    parser.add_argument('--show-all', action='store_true', help='Show all')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"URL Monitor v{__version__}")
        return 0
    
    if args.init:
        return cmd_init(args)
    elif args.add_url:
        args.url = args.add_url
        return cmd_add_url(args)
    elif args.list_urls:
        return cmd_list_urls(args)
    elif args.remove_url:
        args.url = args.remove_url
        return cmd_remove_url(args)
    elif args.status:
        return cmd_status(args)
    elif args.verify_db:
        return cmd_verify_db(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())