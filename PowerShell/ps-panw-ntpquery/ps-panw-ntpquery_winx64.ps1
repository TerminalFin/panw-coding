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

write-host "Palo Alto NTP status tool"
write-host "Written by Josh Levine - Systems Engineer (Army/USSOCOM)"
write-host "--------------------------------------------------------"
write-host "|       Input/Output folder is current directory       |"
write-host "--------------------------------------------------------"
write-host "INPUT FILE: fw_list.txt"
write-host "OUTPUT FILE: fw_ntp_status.txt"

# Read XML API Administrator account info
$Credential = Get-Credential -Message "Enter username and password for administrator with XML API permissions: "

# Initialize the array of results
$fw_ntp_status = @()

# Read the firewall list from .\fw_list.txt
write-host "`n`nReading FW_LIST.TXT"
$fw_list = Get-Content -path .\FW_LIST.TXT

# Clear output file before write
set-content -path ".\fw_ntp_status.txt" -Value "Firewall IP,NTP Status"

foreach ($fw in $fw_list) {
    write-host "Processing Firewall at $fw"

    # Generate plaintext credentials for XML API request
    $User = $Credential.GetNetworkCredential().UserName
    $Pass = $Credential.GetNetworkCredential().Password
    
    # Set up URL for API key retrieval for current firewall
    $URL = "https://$fw/api/?type=keygen&user=$User&password=$Pass"
    
    # Extract API key to $key
    write-host "Generating API key for firewall at $fw"
    [XML]$api_key = Invoke-WebRequest -Uri $URL
    $key = $api_key.response.result.key

    # Clear variables
    $User = ""
    $Pass = ""

    # Set up URL for NTP status retrieval
    $URL = "https://$fw/api/?type=op&cmd=<show><ntp></ntp></show>&key=$key"
    write-host "Checking NTP status for firewall at $fw"

    # Query firewall for NTP status
    [XML]$result = Invoke-WebRequest -Uri $URL
    
    # Extract synchronization status from $result
    $ntp_status = $result.response.result.synched

    # Add firewall IP and NTP status to multi-dimensional array
    $output = "$fw, $ntp_status"    
    Add-Content -Path ".\fw_ntp_status.txt" -Value $output

    # $fw_ntp_status += ,(@($fw, $ntp_status))
}

write-host "File output completed to fw_ntp_status.txt"
