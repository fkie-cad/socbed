@echo off

for /f "delims=," %%a in ('getmac /v /fo csv^| findstr 00-50-56-00-01-01') do set "name=%%a"

netsh interface ip set address name=%name% static 192.168.56.254
