# Persistent host for runtime.ps1 — loads UIAutomation once, loops on stdin.
# Protocol: one JSON operation per stdin line; one JSON result per stdout line.
param(
    [Parameter(Mandatory = $true)]
    [string]$RuntimePath
)

$ErrorActionPreference = "Stop"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

$raw = Get-Content -Raw -Encoding UTF8 -Path $RuntimePath
# Drop param(...) block by line scan (regex stops at first nested ')')
$lines = [System.Collections.Generic.List[string]]::new()
($raw -split "`r?`n") | ForEach-Object { $lines.Add($_) }
if ($lines.Count -gt 0 -and $lines[0] -match '^\s*param\s*\(') {
    for ($i = 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*\)\s*$') {
            $lines.RemoveRange(0, $i + 1)
            break
        }
    }
}
$raw = ($lines -join "`n")
# Drop trailing one-shot main
$idx = $raw.LastIndexOf('try {')
if ($idx -gt 0) { $raw = $raw.Substring(0, $idx) }

Invoke-Expression $raw

Write-Host '{"ok":true,"handshake":{"host":"persistent","runtime":"loaded"}}'

while ($true) {
    $line = [Console]::In.ReadLine()
    if ($null -eq $line) { break }
    $line = $line.Trim()
    if (-not $line) { continue }
    try {
        $op = $line | ConvertFrom-Json
        $result = Invoke-OrcaOperation $op
        Write-OrcaJson $result
    } catch {
        Write-OrcaJson ([pscustomobject]@{ ok = $false; error = [string]$_.Exception.Message })
    }
}
