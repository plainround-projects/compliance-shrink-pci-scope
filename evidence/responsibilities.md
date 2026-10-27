# Who is responsible for what after the redesign

Written for the "Assemble the evidence" step: the card data now flows between the browser and the provider, and the merchant still has duties.

## Now the provider's

- Receiving, processing, transmitting and storing the card number, expiry and CVV, in its own environment.
- The card form and the script that creates it (the hosted fields), including their security and availability.
- Network tokens and provider tokens: creating them, protecting the mapping to the card, and honoring a refund or a repeat charge from a token.
- Its own attestation of compliance, renewed each year, and its list of covered services.

## Still ours

- The payment page: the web server that serves the page which loads the provider's script, and every person and system that can change it (the CI/CD pipeline, the admin accounts). An attacker who changes that page can send the card to themselves.
- The content security policy of that page, and an inventory of the scripts and frames it loads, reviewed when it changes.
- Not logging request bodies, and not adding a card field to any form, log line or database column; the scan and the capture are repeated for each release.
- The provider contract, the provider's current attestation of compliance, and a record of which of its services we use.
- The questionnaire for our merchant level, answered for the reduced scope above, and the list of who has access to the payment page and its pipeline.
- Handling a token like a sensitive value even though it is not card data: stored encrypted at rest, kept out of logs, available only to the services that charge or refund.
