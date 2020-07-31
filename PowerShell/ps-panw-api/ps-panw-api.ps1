param (
    [String] $Hostname="",
    [String] $Command="",
    [String] $Batch="",
    [String] $OutFile="",
    [Boolean] $DisplayAll=$true,
    [Boolean] $PauseBetweenFW=$true
)

# Ask whether or not to pause between outputs in batch mode
function Set-BatchPause() {
    do {
        $PauseBetweenBatches = Read-Host "Pause between firewall outputs (Y/N): "
        $PauseBetweenBatches = $PauseBetweenBatches.toUpper()
    } until ($PauseBetweenBatches -eq "Y" -or $PauseBetweenBatches -eq "N")
    
    if ($PauseBetweenBatches -eq "Y") {
        $Global:Var_Pause_Between_FW = $true
    }
    else {
        $Global:Var_Pause_Between_FW -eq $false
    }
}

# Display all show entries or paginate per 10 lines?
function Set-DisplayAll() {
    do {
        $display_all = read-host "(P)aginate or Display (A)ll results (p/a): "
        $display_all = $display_all.toupper()
    } until ($display_all -eq "A" -or $display_all -eq "P")

    if ($display_all -eq "P") {
        $Global:Var_Display_All = $false
    }
    else {
        $Global:Var_Display_All = $true
    }
}

# Pause function
function Invoke-Pause() {
    Write-Host 'Press any key to continue...';
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown');
}

function Get-SplitCommand($var_Command) {
    $split_command = ""
    # Split the command string into individual tags
    foreach($item in $var_Command.Split(" ")) {
        $split_command += "<" + $item + ">"
    }
    
    # Reverse the order of the command string to terminate the individual command tags
    $reverse_command = @($var_Command.split(" "))
    [array]::reverse($reverse_command)
    foreach($item in $reverse_command) {
        $split_command += "</" + $item + ">"
    }
    return $split_command
}

function Show-XMLResponse($response) {
    # Invalid command
    if ($XML_Response -like "*error*") {
        write-host "Invalid command entered"
    }

    # Character Data XML response (Shell output)
    elseif ($XML_Response -like "*CDATA*") {
        write-host $XML_Response.Content
    }

    # Standard XML response
    else {
        # Convert raw Invoke-WebRequest response to XML for parsing by Get-XMLTree
        $XML_Response = [XML]$XML_Response
        Get-XMLTree $XML_Response
    }
    
    # Is this a batch operation? If not, then pause after output
    if ($Global:Var_Pause_Between_FW) {
        Invoke-Pause
    }
}

function Invoke-CLICommand($var_Command, $fw_list) {

    # Command to execute not passed via CLI
    if ($var_Command -eq "") {
        $var_Command = Read-Host "Enter CLI command to execute: "
        Set-DisplayAll
    }
    if ("log" -in $var_Command) {
        $action = "log"
    }
    else {
        $action = "op"
    }
    
    if ($var_Batch -ne ""){
        foreach ($item in $fw_list) {

            # Get FW specific API key
            $api_key = Get-APIKey $XML_Credential $item

            # Generate FW_URL for $item
            $fw_url = "https://$item/api/?type=$action&cmd=$(Get-SplitCommand($var_Command))&key=$api_key"
            
            Write-Host "--- Executing command: '$var_command' on firewall at https://$item ---"

            if ($OS -eq "linux") {
                $XML_Response = Invoke-WebRequest -SkipCertificateCheck -Uri $fw_url
            }
            elseif ($OS -eq "windows") {
                $XML_Response = Invoke-WebRequest -Uri $fw_url
            }
            Show-XMLResponse $XML_Response
        }
    }
    elseif ($var_Batch -eq "") {

        Write-Host "--- Executing command: '$var_command' on firewall at https://$var_hostname ---"

        # Generate $fw_url
        $fw_url = "https://$var_hostname/api/?type=$action&cmd=$(Get-SplitCommand($var_Command))&key=$api_key"

        if ($OS -eq "linux") {
            $XML_Response = Invoke-WebRequest -SkipCertificateCheck -Uri $fw_url
        }
        elseif ($OS -eq "windows") {
            $XML_Response = Invoke-WebRequest -Uri $fw_url
        }
        Show-XMLResponse $XML_Response
    }
}

# Thanks to "Frodo P" for the post that led me to the final function below
# Source URL: https://stackoverflow.com/questions/37197197/iterate-through-xml-tree-with-unknown-structure-and-size-for-xml-to-registry
function Get-XMLTree($xml) {
    
    $nodesWithText = $xml.SelectNodes("//*[text()]")
    $count = 0
    foreach($node in $nodesWithText)
    {    
        #Start with end of path (element-name of the node with text-value)
        $path = $node.LocalName

        #Get parentnode
        $parentnode = $node.ParentNode

        #Loop until document-node (parent of root-node)
        while($parentnode.LocalName -ne '#document')
        {
            #If sibling with same LocalName (element-name) exists
            if(@($parentnode.ParentNode.ChildNodes | Where-Object { $_.LocalName -eq $parentnode.LocalName }).Count -gt 1)
            {
                #Add text-value to path
                if($parentnode.'#text')
                {
                    $path = "{0}\$path" -f ($parentnode.'#text').Trim()
                }
            }

            #Add LocalName (element-name) for parent to path
            $path = "$($parentnode.LocalName)\$path"

            #Go to next parent node
            $parentnode = $parentnode.ParentNode
        }

        $count += 1
        
        #Output "path = text-value"
        "$path = $(($node.'#text').Trim())"
        if (($count % 10 -eq 0) -and (-not $var_Display_All)) {
            Invoke-Pause
            $count = 0
        }
    }
}

# Function to generate and return API key
function Get-APIKey($cred, $hostn) {
    write-host "----- Retrieving API key for firewall at https://$hostn... -----"
    $User = $cred.GetNetworkCredential().UserName
    $Pass = $cred.GetNetworkCredential().Password
    $URL = "https://$hostn/api/?type=keygen&user=$User&password=$Pass"
    $User = ""
    $Pass = ""
    if ($OS -eq "linux") {
        [XML]$api_key = Invoke-WebRequest -SkipCertificateCheck -Uri $URL
    }
    elseif ($OS -eq "windows") {
        [XML]$api_key = Invoke-WebRequest -Uri $URL
    }
    
    return $api_key.response.result.key
}

### MAIN ROUTINE ###

# Convert script parameters to global variables

$Global:Var_Display_All = $DisplayAll
$Global:Var_Pause_Between_FW = $PauseBetweenFW
$Global:Var_Command = $Command
$Global:Var_Hostname = $Hostname
$Global:Var_Batch = $Batch

# First things first, let's check the OS version to determine how self-signed certs will be handled

if (Test-Path env:OS) {
    $OS = "windows"

    # Configure Powershell to ignore self-signed certificates
    add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
}
    elseif (Test-Path env:SHELL) {
    $OS = "linux"
}
else {
    $OS = "linux"
}

<# --- DEBUG CODE TO VERIFY CLI ARGUMENTS
write-host "DisplayAll = $var_Display_All"
write-host "PauseBetweenFW = $var_Pause_Between_FW"
write-host "Command = $var_Command"
write-host "Batch = $var_Batch"
#>

if ($var_hostname -eq "" -and $var_Batch -eq ""){
    $var_hostname = Read-host "Enter firewall IP address or FQDN: "
}

# Read XML API Administrator account info
$XML_Credential = Get-Credential -Message "Enter username and password for administrator with XML API permissions: "

# Only call Get-APIKey here if we are not operating in batch mode (single firewall mode)
if ($var_Batch -eq "") {
    try {$api_key = Get-APIKey $XML_Credential $var_hostname }
    catch { 
        "Invalid credential entered..."
        break
    }    
}

#### INCOMPLETE ####
# Parse script arguments
if ($var_Batch -ne "") {
    if (-not (Test-Path $var_Batch)) {
        Write-Host "Batch file not found"
        break
    }
}

# Running in batch mode, so process batch mode specific inputs
if ($var_Batch -ne "") {
    if ($var_Display_All -ne $true -and $var_Display_All -ne $false) {
        Set-DisplayAll
    }
    if ($var_Pause_Between_FW -ne $true -and $var_Pause_Between_FW -ne $false) {
        Set-BatchPause
    }
}

<# Not batch mode with no command argument specified
if ($var_Command -eq "" -and $var_Batch -eq "") {
    Invoke-CLICommand
    break
}#>

# Not batch mode but command argument specified
if ($var_Command -ne "" -and $var_Batch -eq ""){
    Write-Host "--- Single Command Processing Mode ---"
    Invoke-CLICommand $var_Command
}

# Batch mode with no command argument specified
elseif ($var_Command -eq "" -and $var_Batch -ne "") {
    Write-Host "--- Batch Processing Mode ---"
    $fw_list = Get-Content -Path $var_Batch
    Invoke-CLICommand "" $fw_list
    break
}

# Batch mode with command argument specified
elseif ($var_Command -ne "" -and $var_Batch -ne "") {
    Write-Host "--- Batch Processing Mode ---"
    $fw_list = Get-Content -Path $var_Batch
    Invoke-CLICommand $var_Command $fw_list
    break
}

do {
    # Display menu
    write-host "PANW Powershell Firewall Manager"
    write-host "Written by Josh Levine (SE-DOD1 - Army/USSOCOM/SOF)"
    write-host "---------------------------------------------------"
    write-host "Main Menu (Please select category)`n"
    write-host "1. Generate API Key"
    write-host "2. Operational Commands"
    write-host "3. Configuration Commands"
    write-host "4. Reporting Commands"
    write-host "5. 'Show Log' Commands"
    write-host "6. Import/Export Commands"
    write-host "7. Generate Tech-Support File (TSF)"
    write-host "8. Perform Firewall Commit"
    write-host "9. Version Information"
    write-host "10. Execute Manual Command`n"
    write-host "0. Exit Script"
    $selection = Read-Host "Enter your selection: "

    $selection = $selection.Trim()

    switch($selection) {
        "1" {
            write-host "Generating API Key"
            $user_credential = Get-Credential -Message "Enter username and password to get API credential for"
            $key = Get-APIKey $user_credential $var_hostname
            write-host $key
            Invoke-Pause
        }
        "2" {
            write-host "`nImplementation Pending"
            Invoke-Pause
        }
        "3" {
            write-host "`nImplementation Pending"
            Invoke-Pause
        }
        "4" {
            write-host "`nImplementation Pending"
            Invoke-Pause
        }
        "5" {
            write-host "`nImplementation Pending"
            Invoke-Pause
        }
        "6" {
            write-host "`nImplementation Pending"
            Invoke-Pause
        }
        "7" {
            write-host "`nGenerating a TSF file requires superuser permissions"
            $admin_creds = Get-Credential -Message "Please enter details for superuser account: "
            
            write-host "Generating superuser API Key"
            $admin_key = Get-APIKey $admin_creds $var_hostname
            $URL = "https://$var_hostname/api/?type=export&category=tech-support&key=$admin_key"
            
            write-host "Generating TSF - Please stand by"
            
            if ($OS -eq "linux") {
                [XML]$tsf_gen_results = Invoke-WebRequest -Uri $URL -SkipCertificateCheck
            }
            elseif ($OS -eq "windows") {
                [XML]$tsf_gen_results = Invoke-WebRequest -Uri $URL
            }
            
            write-host $tsf_gen_results
            
            Invoke-Pause
            if ($tsf_gen_results.response.status -eq "success") {
                write-host "TSF generated successfully"
                Invoke-Pause
            }
        }
        "8" {
            write-host "`nImplementation Pending"
            Invoke-Pause
        }
        "9" {
            write-host "`nImplementation Pending"
            Invoke-Pause
        }
        "10" {
            Invoke-CLICommand "" "" $var_hostname
        }
    }
} While ($selection -ne 0)