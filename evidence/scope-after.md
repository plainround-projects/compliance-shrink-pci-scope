# After: the card number goes from the browser to the provider

```mermaid
flowchart LR
    subgraph cde["In scope"]
        web["Web server (serves the checkout page)"]
        ci["CI/CD pipeline"]
        admin["Admin accounts"]
    end
    browser["Customer browser (provider)"]
    provider["Payment provider (hosted fields) (provider)"]
    log["Request log"]
    shipping["Log shipping"]
    search["Log search tool"]
    db["Order database"]
    bak["Backups"]
    laptops["Developer laptops that read logs"]
    browser -->|card data| provider
    web -->|card data| log
    log -->|card data| shipping
    shipping -->|card data| search
    web -->|card data| db
    db -->|card data| bak
    log -->|card data| bak
    search -->|card data| laptops
    ci -.->|can change| web
    admin -.->|can change| web
    admin -.->|can change| log
    admin -.->|can change| search
    admin -.->|can change| db
    admin -.->|can change| bak
```

**3 systems and 2 teams in scope** (developers, operations).

| System | Team | Why it is in scope |
| --- | --- | --- |
| Web server (serves the checkout page) | developers | serves the page that loads the provider's script |
| CI/CD pipeline | developers | can change Web server (serves the checkout page) |
| Admin accounts | operations | can change Web server (serves the checkout page) |

Out of scope: Request log, Log shipping, Log search tool, Order database, Backups, Developer laptops that read logs.
