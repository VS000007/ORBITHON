"""
Cosmic Crew — Auto GitHub Sync Daemon
Monitors project files for modifications and automatically commits & pushes them to GitHub.
"""
import subprocess
import time
import os

WATCH_EXTS = ('.py', '.html', '.css', '.js', '.json', '.md')
INTERVAL_SECONDS = 15

def has_git_changes():
    try:
        res = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, check=True)
        return bool(res.stdout.strip())
    except Exception:
        return False

def sync_to_github():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Detected file changes. Syncing to GitHub...")
    subprocess.run(['git', 'add', '.'], check=False)
    subprocess.run(['git', 'commit', '-m', f"Auto-update: {time.strftime('%Y-%m-%d %H:%M:%S')}"], check=False)
    push_res = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
    if push_res.returncode == 0:
        print("[SUCCESS] Successfully pushed updates to GitHub.")
    else:
        print("[NOTICE] Push output:", push_res.stderr.strip() or push_res.stdout.strip())

def main():
    print("=" * 60)
    print(" COSMIC CREW AUTO-SYNC DAEMON INITIALIZED")
    print(f" Monitoring changes every {INTERVAL_SECONDS}s...")
    print("=" * 60)
    while True:
        try:
            if has_git_changes():
                sync_to_github()
        except KeyboardInterrupt:
            print("\nAuto-sync stopped by user.")
            break
        except Exception as e:
            print("[Error]", e)
        time.sleep(INTERVAL_SECONDS)

if __name__ == '__main__':
    main()
