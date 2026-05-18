<#
.SYNOPSIS
    Snapshot the current global butler credential into the project's .secrets/butler/.

.DESCRIPTION
    After running 'butler login' for an account, call this to save a copy of the
    resulting credential under .secrets/butler/<account>_creds (gitignored).
    Use butler-use-account.ps1 to restore any saved snapshot.

.PARAMETER Account
    Label to save under: 'runebitdice' or 'dragynrain'.

.EXAMPLE
    # After logging in as Dragynrain:
    butler login
    scripts\butler-save-account.ps1 -Account dragynrain
#>
param(
    [Parameter(Mandatory)]
    [ValidateSet("runebitdice", "dragynrain")]
    [string]$Account
)

$src     = "$env:USERPROFILE\.config\itch\butler_creds"
$credDir = Join-Path $PSScriptRoot "..\\.secrets\\butler"
$dest    = Join-Path $credDir "${Account}_creds"

if (-not (Test-Path $src)) {
    Write-Error "No butler_creds found at $src -- run 'butler login' first."
    exit 1
}

New-Item -ItemType Directory -Force $credDir | Out-Null
Copy-Item -Force $src $dest
Write-Host "Saved $Account cred to $dest"
