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

function Get-APIKey($cred, $hostname) {
    $User = $cred.GetNetworkCredential().UserName
    $Pass = $cred.GetNetworkCredential().Password
    $URL = "https://$hostname/api/?type=keygen&user=$User&password=$Pass"
    $User = ""
    $Pass = ""
    [XML]$api_key = Invoke-WebRequest  -Uri $URL
    return $api_key.response.result.key
}

$firewalls = @()

$file = read-host "Enter filename (line-delimited): "

$firewalls = get-content $file

$app = read-host "Enter application name as shown in the Application library: "
$app = $app.ToLower()
$timeout = read-host "Enter TCP Timeout Value: "
$credential = Get-Credential

foreach ($item in $firewalls) {
    
    write-host "Retrieving API Key for Firewall at https://$item"
    $api_key = Get-APIKey $credential $item

    $url = "https://$item/api/?key=$api_key&type=config&action=set&xpath=/config/shared/override/application/entry[@name='$app']&element=<tcp-timeout>$timeout</tcp-timeout>"
    [XML]$response = Invoke-WebRequest -Uri $url 
    
    if ($response.response.status -eq "success") {
        write-host "Firewall at https://$item configured successfully"
    }
    else {
        write-host "Failed to configure firewall at https://$item"
    }
}

write-host "Script completed. Please commit the firewall changes now"