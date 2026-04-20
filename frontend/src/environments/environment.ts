// temp_future/src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8010', // Global API Gateway / Entry Point
  authUrl: 'http://localhost:8001/api/v1',
  subscriptionUrl: 'http://localhost:8002/api/v1',
  masterDataUrl: 'http://localhost:8003/api/v1',
  ticketsUrl: 'http://localhost:8004/api/v1',
  productionUrl: 'http://localhost:8005/api/v1',
  inventoryUrl: 'http://localhost:8006/api/v1',
  wmsUrl: 'http://localhost:8007/api/v1',
  currencyUrl: 'http://localhost:8008/api/v1',
  hrUrl: 'http://localhost:8009/api/v1',
  notificationUrl: 'http://localhost:8010/api/v1',
  assetsUrl: 'http://momentos.com',
  services: {
    auth: 'http://localhost:8001/api/v1',
    subscription: 'http://localhost:8002/api/v1',
    masterData: 'http://localhost:8003/api/v1',
    tickets: 'http://localhost:8004/api/v1',
    production: 'http://localhost:8005/api/v1',
    inventory: 'http://localhost:8006/api/v1',
    wms: 'http://localhost:8007/api/v1',
    currency: 'http://localhost:8008/api/v1',
    notification: 'http://localhost:8010/api/v1'
  }
};
