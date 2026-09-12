Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Const PYTHON = "C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
Const APPDIR = "C:\Users\megat\Hermes-WebApp"
Const LOGDIR = APPDIR & "\logs"
Const PORT = 9220

' Ensure logs directory exists
If Not fso.FolderExists(LOGDIR) Then fso.CreateFolder(LOGDIR)

' 1. Start FastAPI server (with correct Python, health check built-in)
WshShell.Run "cmd /c """ & PYTHON & """ -m uvicorn main:app --host 127.0.0.1 --port " & PORT & " --app-dir """ & APPDIR & """", 0

' 2. Wait for server to be healthy (max 15 seconds)
Dim ready : ready = False
For i = 1 To 15
    WScript.Sleep 1000
    On Error Resume Next
    Dim http : Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "GET", "http://127.0.0.1:" & PORT & "/api/stats", False
    http.Send
    If Err.Number = 0 And http.Status = 200 Then
        ready = True
        Exit For
    End If
    On Error GoTo 0
Next

If Not ready Then
    WScript.Echo "Server failed to start on port " & PORT
    WScript.Quit 1
End If

' 3. Tunnel + Telegram menu button are owned by scripts/tunnel_keeper.py
'    (scheduled task HermesWebApp_TunnelKeeper, every 5 min, lockfile-guarded).
'    Do NOT start cloudflared here — keeper kills stale tunnels and re-syncs
'    the menu button whenever the trycloudflare URL changes.
WshShell.Run "cmd /c """ & PYTHON & """ """ & APPDIR & "\scripts\tunnel_keeper.py""", 0
