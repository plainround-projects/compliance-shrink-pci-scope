# Payment provider attestation of compliance

| Field | Value |
| --- | --- |
| Provider | The local stand-in used by this repository (`pci-scope serve provider`) |
| Attestation of compliance | NOT OBTAINED: the stand-in is not a PCI service provider and has none |
| Date of the attestation | - |
| Services covered | - |
| Integration type | Hosted fields (an iframe the provider serves), the merchant's server holds tokens only |
| Obtained by, on | - |

## To close the gap (requirement P7, ticket PCI-1)

With a real provider: download its current attestation of compliance for service providers from its compliance or trust page, record its date, the services it covers and the version of the integration you use, and replace "NOT OBTAINED" above. The rules that apply to the merchant depend on the integration type, so write that down too.
