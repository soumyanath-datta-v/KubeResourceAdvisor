<#
.SYNOPSIS
    Captures Kubernetes pod CPU/memory metrics and restart data at 30-second intervals.

.DESCRIPTION
    Periodically runs 'kubectl top pods' and 'kubectl get po' filtered by service names,
    writes output to two text files formatted for the KubeResourceAdvisor Python app.

.PARAMETER Namespace
    The Kubernetes namespace to query (e.g., "test").

.PARAMETER ServiceNames
    Space-separated service name filter string (e.g., "tiger-daemon workflowservice").

.PARAMETER DurationMinutes
    How long (in minutes) the script should run before exiting.

.EXAMPLE
    .\collect-metrics.ps1 -Namespace test -ServiceNames "tiger-daemon workflowservice" -DurationMinutes 5
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Namespace,

    [Parameter(Mandatory = $false)]
    [string]$ServiceNames = "",

    [Parameter(Mandatory = $true)]
    [int]$DurationMinutes
)

# --- Validate kubectl is available ---
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Error "kubectl is not installed or not in PATH. Aborting."
    exit 1
}

# --- Generate output directory and file names ---
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$dataDir = Join-Path $PSScriptRoot "collected-data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
}
$metricsFile = Join-Path $dataDir "metrics_$timestamp.txt"
$restartsFile = Join-Path $dataDir "restarts_$timestamp.txt"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Kubernetes Metrics Collector" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Namespace       : $Namespace"
if ($ServiceNames) {
    Write-Host "Service filter  : $ServiceNames"
} else {
    Write-Host "Service filter  : All services"
}
Write-Host "Duration        : $DurationMinutes minute(s)"
Write-Host "Interval        : 30 seconds"
Write-Host "Metrics file    : $metricsFile"
Write-Host "Restarts file   : $restartsFile"
Write-Host "============================================" -ForegroundColor Cyan

# --- Initialise counters ---
$endTime = (Get-Date).AddMinutes($DurationMinutes)
$iteration = 0
$metricsLineCount = 0
$restartsLineCount = 0
$restartsLineIndex = 0   # global incrementing line counter for restarts file

# --- Main collection loop ---
while ((Get-Date) -lt $endTime) {
    $iteration++
    $now = Get-Date
    $remaining = $endTime - $now
    $timeTag = $now.ToString("HH:mm:ss")

    Write-Host "`n--- Iteration $iteration | $timeTag | $([math]::Round($remaining.TotalMinutes, 1)) min remaining ---" -ForegroundColor Yellow

    # ---- Capture CPU / Memory metrics (kubectl top pods) ----
    try {
        if ($ServiceNames) {
            $topOutput = kubectl top pods -n $Namespace 2>&1 | findstr $ServiceNames
        } else {
            $topOutput = kubectl top pods -n $Namespace 2>&1 | Select-Object -Skip 1
        }
        if ($topOutput) {
            foreach ($line in $topOutput) {
                $formattedLine = "[$timeTag] $line"
                Add-Content -Path $metricsFile -Value $formattedLine
                $metricsLineCount++
            }
            Write-Host "  Metrics  : captured $(@($topOutput).Count) line(s)" -ForegroundColor Green
        }
        else {
            Write-Host "  Metrics  : no matching pods found" -ForegroundColor DarkYellow
        }
    }
    catch {
        Write-Host "  Metrics  : ERROR - $_" -ForegroundColor Red
    }

    # ---- Capture restarts / health data (kubectl get po) ----
    try {
        if ($ServiceNames) {
            $poOutput = kubectl get po -n $Namespace 2>&1 | findstr $ServiceNames
        } else {
            $poOutput = kubectl get po -n $Namespace 2>&1 | Select-Object -Skip 1
        }
        if ($poOutput) {
            foreach ($line in $poOutput) {
                $restartsLineIndex++
                # Prepend a line number so the parser sees >= 7 tokens:
                #   index 0 = line#, 1 = NAME, 2 = READY, 3 = STATUS, 4 = RESTARTS, 5+ = AGE
                $formattedLine = "$restartsLineIndex $line"
                Add-Content -Path $restartsFile -Value $formattedLine
                $restartsLineCount++
            }
            Write-Host "  Restarts : captured $(@($poOutput).Count) line(s)" -ForegroundColor Green
        }
        else {
            Write-Host "  Restarts : no matching pods found" -ForegroundColor DarkYellow
        }
    }
    catch {
        Write-Host "  Restarts : ERROR - $_" -ForegroundColor Red
    }

    # ---- Wait 30 seconds (or exit if time is up) ----
    if ((Get-Date) -ge $endTime) {
        break
    }

    $sleepEnd = (Get-Date).AddSeconds(30)
    if ($sleepEnd -gt $endTime) {
        # Sleep only until the end time
        $remainingSleep = ($endTime - (Get-Date)).TotalSeconds
        if ($remainingSleep -gt 0) {
            Start-Sleep -Seconds ([math]::Ceiling($remainingSleep))
        }
    }
    else {
        Start-Sleep -Seconds 30
    }
}

# --- Summary ---
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host " Collection complete" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Iterations      : $iteration"
Write-Host "Metrics lines   : $metricsLineCount"
Write-Host "Restarts lines  : $restartsLineCount"
Write-Host "Metrics file    : $metricsFile"
Write-Host "Restarts file   : $restartsFile"
Write-Host ""
Write-Host "Run the advisor:" -ForegroundColor Green
Write-Host "  python run.py --metrics-file `"$metricsFile`" --restarts-file `"$restartsFile`""
