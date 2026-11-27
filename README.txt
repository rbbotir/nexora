NEXORA — YOUR OWN LOCAL STORE (DEMO)
====================================

WHAT THIS VERSION DOES
- Own storefront design
- Product list read from SQLite database
- Search products and add to cart
- Submit a demo order (no payment)
- Admin PIN protects local add-product and view-orders endpoints
- Product and order data persist in nexora.db

RUN ON WINDOWS
1. Install Python 3 from https://www.python.org/downloads/
   During installation, enable "Add Python to PATH".
2. Extract this ZIP into a normal folder.
3. Double-click START_NEXORA.bat.
4. Open http://localhost:8000 in your browser.
5. Admin demo PIN: 2468

IMPORTANT
- This is a LOCAL DEMO, not a public live store.
- Change the default admin PIN before using it beyond your own computer:
  set NEXORA_ADMIN_PIN=your-new-pin
  then start the server from that same terminal.
- Do not collect real customer information in this demo.
- No real payments, shipping integrations, tax handling, HTTPS, production security,
  backups, or public hosting are configured.
- To publish online, we must add production security and hosting first.
- Ask a parent/guardian to handle accounts, contracts and any real payments.
