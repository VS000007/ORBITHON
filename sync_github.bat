@echo off
setlocal
echo =======================================================
echo    COSMIC CREW - AUTOMATED GITHUB SYNC
echo =======================================================
echo Checking for changes...
git add .
git diff-index --quiet HEAD --
if %errorlevel% neq 0 (
    echo Changes detected! Committing and pushing to GitHub...
    git commit -m "Auto-update: %date% %time%"
    git push origin main
    echo [SUCCESS] Pushed to GitHub repository!
) else (
    echo [UP-TO-DATE] No changes detected.
)
echo =======================================================
pause
