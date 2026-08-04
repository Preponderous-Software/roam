<#
.SYNOPSIS
    Windows installation wizard for Roam.

.DESCRIPTION
    Guides a Windows user through installing and launching Roam without using
    the command line by hand. This is the Windows analogue of run.sh:
      - verifies Python and pip are available (with guidance if they are not),
      - installs pygame and the rest of requirements.txt,
      - creates Desktop and Start Menu shortcuts that launch the game,
      - optionally launches the game when finished.

.USAGE
    Right-click install.ps1 and choose "Run with PowerShell", or from a
    PowerShell prompt in the repository root:
        powershell -ExecutionPolicy Bypass -File .\install.ps1

.PARAMETER NonInteractive
    Suppress all "Press Enter" prompts and do not launch the game. Implies
    -NoLaunch. Intended for automated/CI runs that cannot answer prompts.

.PARAMETER NoLaunch
    Complete the install (dependencies, icon, shortcuts) but skip the
    "play now?" prompt and do not launch the game.

.PARAMETER Uninstall
    Undo what this wizard created: the Desktop/Start Menu shortcuts and the
    generated icon.ico. Does not touch the cloned repository, the Python
    installation, or (by default) your saves/settings under %APPDATA%\Roam.
    Combine with -RemoveData to also delete that user data, or with
    -NonInteractive to skip the confirmation prompt (user data is kept
    unless -RemoveData is also given).

.PARAMETER RemoveData
    Only meaningful with -Uninstall. Also deletes %APPDATA%\Roam (saves,
    config.yml, screenshots).
#>

param(
    [switch]$NonInteractive,
    [switch]$NoLaunch,
    [switch]$Uninstall,
    [switch]$RemoveData
)

# Run from the directory this script lives in so relative paths resolve.
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Pause-IfInteractive {
    # Keep the window open so the user can read the message, unless running
    # non-interactively (e.g. in CI), where there is no one to press Enter.
    if (-not $NonInteractive) {
        Read-Host "Press Enter to exit"
    }
}

function Resolve-Python {
    # Prefer the "python" command; fall back to the "py" launcher shipped with
    # the python.org installer. Returns the command name, or $null if absent.
    foreach ($candidate in @("python", "py")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            return $candidate
        }
    }
    return $null
}

function Print-Version {
    if (Test-Path (Join-Path $RepoRoot "version.txt")) {
        $version = (Get-Content (Join-Path $RepoRoot "version.txt") -Raw).Trim()
        Write-Host "Installing Roam version: $version"
    }
}

function Install-Dependencies {
    param([string]$Python)

    Write-Step "Checking dependencies"

    # Ensure pip is available; bootstrap it if the interpreter ships without it.
    & $Python -m pip --version *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "pip was not found; attempting to bootstrap it with ensurepip..."
        & $Python -m ensurepip --upgrade
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Could not bootstrap pip. Install it from https://pip.pypa.io/en/stable/installation/" -ForegroundColor Red
            return $false
        }
    }

    # Show pip's normal output (no --quiet): the downloads can take a minute, so
    # the progress reassures the user it isn't frozen, and on failure pip's real
    # error is visible instead of being swallowed.
    Write-Host "Installing pygame (this can take a minute)..."
    & $Python -m pip install pygame --pre
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install pygame. See the pip output above for the cause." -ForegroundColor Red
        return $false
    }

    Write-Host "Installing remaining dependencies from requirements.txt..."
    & $Python -m pip install -r (Join-Path $RepoRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies. See the pip output above for the cause." -ForegroundColor Red
        return $false
    }

    Write-Host "Dependencies installed." -ForegroundColor Green
    return $true
}

function Get-IconPath {
    param([string]$Python)

    # Windows shortcuts need a .ico file. Convert the bundled PNG icon to .ico
    # using Pillow (a project dependency, installed in the previous step). If the
    # conversion fails for any reason, the shortcut simply falls back to the
    # launcher's default icon.
    $pngPath = Join-Path $RepoRoot "src\media\icon.PNG"
    $icoPath = Join-Path $RepoRoot "src\media\icon.ico"

    if (-not (Test-Path $pngPath)) {
        return $null
    }
    if (Test-Path $icoPath) {
        return $icoPath
    }

    $script = "from PIL import Image; " +
              "Image.open(r'$pngPath').save(r'$icoPath', sizes=[(16,16),(32,32),(48,48),(256,256)])"
    & $Python -c $script *> $null
    if ($LASTEXITCODE -eq 0 -and (Test-Path $icoPath)) {
        return $icoPath
    }
    return $null
}

function Resolve-WindowlessPython {
    param([string]$Python)

    # The shortcut target needs the windowless counterpart of the resolved
    # interpreter (pythonw.exe next to python.exe, or pyw.exe next to the py
    # launcher) so the game doesn't trail a console window for the whole
    # session. Both ship alongside their console counterpart on a standard
    # python.org install.
    $command = Get-Command $Python -ErrorAction SilentlyContinue
    if (-not $command) {
        return $null
    }
    $windowlessName = if ($Python -eq "py") { "pyw.exe" } else { "pythonw.exe" }
    $windowlessPath = Join-Path (Split-Path -Parent $command.Source) $windowlessName
    if (Test-Path $windowlessPath) {
        return $windowlessPath
    }
    return $null
}

function New-RoamShortcut {
    param(
        [string]$ShortcutPath,
        [string]$TargetPath,
        [string]$Arguments,
        [string]$IconPath
    )

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = $RepoRoot
    $shortcut.Description = "Launch Roam"
    if ($IconPath) {
        $shortcut.IconLocation = $IconPath
    }
    $shortcut.Save()
}

function Create-Shortcuts {
    param(
        [string]$IconPath,
        [string]$Python
    )

    Write-Step "Creating shortcuts"

    $windowlessPython = Resolve-WindowlessPython -Python $Python
    if ($windowlessPython) {
        $target = $windowlessPython
        $arguments = '"' + (Join-Path $RepoRoot "src\roam.py") + '"'
    } else {
        # No windowless interpreter available; fall back to run.bat so the
        # shortcut still works, at the cost of a trailing console window.
        Write-Host "No windowless Python interpreter (pythonw.exe/pyw.exe) found; shortcuts will use run.bat and show a console window." -ForegroundColor Yellow
        $launcher = Join-Path $RepoRoot "run.bat"
        if (-not (Test-Path $launcher)) {
            Write-Host "Launcher run.bat was not found; skipping shortcut creation." -ForegroundColor Yellow
            return
        }
        $target = $launcher
        $arguments = ""
    }

    $desktop = [Environment]::GetFolderPath("Desktop")
    $startMenu = [Environment]::GetFolderPath("Programs")

    New-RoamShortcut -ShortcutPath (Join-Path $desktop "Roam.lnk") -TargetPath $target -Arguments $arguments -IconPath $IconPath
    Write-Host "Created Desktop shortcut."

    New-RoamShortcut -ShortcutPath (Join-Path $startMenu "Roam.lnk") -TargetPath $target -Arguments $arguments -IconPath $IconPath
    Write-Host "Created Start Menu shortcut."
}

function Remove-RoamShortcuts {
    # Symmetric with Create-Shortcuts: removes exactly the two shortcuts that
    # function creates, if present.
    $removed = @()

    $desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Roam.lnk"
    if (Test-Path $desktopShortcut) {
        Remove-Item $desktopShortcut -Force
        $removed += "Desktop shortcut ($desktopShortcut)"
    }

    $startMenuShortcut = Join-Path ([Environment]::GetFolderPath("Programs")) "Roam.lnk"
    if (Test-Path $startMenuShortcut) {
        Remove-Item $startMenuShortcut -Force
        $removed += "Start Menu shortcut ($startMenuShortcut)"
    }

    return $removed
}

function Remove-GeneratedIcon {
    # Symmetric with Get-IconPath: removes the icon.ico that wizard generated
    # from icon.PNG, if present. icon.PNG itself is a repo asset, not
    # generated, so it is left alone.
    $icoPath = Join-Path $RepoRoot "src\media\icon.ico"
    if (Test-Path $icoPath) {
        Remove-Item $icoPath -Force
        return $icoPath
    }
    return $null
}

function Invoke-Uninstall {
    Write-Step "Roam Windows uninstall wizard"

    $removed = @()
    $removed += Remove-RoamShortcuts

    $icon = Remove-GeneratedIcon
    if ($icon) {
        $removed += "Generated icon ($icon)"
    }

    $dataDir = Join-Path $env:APPDATA "Roam"
    $deleteData = $RemoveData
    if ((-not $deleteData) -and (-not $NonInteractive) -and (Test-Path $dataDir)) {
        $answer = Read-Host "Also delete your saves, settings, and screenshots at $dataDir ? (y/N)"
        if ($answer -match '^(y|yes)$') {
            $deleteData = $true
        }
    }

    if (Test-Path $dataDir) {
        if ($deleteData) {
            Remove-Item $dataDir -Recurse -Force
            $removed += "User data ($dataDir)"
        } else {
            Write-Host "Keeping user data at $dataDir (pass -RemoveData to delete it)."
        }
    }

    Write-Step "Uninstall summary"
    if ($removed.Count -eq 0) {
        Write-Host "Nothing to remove; install.ps1's shortcuts and icon were not found."
    } else {
        foreach ($item in $removed) {
            Write-Host "Removed: $item" -ForegroundColor Green
        }
    }
    Write-Host ""
    Write-Host "The cloned repository and your Python installation were left untouched."
}

# --- main -------------------------------------------------------------------

if ($Uninstall) {
    Invoke-Uninstall
    Pause-IfInteractive
    exit 0
}

Write-Step "Roam Windows installation wizard"
Print-Version

$python = Resolve-Python
if (-not $python) {
    Write-Host "Python could not be found." -ForegroundColor Red
    Write-Host "Install it from https://www.python.org/downloads/ and be sure to check"
    Write-Host "'Add python.exe to PATH' in the installer, then run this wizard again."
    try { Start-Process "https://www.python.org/downloads/" } catch {}
    Pause-IfInteractive
    exit 1
}

if (-not (Install-Dependencies -Python $python)) {
    Pause-IfInteractive
    exit 1
}

$iconPath = Get-IconPath -Python $python
Create-Shortcuts -IconPath $iconPath -Python $python

Write-Step "Installation complete"
Write-Host "Roam is installed. Launch it from the Desktop or Start Menu shortcut," -ForegroundColor Green
Write-Host "or by double-clicking run.bat in this folder." -ForegroundColor Green
Write-Host ""
Write-Host "The shortcuts point to this folder ($RepoRoot), so keep it where it is —"
Write-Host "moving or deleting it will break them (re-run install.ps1 if you do move it)."
$dataDir = Join-Path $env:APPDATA "Roam"
Write-Host "Your saves, settings, and screenshots are stored in: $dataDir"

if ($NonInteractive -or $NoLaunch) {
    Write-Host "Skipping launch (run was non-interactive or -NoLaunch was set)."
} else {
    $answer = Read-Host "Would you like to play Roam now? (y/N)"
    if ($answer -match '^(y|yes)$') {
        & $python (Join-Path $RepoRoot "src\roam.py")
    }
}
