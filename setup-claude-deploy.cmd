@echo off
rem One-time setup: create a SEPARATE deploy key for Claude and authorize it on the Guangzhou server.
rem Your own key (%USERPROFILE%\.ssh\youai_deploy) is only used to install the new public key; it is not copied.
rem Revoke later: on the server, delete the line ending in "claude-deploy" from /root/.ssh/authorized_keys.
setlocal
set "SERVER=root@182.61.14.185"
set "HOST=182.61.14.185"
set "DIR=E:\data\codexYOUAI-data\claude-deploy"
set "MYKEY=%USERPROFILE%\.ssh\youai_deploy"
set "SSHOPTS=-i "%MYKEY%" -o BatchMode=yes -o StrictHostKeyChecking=yes"

if not exist "%MYKEY%" (echo [x] Your deploy key was not found: %MYKEY% & goto :fail)
if not exist "%DIR%" mkdir "%DIR%"

echo [1/3] Creating Claude's own key in %DIR%
if exist "%DIR%\id_ed25519" (
  echo     key already exists, reusing it
) else (
  ssh-keygen -q -t ed25519 -N "" -C claude-deploy -f "%DIR%\id_ed25519" || goto :fail
)
set /p PUB=<"%DIR%\id_ed25519.pub"

echo [2/3] Authorizing the new public key on the server (using your existing key)
ssh %SSHOPTS% %SERVER% "umask 077; mkdir -p ~/.ssh; touch ~/.ssh/authorized_keys; grep -qxF '%PUB%' ~/.ssh/authorized_keys || echo '%PUB%' >> ~/.ssh/authorized_keys; echo authorized: $(grep -c claude-deploy ~/.ssh/authorized_keys) claude-deploy keys" || goto :fail

echo [3/3] Saving the server's verified host key for strict checking
ssh %SSHOPTS% %SERVER% "cat /etc/ssh/ssh_host_ed25519_key.pub" > "%DIR%\host_key.pub" || goto :fail
for /f "tokens=1,2" %%a in (%DIR%\host_key.pub) do (echo %HOST% %%a %%b)> "%DIR%\known_hosts"
del "%DIR%\host_key.pub"

echo.
echo Done. Test login with the new key:
ssh -i "%DIR%\id_ed25519" -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="%DIR%\known_hosts" %SERVER% "echo OK: claude-deploy key works on $(hostname)" || goto :fail
echo.
echo Now tell Claude "done". Claude will ask for access to %DIR% in each new conversation.
pause
exit /b 0

:fail
echo.
echo Setup failed. Nothing on the server was removed. Send a screenshot to Claude.
pause
exit /b 1
