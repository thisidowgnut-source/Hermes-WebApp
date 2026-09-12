$paths = @(
    "C:\Users\megat\.gemini",
    "C:\Users\megat\.ollama",
    "D:\.ollama",
    "C:\Users\megat\AppData\Local\Programs",
    "D:\UserPrograms",
    "C:\Users\megat\Hermes-WebApp",
    "C:\Users\megat\ObsidianVault"
)
foreach ($p in $paths) {
    if (Test-Path $p) {
        Add-MpPreference -ExclusionPath $p -ErrorAction SilentlyContinue
    }
}
$procs = @("node.exe", "python.exe", "pythonw.exe", "pwsh.exe", "agy.exe", "Antigravity IDE.exe")
foreach ($proc in $procs) {
    Add-MpPreference -ExclusionProcess $proc -ErrorAction SilentlyContinue
}
