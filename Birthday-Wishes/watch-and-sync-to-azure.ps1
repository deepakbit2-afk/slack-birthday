[CmdletBinding()]
param(
    [string]$SourceRemote = "origin",
    [string]$TargetRemote = "azure",
    [int]$IntervalSeconds = 60
)

$ErrorActionPreference = "Stop"

function Assert-Remote($Name) {
    git remote get-url $Name *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Git remote '$Name' was not found. Run push-to-azure.ps1 first."
    }
}

$repoRoot = (& git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Run this script from inside a Git repository."
}
Set-Location $repoRoot

Assert-Remote $SourceRemote
Assert-Remote $TargetRemote

Write-Host "Watching '$SourceRemote' and syncing changes to '$TargetRemote' every $IntervalSeconds seconds."
Write-Host "Press Ctrl+C to stop."

while ($true) {
    try {
        git fetch $SourceRemote --prune
        if ($LASTEXITCODE -ne 0) {
            throw "git fetch failed."
        }

        $branches = @(git for-each-ref --format="%(refname:strip=3)" "refs/remotes/$SourceRemote/heads")
        foreach ($branch in $branches) {
            if ($branch -and $branch -ne "HEAD") {
                git push $TargetRemote "refs/remotes/$SourceRemote/$branch`:refs/heads/$branch"
                if ($LASTEXITCODE -ne 0) {
                    throw "Could not push branch '$branch'."
                }
            }
        }

        git push $TargetRemote --tags
        if ($LASTEXITCODE -ne 0) {
            throw "Could not push tags."
        }

        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Sync complete."
    } catch {
        Write-Warning $_.Exception.Message
    }

    Start-Sleep -Seconds $IntervalSeconds
}