$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Assert-Exit([string]$Message) {
    if ($LASTEXITCODE -ne 0) { throw $Message }
}

$tag = '2.0.9-beta'
$fork = 'DanielP-1337/ha-speidel-braumeister'
$forkUrl = "https://github.com/$fork.git"
$branch = git branch --show-current
Assert-Exit 'Cannot read branch.'
if ($branch -notlike 'release/rtc-2.0.9-beta*') {
    throw 'Run this script on the separate release/rtc-2.0.9-beta branch.'
}
$manifest = Get-Content 'custom_components/speidel_braumeister/manifest.json' -Raw | ConvertFrom-Json
if ($manifest.version -ne $tag) { throw 'Unexpected integration version.' }
$changes = git status --porcelain
Assert-Exit 'Cannot read Git status.'
if ($changes) { throw "Working tree is not clean: $changes" }

# Tests use a disposable environment outside the repository.
$testEnv = Join-Path ([System.IO.Path]::GetTempPath()) ('braumeister-rtc-tests-' + [guid]::NewGuid().ToString('N'))
try {
    py -3 -m venv $testEnv
    Assert-Exit 'Cannot create Python test environment.'
    $python = Join-Path $testEnv 'Scripts/python.exe'
    & $python -m pip install -r requirements_test.txt
    Assert-Exit 'Cannot install test dependencies.'
    & $python -m pytest -q
    Assert-Exit 'Python tests failed; nothing published.'
    node dashboard/test.cjs
    Assert-Exit 'Dashboard tests failed; nothing published.'
    git diff --check
    Assert-Exit 'Diff check failed.'
}
finally {
    if (Test-Path -LiteralPath $testEnv) {
        Remove-Item -LiteralPath $testEnv -Recurse -Force
    }
}

# Refuse to overwrite an existing release tag.
$existing = git ls-remote --tags $forkUrl "refs/tags/$tag"
Assert-Exit 'Cannot check remote tag.'
if ($existing) { throw "$tag already exists on GitHub. Nothing overwritten." }
$localTag = git tag --list $tag
Assert-Exit 'Cannot check local tag.'
if ($localTag) { throw "$tag already exists locally. Nothing overwritten." }

git tag -a $tag -m '2.0.9-beta - RTC monitoring hardware test'
Assert-Exit 'Cannot create tag.'
git push --atomic $forkUrl "HEAD:refs/heads/$branch" "refs/tags/$tag"
Assert-Exit 'Push failed; local tag retained for diagnosis.'
gh release create $tag --repo $fork --verify-tag --prerelease --latest=false `
    --title '2.0.9-beta - RTC monitoring hardware test' `
    --notes-file 'RELEASE-NOTES-2.0.9-beta.md'
Assert-Exit 'Branch/tag pushed, but release creation failed. Do not rerun; inspect the error.'
gh release view $tag --repo $fork --json tagName,isPrerelease,url
Assert-Exit 'Cannot read published release.'
