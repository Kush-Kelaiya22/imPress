<#
.SYNOPSIS
    Activates the ESP-IDF PowerShell environment for imPress.
.DESCRIPTION
    Discovers and dot-sources the ESP-IDF activation script or export script.
    Checks known standard installation paths (including EIM configs, K:\esp, C:\esp, and IDF_PATH).
    Sets IDF_PATH and adds IDF tools to the session PATH.
.EXAMPLE
    . .\firmware\activate_idf.ps1
    idf.py --version
#>

[CmdletBinding()]
param(
    [string]$IdfRoot = ""
)

$activated = $false

# 0. Check user-supplied or default $IdfRoot directly
if ($IdfRoot -and (Test-Path $IdfRoot)) {
    $rootCandidates = @(
        (Join-Path $IdfRoot "esp-idf\export.ps1"),
        (Join-Path $IdfRoot "export.ps1")
    )
    foreach ($cand in $rootCandidates) {
        if (Test-Path $cand) {
            $idfDir = Split-Path $cand -Parent
            $env:IDF_PATH = $idfDir
            Write-Host "[ESP-IDF] Found ESP-IDF in IdfRoot: $idfDir"
            break
        }
    }
}

# 1. Check if IDF_PATH is already set and has export.ps1
if (-not $activated -and $env:IDF_PATH -and (Test-Path "$env:IDF_PATH\export.ps1")) {
    Write-Host "[ESP-IDF] Using existing IDF_PATH: $env:IDF_PATH"
    . "$env:IDF_PATH\export.ps1"
    $activated = $true
}

# 2. Check eim_idf.json for standard registered profiles
if (-not $activated) {
    $eimConfigPaths = @(
        "C:\Espressif\tools\eim_idf.json",
        "$env:USERPROFILE\.espressif\eim_idf.json",
        "K:\Espressif\tools\eim_idf.json"
    )
    foreach ($config in $eimConfigPaths) {
        if (Test-Path $config) {
            try {
                $json = Get-Content $config -Raw | ConvertFrom-Json
                foreach ($inst in $json.idfInstalled) {
                    if ($inst.activationScript -and (Test-Path $inst.activationScript)) {
                        Write-Host "[ESP-IDF] Activating from EIM profile: $($inst.activationScript)"
                        . $inst.activationScript
                        $activated = $true
                        break
                    }
                }
            } catch {
                Write-Warning "Could not parse ${config}: $($_.Exception.Message)"
            }
        }
        if ($activated) { break }
    }
}

# 3. Check known standard installation locations for export.ps1 or profiles
if (-not $activated) {
    $candidates = @(
        "C:\Espressif\tools\Microsoft.v6.1.PowerShell_profile.ps1",
        "K:\Espressif\tools\Microsoft.v6.1.PowerShell_profile.ps1",
        "K:\esp\v6.1\esp-idf\export.ps1",
        "C:\esp\v6.1\esp-idf\export.ps1",
        "K:\esp-idf\export.ps1",
        "C:\esp-idf\export.ps1"
    )
    foreach ($cand in $candidates) {
        if (Test-Path $cand) {
            Write-Host "[ESP-IDF] Activating environment using $cand"
            . $cand
            $activated = $true
            break
        }
    }
}

if (-not $activated) {
    Write-Error "[ESP-IDF] Could not locate an ESP-IDF installation. Please install ESP-IDF or set IDF_PATH."
    return
}

# Verify idf.py is accessible
if (Get-Command idf.py -ErrorAction SilentlyContinue) {
    Write-Host "[ESP-IDF] ESP-IDF toolchain activated successfully."
} else {
    Write-Warning "[ESP-IDF] Environment script executed, but 'idf.py' is not recognized in the current scope."
}
