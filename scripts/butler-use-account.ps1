<#
.SYNOPSIS
    Swap the global butler credential to a project-stored account cred.

.DESCRIPTION
    Butler uses a single global cred file at %USERPROFILE%\.config\itch\butler_creds.
    This project stores per-account snapshots under .secrets/butler/<account>_creds
    (gitignored). Run this before any butler push to ensure you're pushing as
    the right itch.io account.

.PARAMETER Account
    Which account to activate: 'runebitdice' or 'dragynrain'.

.EXAMPLE
    scripts\butler-use-account.ps1 -Account dragynrain
    scripts\butler-use-account.ps1 -Account runebitdice
#>
param(
    [Parameter(Mandatory)]
    [ValidateSet("runebitdice", "dragynrain")]
    [string]$Account
)

$credDir  = Join-Path $PSScriptRoot "..\\.secrets\\butler"
$src      = Join-Path $credDir "${Account}_creds"
$dest     = "$env:USERPROFILE\.config\itch\butler_creds"

if (-not (Test-Path $src)) {
    Write-Error "No saved cred for '$Account' at $src -- log in first with 'butler login' and then run scripts\butler-save-account.ps1 -Account $Account"
    exit 1
}

Copy-Item -Force $src $dest
Write-Host "butler now set to account: $Account"
