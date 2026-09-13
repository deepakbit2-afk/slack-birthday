[CmdletBinding()]
param(
    [string]$Organization = "https://dev.azure.com/Deepaksingh0643",
    [string]$Project = "Pipelines",
    [string]$Repository = "Pipelines",
    [switch]$CreateProject
)

$ErrorActionPreference = "Stop"

function Assert-Command($Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required. Install Azure CLI and the azure-devops extension first."
    }
}

Assert-Command "az"
Assert-Command "git"

$repoRoot = (& git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Run this script from inside a Git repository."
}
Set-Location $repoRoot

$Organization = $Organization.TrimEnd("/")
az extension add --name azure-devops --only-show-errors | Out-Null
az devops configure --defaults organization=$Organization project=$Project

if ($CreateProject) {
    $existingProject = az devops project show --project $Project --organization $Organization --only-show-errors 2>$null
    if (-not $existingProject) {
        Write-Host "Creating Azure DevOps project '$Project'..."
        az devops project create --name $Project --organization $Organization --source-control git --visibility private
    }
}

$existingRepo = az repos show --repository $Repository --project $Project --organization $Organization --only-show-errors 2>$null
if (-not $existingRepo) {
    Write-Host "Creating Azure Repos repository '$Repository'..."
    az repos create --name $Repository --project $Project --organization $Organization --only-show-errors | Out-Null
}

$azureRemote = "$Organization/$Project/_git/$Repository"
$remotes = @(git remote)
if ($remotes -contains "azure") {
    git remote set-url azure $azureRemote
} else {
    git remote add azure $azureRemote
}

git add -A
if (git diff --cached --quiet) {
    Write-Host "No uncommitted changes to commit."
} else {
    $message = "Sync project to Azure DevOps"
    git commit -m $message
}

$branch = (& git branch --show-current).Trim()
if (-not $branch) {
    throw "The current Git branch could not be determined."
}

Write-Host "Pushing '$branch' to $azureRemote ..."
git push --set-upstream azure $branch
if ($LASTEXITCODE -ne 0) {
    throw "Azure push failed. Resolve the remote history conflict and run the script again."
}
Write-Host "Azure DevOps repository is ready: $azureRemote"