import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import List, Dict, Any, Callable
import logging
from queue import PriorityQueue
from threading import Thread
import os

logger = logging.getLogger(__name__)

class BatchEventHandler(FileSystemEventHandler):
    def __init__(self, config: Dict[str, Any], update_callback: Callable[[List[str]], None] = None):
        self.config = config
        self.update_callback = update_callback or (lambda x: None)
        self.critical_event_queue = PriorityQueue()
        self.non_critical_event_queue = PriorityQueue()
        self.processing = False
        self.last_event_time = 0
        self.changed_files = set()  # Track unique changed files

    def on_any_event(self, event):
        # Skip directory events
        if hasattr(event, 'is_directory') and event.is_directory:
            return
            
        # Skip temporary files and hidden files
        if event.src_path.endswith(('.swp', '.tmp', '~')) or os.path.basename(event.src_path).startswith('.'):
            return
            
        # Check if file extension is in ignored list
        ignored_extensions = self.config.get('ignored_extensions', ['.pyc', '.pyo', '.pyd', '.git'])
        if any(event.src_path.endswith(ext) for ext in ignored_extensions):
            return

        current_time = time.time()
        debounce_interval = self.config.get('watchdog', {}).get('debounce_interval', 5)
        
        # Add to changed files set
        self.changed_files.add(event.src_path)
        
        # If we're within debounce interval, just record the file but don't process yet
        if current_time - self.last_event_time < debounce_interval:
            return

        # Filter event types
        event_types = self.config.get('event_types', ['created', 'modified', 'deleted'])
        if event.event_type not in event_types:
            return

        priority = 1  # Default priority
        if event.event_type == 'modified':
            priority = 0  # Higher priority for modifications

        # Check if path is in critical paths
        critical_paths = self.config.get('critical_paths', [])
        is_critical = any(event.src_path.startswith(path) for path in critical_paths)
        
        if is_critical:
            self.critical_event_queue.put((priority, event))
        else:
            self.non_critical_event_queue.put((priority, event))

        self.last_event_time = current_time

        # Start processing batches if we have enough events
        batch_size = self.config.get('watchdog', {}).get('batch_size', 10)
        
        # If we have enough critical events, process them first
        if self.critical_event_queue.qsize() >= batch_size:
            thread = Thread(target=self.process_critical_events)
            thread.daemon = True
            thread.start()
        # Otherwise, if we have enough non-critical events, process those
        elif self.non_critical_event_queue.qsize() >= batch_size:
            thread = Thread(target=self.process_non_critical_events)
            thread.daemon = True
            thread.start()
        # Or if we've accumulated enough changed files, process everything
        elif len(self.changed_files) >= batch_size:
            thread = Thread(target=self.process_all_events)
            thread.daemon = True
            thread.start()

    def process_all_events(self):
        """Process all accumulated changed files"""
        if self.processing:
            return

        self.processing = True
        try:
            if self.changed_files:
                changed_files_list = list(self.changed_files)
                logger.info(f'Processing batch of {len(changed_files_list)} changed files')
                self.update_callback(changed_files_list)
                self.changed_files.clear()
        except Exception as e:
            logger.error(f'Error processing all events: {e}')
        finally:
            self.processing = False

    def process_critical_events(self):
        if self.processing:
            return

        self.processing = True
        events = []
        start_time = time.time()
        max_batch_time = self.config.get('max_batch_time', 5)
        
        try:
            while not self.critical_event_queue.empty() and time.time() - start_time < max_batch_time:
                priority, event = self.critical_event_queue.get()
                events.append(event)

            min_change_threshold = self.config.get('watchdog', {}).get('min_change_threshold', 3)
            if len(events) >= min_change_threshold:
                logger.info(f'Processing batch of {len(events)} critical events')
                changed_files = [e.src_path for e in events]
                self.update_callback(changed_files)
        except Exception as e:
            logger.error(f'Error processing critical events: {e}')
        finally:
            self.processing = False

    def process_non_critical_events(self):
        if self.processing:
            return

        self.processing = True
        events = []
        start_time = time.time()
        max_batch_time = self.config.get('max_batch_time', 5)
        
        try:
            while not self.non_critical_event_queue.empty() and time.time() - start_time < max_batch_time:
                priority, event = self.non_critical_event_queue.get()
                events.append(event)

            min_change_threshold = self.config.get('watchdog', {}).get('min_change_threshold', 3)
            if len(events) >= min_change_threshold:
                logger.info(f'Processing batch of {len(events)} non-critical events')
                changed_files = [e.src_path for e in events]
                self.update_callback(changed_files)
        except Exception as e:
            logger.error(f'Error processing non-critical events: {e}')
        finally:
            self.processing = False

class WatchdogService:
    def __init__(self, config: Dict[str, Any], update_callback: Callable[[List[str]], None] = None):
        self.config = config
        self.update_callback = update_callback
        self.observer = Observer()
        self.event_handler = BatchEventHandler(config, update_callback)
        self.is_running = False
        
        # Set default values if not provided
        if 'watchdog' not in self.config:
            self.config['watchdog'] = {}
            
        if 'debounce_interval' not in self.config['watchdog']:
            self.config['watchdog']['debounce_interval'] = 5
            
        if 'batch_size' not in self.config['watchdog']:
            self.config['watchdog']['batch_size'] = 10
            
        if 'min_change_threshold' not in self.config['watchdog']:
            self.config['watchdog']['min_change_threshold'] = 3

    def start(self):
        if self.is_running:
            logger.warning('Watchdog service is already running')
            return
            
        logger.info('Starting watchdog service')
        
        # Make sure app_path exists before starting the observer
        app_path = self.config.get('app_path')
        if not app_path or app_path == '/path/to/your/app' or not os.path.exists(app_path):
            logger.warning(f'App path does not exist: {app_path}. Watchdog service not started.')
            return
            
        try:
            self.observer.schedule(
                self.event_handler,
                path=app_path,
                recursive=True
            )
            self.observer.start()
            self.is_running = True
            logger.info(f'Watchdog service monitoring: {app_path}')
            
            # Process any initial events that might have been queued
            Thread(target=self.event_handler.process_all_events).start()
        except Exception as e:
            logger.error(f'Failed to start watchdog service: {e}')

    def stop(self):
        if not self.is_running:
            logger.warning('Watchdog service is not running')
            return
            
        logger.info('Stopping watchdog service')
        try:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info('Watchdog service stopped')
        except Exception as e:
            logger.error(f'Error stopping watchdog service: {e}')
            
    def force_scan(self):
        """Force a scan of the app directory"""
        if not self.is_running:
            logger.warning('Cannot force scan, watchdog service is not running')
            return
            
        logger.info('Forcing a scan of the app directory')
        if self.update_callback:
            # Pass an empty list to trigger a full scan
            self.update_callback([])
