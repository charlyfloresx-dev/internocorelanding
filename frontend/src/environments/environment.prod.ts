const AUTH_BACKEND_URL = 'https://zdvp36ydhj.us-east-2.awsapprunner.com';
const NOTIFICATION_BACKEND_URL = 'https://zi2vwrmucp.us-east-2.awsapprunner.com';
const MASTER_DATA_URL = 'https://qrhbfj8hb4.us-east-2.awsapprunner.com';

const API_V1 = `${AUTH_BACKEND_URL}/api/v1`;
const NOTIFICATION_API_V1 = `${NOTIFICATION_BACKEND_URL}/api/v1`;
const MASTER_DATA_API_V1 = `${MASTER_DATA_URL}/api/v1`;

export const environment = {
  production: true,
  // Propiedades planas (usadas directamente por los servicios Angular)
  apiUrl:        AUTH_BACKEND_URL,
  authUrl:       API_V1,
  assetsUrl:     AUTH_BACKEND_URL,
  masterDataUrl: MASTER_DATA_API_V1,
  inventoryUrl:  API_V1,
  currencyUrl:   API_V1,
  productionUrl: API_V1,
  hrUrl:         API_V1,
  wmsUrl:        API_V1,
  ticketsUrl:    API_V1,
  subscriptionUrl: API_V1,
  notificationUrl: NOTIFICATION_API_V1,
  // Map de servicios (compatibilidad con environment.services.auth etc)
  services: {
    auth:         API_V1,
    subscription: API_V1,
    masterData:   MASTER_DATA_API_V1,
    tickets:      API_V1,
    production:   API_V1,
    inventory:    API_V1,
    wms:          API_V1,
    currency:     API_V1,
    notification: NOTIFICATION_API_V1
  }
};
