import subprocess
import time
import os
import signal
import requests
from django.core.management.commands.runserver import Command as RunServerCommand


class Command(RunServerCommand):
    """Custom runserver that auto-starts Qwen server first"""
    
    def handle(self, *args, **options):
        """Start Qwen before starting Django runserver"""
        qwen_process = None
        
        try:
            # Start Qwen server in background
            qwen_process = self._start_qwen_server()
            
            if not qwen_process:
                self.stdout.write(self.style.WARNING("⚠️  Qwen failed to start, but continuing anyway..."))
            
            # Continue with normal runserver
            super().handle(*args, **options)
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\n🛑 Shutting down..."))
        finally:
            # Kill Qwen server when Django shuts down
            if qwen_process:
                self._kill_qwen_server(qwen_process)
    
    def _start_qwen_server(self):
        """Start the local Qwen server in background with health checks"""
        try:
            # Get the project base directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            script_path = os.path.join(base_dir, 'start_qwen_server.sh')
            
            if not os.path.exists(script_path):
                self.stdout.write(self.style.ERROR(f"❌ Qwen startup script not found at {script_path}"))
                return None
            
            self.stdout.write(self.style.SUCCESS("\n" + "="*60))
            self.stdout.write(self.style.SUCCESS("🚀 STARTING QWEN AI SERVER"))
            self.stdout.write(self.style.SUCCESS("="*60))
            
            # Kill any existing Qwen processes
            subprocess.run(['pkill', '-9', '-f', 'qwen|local_qwen'], 
                         capture_output=True, cwd=base_dir)
            time.sleep(1)
            
            # Start the server in background
            process = subprocess.Popen(
                ['bash', script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=base_dir
            )
            
            if not process or process.poll() is not None:
                self.stdout.write(self.style.ERROR("❌ Failed to start Qwen process"))
                return None
            
            self.stdout.write(self.style.WARNING("⏳ Loading Qwen 0.5B model..."))
            self.stdout.write(self.style.WARNING("   (This takes 20-30 seconds, please wait...)"))
            self.stdout.write("")
            
            # Wait and show progress
            for i in range(1, 36):
                time.sleep(1)
                
                # Every 5 seconds, show progress
                if i % 5 == 0:
                    self.stdout.write(f"   [{i:2d}s] Loading...", ending="")
                    self.stdout.flush()
                
                # Every 10 seconds, try to connect
                if i % 10 == 0:
                    try:
                        resp = requests.post(
                            "http://localhost:21002/v1/chat/completions",
                            json={"model": "qwen", "messages": [{"role": "user", "content": "test"}], "max_tokens": 5},
                            timeout=5
                        )
                        if resp.status_code == 200:
                            self.stdout.write("")
                            self.stdout.write(self.style.SUCCESS("✓ Qwen server is responding!"))
                            self.stdout.write("")
                            return process
                    except:
                        pass
            
            # Final check after wait
            try:
                resp = requests.post(
                    "http://localhost:21002/v1/chat/completions",
                    json={"model": "qwen", "messages": [{"role": "user", "content": "test"}], "max_tokens": 5},
                    timeout=5
                )
                if resp.status_code == 200:
                    self.stdout.write("")
                    self.stdout.write(self.style.SUCCESS("✓ Qwen server is ready!"))
                    self.stdout.write("")
                    return process
            except:
                pass
            
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("⚠️  Qwen may still be loading... continuing anyway"))
            self.stdout.write("")
            return process
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error starting Qwen: {str(e)}"))
            return None
    
    def _kill_qwen_server(self, process):
        """Kill the Qwen server process"""
        try:
            self.stdout.write(self.style.WARNING("\n🛑 Stopping Qwen server..."))
            subprocess.run(['pkill', '-9', '-f', 'qwen|local_qwen'], 
                         capture_output=True)
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except:
                    process.kill()
            self.stdout.write(self.style.SUCCESS("✓ Qwen stopped"))
        except:
            pass

