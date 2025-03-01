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
    def __init__(self, config: Dict[str, Any], update_callback: Callable[[List[str]], None] = None, graph_update_callback: Callable[[List[str]], None] = None):
        self.config = config
        self.update_callback = update_callback or (lambda x: None)
        self.graph_update_callback = graph_update_callback or (lambda x: None)
        self.critical_event_queue = PriorityQueue()
        self.non_critical_event_queue = PriorityQueue()
        self.processing = False
        self.last_event_time = 0

    def on_any_event(self, event):
        current_time = time.time()
        if current_time - self.last_event_time < self.config['watchdog'].get('debounce_interval', 5):
            return

        # Filter event types
        if event.event_type not in self.config.get('event_types', ['created', 'modified', 'deleted']):
            return

        priority = 1  # Default priority
        if event.event_type == 'modified':
            priority = 0  # Higher priority for modifications

        if event.src_path in self.config.get('critical_paths', []):
            self.critical_event_queue.put((priority, event))
        else:
            self.non_critical_event_queue.put((priority, event))

        self.last_event_time = current_time

        # Start processing batches if we have enough events
        batch_size = self.config['watchdog'].get('batch_size', 10)
        if self.critical_event_queue.qsize() >= batch_size:
            # Process critical events in a separate thread to avoid blocking
            thread = Thread(target=self.process_critical_events)
            thread.daemon = True
            thread.start()
        elif self.non_critical_event_queue.qsize() >= batch_size:
            # Process non-critical events in a separate thread
            thread = Thread(target=self.process_non_critical_events)
            thread.daemon = True
            thread.start()

    def process_critical_events(self):
        if self.processing:
            return

        self.processing = True
        events = []
        start_time = time.time()
        max_batch_time = self.config.get('max_batch_time', 5)
        
        while not self.critical_event_queue.empty() and time.time() - start_time < max_batch_time:
            priority, event = self.critical_event_queue.get()
            events.append(event)

        min_change_threshold = self.config['watchdog'].get('min_change_threshold', 3)
        if len(events) >= min_change_threshold:
            logger.info(f'Processing batch of {len(events)} critical events')
            try:
                self.update_callback([e.src_path for e in events])
                self.graph_update_callback([e.src_path for e in events])
            except Exception as e:
                logger.error(f'Error processing critical events: {e}')

        self.processing = False

    def process_non_critical_events(self):
        if self.processing:
            return

        self.processing = True
        events = []
        start_time = time.time()
        max_batch_time = self.config.get('max_batch_time', 5)
        
        while not self.non_critical_event_queue.empty() and time.time() - start_time < max_batch_time:
            priority, event = self.non_critical_event_queue.get()
            events.append(event)

        min_change_threshold = self.config['watchdog'].get('min_change_threshold', 3)
        if len(events) >= min_change_threshold:
            logger.info(f'Processing batch of {len(events)} non-critical events')
            try:
                self.update_callback([e.src_path for e in events])
                self.graph_update_callback([e.src_path for e in events])
            except Exception as e:
                logger.error(f'Error processing non-critical events: {e}')

        self.processing = False

class WatchdogService:
    def __init__(self, config: Dict[str, Any], update_callback: Callable[[List[str]], None] = None, graph_update_callback: Callable[[List[str]], None] = None):
        self.config = config
        self.update_callback = update_callback or (lambda x: None)
        self.graph_update_callback = graph_update_callback or (lambda x: None)
        self.observer = Observer()
        self.event_handler = BatchEventHandler(config, update_callback, graph_update_callback)

    def start(self):
        logger.info('Starting watchdog service')
        
        # Make sure app_path exists before starting the observer
        app_path = self.config.get('app_path')
        if not app_path or app_path == '/path/to/your/app' or not os.path.exists(app_path):
            logger.warning(f'App path does not exist: {app_path}. Watchdog service not started.')
            return
            
        self.observer.schedule(
            self.event_handler,
            path=app_path,
            recursive=True
        )
        self.observer.start()
        logger.info(f'Watchdog service monitoring: {app_path}')

    def stop(self):
        logger.info('Stopping watchdog service')
        self.observer.stop()
        self.observer.join()
