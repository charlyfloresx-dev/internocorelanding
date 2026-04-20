const BACKEND_URL = 'https://jtq5mfp8pj.us-east-2.awsapprunner.com';
const API_V1 = `${BACKEND_URL}/api/v1`;

export const environment = {
  production: true,
  // Propiedades planas (usadas directamente por los servicios Angular)
  apiUrl:        BACKEND_URL,
  authUrl:       API_V1,
  assetsUrl:     BACKEND_URL,
  masterDataUrl: API_V1,
  inventoryUrl:  API_V1,
  currencyUrl:   API_V1,
  productionUrl: API_V1,
  hrUrl:         API_V1,
  wmsUrl:        API_V1,
  ticketsUrl:    API_V1,
  subscriptionUrl: API_V1,
  // Map de servicios (compatibilidad con environment.services.auth etc)
  services: {
    auth:         API_V1,
    subscription: API_V1,
    masterData:   API_V1,
    tickets:      API_V1,
    production:   API_V1,
    inventory:    API_V1,
    wms:          API_V1,
    currency:     API_V1
  }
};
