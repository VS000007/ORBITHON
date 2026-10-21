@echo off
title ORBITHON - Deploy to Vercel
echo =======================================================
echo          ORBITHON - One-Click Vercel Deployer
echo =======================================================
echo.
echo Deploying latest changes to https://orbithon.vercel.app...
echo.
npx -y vercel --prod
echo.
pause
