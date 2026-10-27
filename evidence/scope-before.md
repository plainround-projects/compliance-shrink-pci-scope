# Before: the card number reaches the merchant's server

```mermaid
flowchart LR
    subgraph cde["In scope"]
        web["Web server (naive.py)"]
        log["Request log"]
        shipping["Log shipping"]
        search["Log search tool"]
        db["Order database"]
        bak["Backups"]
        ci["CI/CD pipeline"]
        admin["Admin accounts"]
        laptops["Developer laptops that read logs"]
    end
    browser["Customer browser (provider)"]
    browser -->|card data| web
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

**9 systems and 3 teams in scope** (developers, operations, support).

| System | Team | Why it is in scope |
| --- | --- | --- |
| Web server (naive.py) | developers | card data reaches it |
| Request log | operations | card data reaches it from Web server (naive.py) |
| Log shipping | operations | card data reaches it from Request log |
| Log search tool | support | card data reaches it from Log shipping |
| Order database | developers | card data reaches it from Web server (naive.py) |
| Backups | operations | card data reaches it from Order database |
| CI/CD pipeline | developers | can change Web server (naive.py) |
| Admin accounts | operations | can change Web server (naive.py) |
| Developer laptops that read logs | developers | card data reaches it from Log search tool |

Out of scope: none.
