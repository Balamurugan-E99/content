This playbook leverages the windows builtin Powershell and WinRM capabilities to connect to a Windows host and then the Netsh tool to create an ETL file which is the equivalent of a Wireshark PCAP file by using PS-Remote integration. After receiving the resultant ETL,  XSOAR will be able to convert the ETL to a PCAP file to be parsed and enriched later on.

## Dependencies
This playbook uses the following sub-playbooks, integrations, and scripts.

### Sub-playbooks
This playbook does not use any sub-playbooks.

### Integrations
This playbook does not use any integrations.

### Scripts
* Etl2Pcap
* AddEvidence
* IsIntegrationAvailable
* UnzipFile
* Sleep
* Set

### Commands
* ps-remote-download-file
* ps-remote-etl-create-stop
* ps-remote-etl-create-start

## Playbook Inputs
---

| **Name** | **Description** | **Default Value** | **Required** |
| --- | --- | --- | --- |
| Host | The host name for which to create the ETL file. For example testpc01 |  | Optional |
| EtlSizeLimit | The maximum file size for the ETL. Once the file has reached this size the capute will stop. For example 10MB. The default size is 10MB | 10 | Optional |
| EtlPath | The path on the hostname on which to create the ETL file. The default path will be c:\\etl.etl<br/>In case you use the AddHostNameToFile input as true the file downloaded to XSOAR will be comprised of the hostname. | c:\etl.etl | Optional |
| EtlFilter | The filter to apply when creating the ETL file. For example IPv4.Address=1.1.1.1 to capture traffic just from the 1.1.1.1 IP address. If no filter is specified all traffic will be recorded. |  | Optional |
| ETlTimeToRecord | The time to record in seconds. | 60 | Optional |
| ZipEtl | Specify true to zip the ETL file before sending it to XSOAR. | true | Optional |
| AddHostNameToFile | Specify true for the downloaded file name to be comprised of the host name or false  to keep the file name as configured in the FilePath argument. | true | Optional |

## Playbook Outputs
---

| **Path** | **Description** | **Type** |
| --- | --- | --- |
| PcapDetails | The PCAP file details. | string |

## Playbook Image
---
![PS-Remote Get Network Traffic](Insert the link to your image here)