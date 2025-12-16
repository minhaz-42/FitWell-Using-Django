import subprocess
import time
import os
import sys
import socket
import threading
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    qwen_started = False
    
    def ready(self):
        """Start Qwen server when Django app is ready"""
        # Only run once per process
        if CoreConfig.qwen_started:
            return
        
        CoreConfig.qwen_started = True
        
        # Only start on main process (not on reloader)
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        self._start_qwen_if_needed()
    
    def _is_port_open(self, host='localhost', port=21002, timeout=2):
        """Check if port is open using socket"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((host, port))
            return result == 0
        except:
            return False
        finally:
            sock.close()
    
    def _start_qwen_if_needed(self):
        """Check if Qwen is running, start if not"""
        # Quick check if already running
        if self._is_port_open():
            print("\n✓ Qwen server already running on port 21002\n")
            sys.stdout.flush()
            return
        
        # Qwen not running, start it
        self._start_qwen()
    
    def _start_qwen(self):
        """Start Qwen server"""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(base_dir, 'start_qwen_server.sh')
            
            if not os.path.exists(script_path):
                print(f"⚠️  Qwen script not found at {script_path}")
                sys.stdout.flush()
                return
            
            print("\n" + "="*70)
            print("🚀 QWEN AI SERVER STARTUP")
            print("="*70)
            print("🔄 Stopping any existing Qwen processes...")
            
            # Kill existing processes
            subprocess.run(['pkill', '-9', '-f', 'qwen|local_qwen'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=base_dir)
            time.sleep(1)
            
            print("⏳ Starting Qwen model on port 21002...")
            print("   (Loading model - this takes 20-30 seconds)\n")
            sys.stdout.flush()
            
            # Start Qwen
            process = subprocess.Popen(
                ['bash', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=base_dir
            )
            
            # Print server output in background thread
            def print_output():
                try:
                    for line in process.stdout:
                        if line.strip():
                            print(f"[QWEN] {line.rstrip()}", flush=True)
                except:
                    pass
            
            output_thread = threading.Thread(target=print_output, daemon=True)
            output_thread.start()
            
            # Wait and show progress
            for i in range(1, 61):  # Wait up to 60 seconds
                time.sleep(1)
                
                if i % 15 == 0:
                    print(f"   ⏳ [{i}s] Loading model...", flush=True)
                
                # Try to connect every 2 seconds after 5s
                if i >= 5 and i % 2 == 0:
                    if self._is_port_open():
                        print(f"\n✓ Qwen server READY! ({i}s)")
                        print("="*70 + "\n")
                        sys.stdout.flush()
                        return
            
            print("\n✓ Qwen started (model may still be loading in background)")
            print("="*70 + "\n")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"⚠️  Error starting Qwen: {str(e)}")
            print("="*70 + "\n")
            sys.stdout.flush()


