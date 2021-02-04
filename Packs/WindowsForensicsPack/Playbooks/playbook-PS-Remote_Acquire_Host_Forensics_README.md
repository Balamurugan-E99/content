This playbook allows the user to gather multiple forensic data from a windows endpoint. Including network traffic, MFT (Master File Table) or registry export by using the Powershell Remoting integration which enables to connect to a windows host without the need to install any 3rd party tools using just native Windows management tools.

## Dependencies
This playbook uses the following sub-playbooks, integrations, and scripts.

### Sub-playbooks
* PS-Remote Get Network Traffic
* PS-Remote Get Registry
* PS-Remote Get MFT

### Integrations
This playbook does not use any integrations.

### Scripts
* SetAndHandleEmpty

### Commands
This playbook does not use any commands.

## Playbook Inputs
---

| **Name** | **Description** | **Default Value** | **Required** |
| --- | --- | --- | --- |
| GetNetworkTraffic | This input specifies whether to capture network traffic on the host. | true | Optional |
| GetMft | This input specifies whether to acquire the MFT for the host. | true | Optional |
| GetRegistry | This input specifies whether to export the registry on the host. | true | Optional |
| Host | The host name for which to export the registry file. For example testpc01 |  | Optional |

## Playbook Outputs
---

| **Path** | **Description** | **Type** |
| --- | --- | --- |
| PcapDetails | Pcap file details. | string |
| RegistryDetails | Registry file details. | string |
| MftDetails | MFT file details | string |

## Playbook Image
---
![PS-Remote Acquire Host Forensics](Insert the link to your image here)