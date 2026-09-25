import zipfile
import string
import itertools
import threading
import time
import os
import tempfile
import shutil
import logging
from typing import Optional, List, Iterator, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZipCracker:
    """
    A professional-grade ZIP password cracker supporting brute-force 
    and dictionary attacks.
    """
    def __init__(self):
        self.zip_path: Optional[Path] = None
        self.char_set = string.ascii_lowercase + string.digits
        self.attempts = 0
        self.found_password: Optional[str] = None
        self.is_running = False
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.current_length = 1
        self.attempts_per_second = 0.0
        self.thread: Optional[threading.Thread] = None
        self.temp_dir = Path(tempfile.mkdtemp(prefix="brutus_"))
        self.mode = "brute"  # "brute" or "dictionary"
        self.dictionary_path: Optional[Path] = None

    def load_file(self, file_path: str) -> bool:
        """Loads and validates the target ZIP file."""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            with zipfile.ZipFile(path) as zf:
                # Check if it's actually encrypted (at least one file)
                is_encrypted = any(info.flag_bits & 0x1 for info in zf.infolist())
                if not is_encrypted:
                    logger.warning(f"File {file_path} does not seem to be password protected.")
            
            self.zip_path = path
            return True
        except (zipfile.BadZipFile, Exception) as e:
            logger.error(f"Failed to load ZIP: {e}")
            return False

    def _is_safe_path(self, base_dir: Path, target_path: Path) -> bool:
        """Prevents Zip Slip vulnerability by validating extraction paths."""
        try:
            resolved_base = base_dir.resolve()
            resolved_target = (base_dir / target_path).resolve()
            return resolved_base in resolved_target.parents or resolved_base == resolved_target
        except Exception:
            return False

    def test_password(self, password: str) -> bool:
        """
        Tests a password against the ZIP file.
        Uses a secure extraction method to verify success.
        """
        if not self.zip_path:
            return False
            
        try:
            test_dir = self.temp_dir / f"test_{threading.get_ident()}"
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Use only a small file for testing if possible, or first file
            with zipfile.ZipFile(self.zip_path) as zf:
                # Tries to extract the first file to verify password
                first_file = zf.namelist()[0]
                
                # Check for Zip Slip
                if not self._is_safe_path(test_dir, Path(first_file)):
                    return False
                    
                zf.extract(first_file, path=test_dir, pwd=password.encode())
            
            # Clean up after successful (or failed) test
            shutil.rmtree(test_dir, ignore_errors=True)
            return True
        except (RuntimeError, zipfile.BadZipFile, Exception):
            # RuntimeError is usually "Bad password"
            return False

    def _run_brute_force(self):
        """Internal method for brute force attack."""
        max_length = 8
        while self.is_running and self.current_length <= max_length:
            for combo in itertools.product(self.char_set, repeat=self.current_length):
                if not self.is_running:
                    return
                
                self.attempts += 1
                password = ''.join(combo)
                
                if self.test_password(password):
                    self.found_password = password
                    self.is_running = False
                    logger.info(f"Password found: {password}")
                    return
                
                # Performance metrics
                now = time.time()
                delta = now - self.start_time
                if delta >= 1:
                    self.attempts_per_second = self.attempts / delta
            
            self.current_length += 1

    def _run_dictionary(self):
        """Internal method for dictionary attack."""
        if not self.dictionary_path or not self.dictionary_path.exists():
            logger.error("Dictionary file missing")
            self.is_running = False
            return

        try:
            with open(self.dictionary_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if not self.is_running:
                        return
                    
                    password = line.strip()
                    if not password:
                        continue
                        
                    self.attempts += 1
                    if self.test_password(password):
                        self.found_password = password
                        self.is_running = False
                        logger.info(f"Password found: {password}")
                        return
                    
                    # Performance metrics
                    now = time.time()
                    delta = now - self.start_time
                    if delta >= 1:
                        self.attempts_per_second = self.attempts / delta
        except Exception as e:
            logger.error(f"Dictionary attack error: {e}")
        
        self.is_running = False

    def start_cracking(self, mode: str = "brute", dictionary_path: Optional[str] = None):
        """Launches the cracking process in a background thread."""
        if self.is_running or not self.zip_path:
            return

        self.mode = mode
        if mode == "dictionary":
            if not dictionary_path:
                logger.error("Dictionary mode requires a file path")
                return
            self.dictionary_path = Path(dictionary_path)

        self.is_running = True
        self.attempts = 0
        self.found_password = None
        self.start_time = time.time()
        
        target = self._run_brute_force if mode == "brute" else self._run_dictionary
        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()

    def stop_cracking(self):
        """Stops the current cracking session."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.elapsed_time = time.time() - self.start_time

    def cleanup(self):
        """Removes temporary files and directories."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
