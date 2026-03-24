# getOrphanVMDK.ps1
# Purpose : List all orphaned vmdk on all datastores in all VC's
# Version : v2.0
# Author  : J. Greg Mackinnon, from original by HJA van Bokhoven
# Change  : v1.1  2009.02.14  DE  angepasst an ESX 3.5, Email versenden und Filegrösse ausgeben
# Change  : v1.2  2011.07.12 EN  Updated for ESX 4, collapsed if loops into single conditional
# Change  : v2.0  2011.07.22 EN:
    # Changed vmdk search to use the VMware.Vim.VmDiskFileQuery object to improve search accuracy
    # Change vmdk matching logic as a result of VmDiskFileQuery usage
    # Pushed discovered orphans into an array of custom PS objects
    # Simplified logging and email output
             
Set-PSDebug -Strict
 
#Initialize the VIToolkit:
add-pssnapin VMware.VimAutomation.Core
# [Reflection.Assembly]::LoadWithPartialName("VMware.Vim") # Commented out based on https://community.broadcom.com/vmware-cloud-foundation/discussion/zombie-vmdk-issues
 
#Main
 
[string]$strVC = "myViServer.mydomain.org"                              # Virtual Center Server name
[string]$logfile = "c:\local\temp\getOrphanVMDK.log"
[string]$SMTPServer = "mysmtp.mydomain.org"                         # Change to a SMTP server in your environment
[string]$mailfrom = "GetOrphanVMDK@myViServer.mydomain.org" # Change to email address you want emails to be coming from
[string]$mailto = "vmware@mydomain.org"                         # Change to email address you would like to receive emails
[string]$mailreplyto = "vmware@mydomain.org"                        # Change to email address you would like to reply emails
 
[int]$countOrphaned = 0
[int64]$orphanSize = 0
 
# vmWare Datastore Browser query parameters
# See http://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.host.DatastoreBrowser.SearchSpec.html
$fileQueryFlags = New-Object VMware.Vim.FileQueryFlags
$fileQueryFlags.FileSize = $true
$fileQueryFlags.FileType = $true
$fileQueryFlags.Modification = $true
$searchSpec = New-Object VMware.Vim.HostDatastoreBrowserSearchSpec
$searchSpec.details = $fileQueryFlags
#The .query property is used to scope the query to only active vmdk files (excluding snaps and change block tracking).
$searchSpec.Query = (New-Object VMware.Vim.VmDiskFileQuery)
#$searchSpec.matchPattern = "*.vmdk" # Alternative VMDK match method.
$searchSpec.sortFoldersFirst = $true
 
if ([System.IO.File]::Exists($logfile)) {
    Remove-Item $logfile
}
 
#Time stamp the log file
(Get-Date –f "yyyy-MM-dd HH:mm:ss") + "  Searching Orphaned VMDKs..." | Tee-Object -Variable logdata
$logdata | Out-File -FilePath $logfile -Append
#Connect to vCenter Server
Connect-VIServer $strVC
 
#Collect array of all VMDK hard disk files in use:
[array]$UsedDisks = Get-View -ViewType VirtualMachine | % {$_.Layout} | % {$_.Disk} | % {$_.DiskFile}
#The following three lines were used before adding the $searchSpec.query property.  We now want to exclude template and snapshot disks from the in-use-disks array.
# [array]$UsedDisks = Get-VM | Get-HardDisk | %{$_.filename}
# $UsedDisks += Get-VM | Get-Snapshot | Get-HardDisk | %{$_.filename}
# $UsedDisks += Get-Template | Get-HardDisk | %{$_.filename}
 
#Collect array of all Datastores:
#$arrDS is a list of datastores, filtered to exclude ESX local datastores (all of which end with "-local1" in our environment), and our ISO storage datastore.
[array]$allDS = Get-Datastore | select -property name,Id | ? {$_.name -notmatch "-local1"} | ? {$_.name -notmatch "-iso$"} | Sort-Object -Property Name
 
[array]$orphans = @()
Foreach ($ds in $allDS) {
    "Searching datastore: " + [string]$ds.Name | Tee-Object -Variable logdata
    $logdata | Out-File -FilePath $logfile -Append
    $dsView = Get-View $ds.Id
    $dsBrowser = Get-View $dsView.browser
    $rootPath = "["+$dsView.summary.Name+"]"
    $searchResult = $dsBrowser.SearchDatastoreSubFolders($rootPath, $searchSpec)
    foreach ($folder in $searchResult) {
        foreach ($fileResult in $folder.File) {
            if ($UsedDisks -notcontains ($folder.FolderPath + $fileResult.Path) -and ($fileResult.Path.length -gt 0)) {
                $countOrphaned++
                IF ($countOrphaned -eq 1) {
                    ("Orphaned VMDKs Found: ") | Tee-Object -Variable logdata
                    $logdata | Out-File -FilePath $logfile -Append
                }
                $orphan = New-Object System.Object
                $orphan | Add-Member -type NoteProperty -name Name -value ($folder.FolderPath + $fileResult.Path)
                $orphan | Add-Member -type NoteProperty -name SizeInGB -value ([Math]::Round($fileResult.FileSize/1gb,2))
                $orphan | Add-Member -type NoteProperty -name LastModified -value ([string]$fileResult.Modification.year + "-" + [string]$fileResult.Modification.month + "-" + [string]$fileResult.Modification.day)
                $orphans += $orphan
                $orphanSize += $fileResult.FileSize
                $orphan | ft -autosize | out-string | Tee-Object -Variable logdata
                $logdata | Out-File -FilePath $logfile -Append
                [string]("Total Size or orphaned files: " + ([Math]::Round($orphanSize/1gb,2)) + " GB") | Tee-Object -Variable logdata
                $logdata | Out-File -FilePath $logfile -Append
                Remove-Variable orphan
            }
        }
    }
}
(Get-Date –f "yyyy-MM-dd HH:mm:ss") + "  Finished (" + $countOrphaned + " Orphaned VMDKs Found.)" | Tee-Object -Variable logdata
$logdata | Out-File -FilePath $logfile -Append
 
if ($countOrphaned -gt 0) {
    [string]$body = "Orphaned VMDKs Found: `n"
    $body += $orphans | Sort-Object -Property LastModified| ft -AutoSize | out-string
    $body += [string]("Total Size or orphaned files: " + ([Math]::Round($orphanSize/1gb,2)) + "GB")
    $SmtpClient = New-Object system.net.mail.smtpClient
    $SmtpClient.host = $SMTPServer
    $MailMessage = New-Object system.net.mail.mailmessage
    $MailMessage.from = $mailfrom
    $MailMessage.To.add($mailto)
    $MailMessage.replyto = $mailreplyto
    $MailMessage.IsBodyHtml = 0
    $MailMessage.Subject = "Info: VMware orphaned VMDKs"
    $MailMessage.Body = $body
    "Mailing report... " | Tee-Object -Variable logdata
    $logdata | Out-File -FilePath $logfile -Append
    $SmtpClient.Send($MailMessage)
}
Disconnect-VIServer -Confirm:$False