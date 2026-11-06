param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$imageTag = 'braumeister-local-test:control4-beta1-arm64-20261106'
$resourceId = [guid]::NewGuid().ToString('N').Substring(0,12)
$networkName = "bm-control4-test-$resourceId"
$cloudName = "bm-control4-cloud-$resourceId"
$bridgeName = "bm-control4-bridge-$resourceId"
$blockedName = "bm-control4-blocked-$resourceId"
$started = [System.Collections.Generic.List[string]]::new()
$networkCreated = $false

function Invoke-TestDocker([string[]]$DockerArgs) {
    $result = & docker --context desktop-linux @DockerArgs
    if ($LASTEXITCODE -ne 0) { throw "Docker test command failed: $($DockerArgs[0])" }
    return $result
}

New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$testScripts = New-Item -ItemType Directory -Path (Join-Path $OutputDirectory 'scripts')
$testData = New-Item -ItemType Directory -Path (Join-Path $OutputDirectory 'synthetic-data')
foreach ($file in @('container_mock_cloud.py','container_program_smoke.py')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination $testScripts.FullName
}
@{
    bridge_ip='192.0.2.10'; cloud_host='cloud.invalid'; upstream_dns='192.0.2.1'
    forward_to_cloud=$true; dns_port=0; cloud_dns=@(); http_port=8080
    api_host='127.0.0.1'; api_port=8642; passthrough_url=''; log_level='info'
    cloud_url="http://${cloudName}:18080"; state_file='/data/recipes.json'
    control_enabled=$true; program_control_enabled=$true; allow_remote_heating=$true
    manual_pump_enabled=$false
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $testData.FullName 'options.json') -Encoding utf8NoBOM

try {
    Invoke-TestDocker -DockerArgs @('network','create','--internal',$networkName) | Out-Null
    $networkCreated = $true
    $internalFlag = Invoke-TestDocker -DockerArgs @('network','inspect',$networkName,'--format','{{.Internal}}')
    if ($internalFlag -ne 'true') { throw 'Test network must be internal' }
    "Network internal: $internalFlag" | Set-Content -LiteralPath (Join-Path $OutputDirectory 'isolation.txt')
    Invoke-TestDocker -DockerArgs @('run','-d','--platform','linux/arm64','--network',$networkName,
        '--name',$cloudName,'--mount',"type=bind,source=$($testScripts.FullName),target=/test,readonly",
        $imageTag,'python3','-u','/test/container_mock_cloud.py') | Out-Null
    $started.Add($cloudName)
    Invoke-TestDocker -DockerArgs @('run','-d','--platform','linux/arm64','--network',$networkName,
        '--name',$bridgeName,'--env',"SMOKE_CLOUD=http://${cloudName}:18080",
        '--mount',"type=bind,source=$($testScripts.FullName),target=/test,readonly",
        '--mount',"type=bind,source=$($testData.FullName),target=/data",$imageTag) | Out-Null
    $started.Add($bridgeName)
    $result = Invoke-TestDocker -DockerArgs @('exec',$bridgeName,'python3','/test/container_program_smoke.py')
    $result | Tee-Object -FilePath (Join-Path $OutputDirectory 'smoke-result.txt')
    Invoke-TestDocker -DockerArgs @('exec',$bridgeName,'sha256sum','/app/bridge.py') |
        Set-Content -LiteralPath (Join-Path $OutputDirectory 'container-code-sha256.txt')
    Invoke-TestDocker -DockerArgs @('image','inspect',$imageTag,'--format','{{.Os}}/{{.Architecture}} {{.Id}}') |
        Set-Content -LiteralPath (Join-Path $OutputDirectory 'image.txt')
    $disabledData = New-Item -ItemType Directory -Path (Join-Path $OutputDirectory 'disabled-synthetic-data')
    $disabledOptions = Get-Content -LiteralPath (Join-Path $testData.FullName 'options.json') -Raw | ConvertFrom-Json
    $disabledOptions.PSObject.Properties.Remove('program_control_enabled')
    $disabledOptions | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $disabledData.FullName 'options.json') -Encoding utf8NoBOM
    Invoke-TestDocker -DockerArgs @('run','-d','--platform','linux/arm64','--network',$networkName,
        '--name',$blockedName,'--env',"SMOKE_CLOUD=http://${cloudName}:18080",'--env','SMOKE_RESUME_DISABLED=1',
        '--mount',"type=bind,source=$($testScripts.FullName),target=/test,readonly",
        '--mount',"type=bind,source=$($disabledData.FullName),target=/data",$imageTag) | Out-Null
    $started.Add($blockedName)
    Invoke-TestDocker -DockerArgs @('exec',$blockedName,'python3','/test/container_program_smoke.py') |
        Tee-Object -FilePath (Join-Path $OutputDirectory 'smoke-disabled-result.txt')
} finally {
    foreach ($containerName in $started) {
        & docker --context desktop-linux logs $containerName 2>&1 |
            Set-Content -LiteralPath (Join-Path $OutputDirectory "$containerName.log")
        # Exact, uniquely generated test names only; no foreign resources or prune.
        & docker --context desktop-linux rm -f $containerName | Out-Null
    }
    if ($networkCreated) { & docker --context desktop-linux network rm $networkName | Out-Null }
}
