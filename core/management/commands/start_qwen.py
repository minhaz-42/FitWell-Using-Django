import os
import subprocess
import time
import logging
from django.core.management.base import BaseCommand
import requests

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start the Qwen server if not already running'

    def handle(self, *args, **options):
        """Start Qwen server in background"""
        qwen_port = os.getenv("QWEN_LOCAL_PORT", "21002")
        qwen_url = f"http://localhost:{qwen_port}/v1/chat/completions"
        
        # Check if Qwen is already running
        try:
            response = requests.post(
                qwen_url,
                json={"model": "qwen", "messages": [{"role": "user", "content": "test"}], "max_tokens": 5},
                timeout=2
            )
            if response.status_code in [200, 400, 500]:  # Any response means server is running
                self.stdout.write(self.style.SUCCESS(f"✓ Qwen server already running on port {qwen_port}"))
                return
        except (requests.RequestException, Exception):
            pass  # Server not running, start it
        
        self.stdout.write(f"Starting Qwen server on port {qwen_port}...")
        
        try:
            # Get the script path
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            script_path = os.path.join(script_dir, "start_qwen_server.sh")
            
            if not os.path.exists(script_path):
                self.stdout.write(self.style.ERROR(f"Qwen start script not found: {script_path}"))
                return
            
            # Start the Qwen server in background
            process = subprocess.Popen(
                ["bash", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=script_dir,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.stdout.write(f"Qwen server process started (PID: {process.pid})")
            
            # Wait a bit for server to start
            time.sleep(5)
            
            # Check if server is responding
            for attempt in range(10):
                try:
                    response = requests.post(
                        qwen_url,
                        json={"model": "qwen", "messages": [{"role": "user", "content": "test"}], "max_tokens": 5},
                        timeout=2
                    )
                    self.stdout.write(self.style.SUCCESS(f"✓ Qwen server is ready on port {qwen_port}"))
                    return
                except requests.RequestException:
                    if attempt < 9:
                        time.sleep(2)
                    continue
            
            self.stdout.write(self.style.WARNING(f"⚠ Qwen server started but not responding yet. It may take a moment to load the model."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to start Qwen server: {str(e)}"))
