# Worth-It Behavior Guidelines

## 1. Regression Resistance & Fault Tolerance
A failure in one component must never bring down the rest of the application.
Specifically, a platform failure (e.g. Blinkit endpoint timeout or structure change) must NOT cause:
- Zepto or Instamart scans to stop.
- The SSE stream to die (it must yield an error event and continue).
- History writes to fail globally.
- The background scheduler to stop.
- The frontend scan state to become permanently stuck in an invalid state.

The UI must distinguish between "0 deals found" and "Platform Error".

## 2. Target Semantics
- **KEYWORD / CATEGORY Targets**: Represent continuous discovery. The system must map these to live search operations and dynamically evaluate ALL matching products. A keyword target must NEVER silently convert into a single fixed product ID.
- **LINK Targets**: Represent direct product tracking. The system extracts the product identifier from the URL and checks ONLY that exact item across stores.

## 3. Discount Handling
- Target categories and keywords have an optional "minimum discount percentage".
- The frontend explicitly sets and submits this minimum discount.
- The backend evaluates this threshold strictly. If the threshold is 30%, a 20% discount does not qualify.
- The visual state of the discount threshold must clearly indicate whether it is active, and the frontend state must not lag or fall out of sync with the true configuration.
