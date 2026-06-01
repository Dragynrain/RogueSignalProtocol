<#
.SYNOPSIS
    Patch an AUR PKGBUILD's pkgver, _vertag, and sha256sums, then verify.

.DESCRIPTION
    Called by update-aur.bat. Lives in its own file (invoked with -File and named
    parameters) so the replacements are plain PowerShell with no cmd quote-escaping.
    The previous inline `powershell -Command "...\"sha256sums...\"..."` form had the
    sha256 replace silently fail (cmd mangled the escaped double quotes), shipping a
    stale checksum to AUR. This script replaces reliably AND verifies, exiting
    non-zero if the result does not match - so a wrong hash can never ship silently.

.PARAMETER PkgBuild
    Path to the PKGBUILD to patch.
.PARAMETER PkgVer
    Value for pkgver= (e.g. 1.0.0 or 1.0.0_beta).
.PARAMETER VerTag
    Value for _vertag= (e.g. 1.0.0 or 1.0.0-beta).
.PARAMETER Sha256
    64-char hex sha256 of the source tarball.
#>
param(
    [Parameter(Mandatory)][string]$PkgBuild,
    [Parameter(Mandatory)][string]$PkgVer,
    [Parameter(Mandatory)][string]$VerTag,
    [Parameter(Mandatory)][string]$Sha256
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $PkgBuild)) {
    Write-Error "PKGBUILD not found: $PkgBuild"
    exit 1
}

# Guard against a junk/empty hash slipping through.
if ($Sha256 -notmatch '^[0-9a-fA-F]{64}$') {
    Write-Error "Refusing to patch: Sha256 '$Sha256' is not a 64-char hex digest"
    exit 1
}
$Sha256 = $Sha256.ToLower()

$content = Get-Content $PkgBuild -Raw
$content = $content -replace 'pkgver=[^\r\n]+', "pkgver=$PkgVer"
$content = $content -replace '_vertag=[^\r\n]+', "_vertag=$VerTag"
# Replacement value is pre-expanded literal hex (no '$' chars), so -replace's
# substitution metacharacters are not a concern here.
$content = $content -replace "sha256sums=\('[^']+'\)", "sha256sums=('$Sha256')"

# AUR requires Unix (LF) line endings.
$content = $content -replace "`r`n", "`n"
[System.IO.File]::WriteAllText($PkgBuild, $content)

# Verify the patch actually took. A no-op replace (e.g. the sha regex not matching)
# must fail loudly rather than ship a stale checksum.
$after = Get-Content $PkgBuild -Raw
$failures = @()
if ($after -notmatch [regex]::Escape("sha256sums=('$Sha256')")) {
    $failures += "sha256sums is not ('$Sha256')"
}
if ($after -notmatch ("pkgver=" + [regex]::Escape($PkgVer) + "(\r?\n|$)")) {
    $failures += "pkgver is not '$PkgVer'"
}
if ($after -notmatch ("_vertag=" + [regex]::Escape($VerTag) + "(\r?\n|$)")) {
    $failures += "_vertag is not '$VerTag'"
}

if ($failures.Count -gt 0) {
    Write-Error ("VERIFICATION FAILED for ${PkgBuild}: " + ($failures -join '; '))
    exit 1
}

Write-Host "PKGBUILD patched and verified: pkgver=$PkgVer, _vertag=$VerTag, sha256=$Sha256"
exit 0
