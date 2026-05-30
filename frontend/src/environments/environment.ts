// Dev: empty BASE_URL → Angular proxy routes /api/* → localhost:8000
// This makes the app work both locally and via VS Code dev tunnels (port 4200 only).
// Production URLs live in environment.prod.ts.
const BASE_URL = '';
const API_V1 = `/api/v1`;

export const environment = {
  production: false,
  apiUrl:        BASE_URL,
  authUrl:       API_V1,
  assetsUrl:     BASE_URL,
  masterDataUrl: API_V1,
  inventoryUrl:  API_V1,
  currencyUrl:   API_V1,
  productionUrl: API_V1,
  hrUrl:         API_V1,
  wmsUrl:        API_V1,
  ticketsUrl:    API_V1,
  subscriptionUrl: API_V1,
  notificationUrl: API_V1,
  services: {
    auth:         API_V1,
    subscription: API_V1,
    masterData:   API_V1,
    tickets:      API_V1,
    production:   API_V1,
    inventory:    API_V1,
    wms:          API_V1,
    currency:     API_V1,
    notification: API_V1
  }
};
