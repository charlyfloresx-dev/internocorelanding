const ALB = 'http://InternoCore-ALB-437730134.us-east-2.elb.amazonaws.com/api/v1';
const ALB_BASE = 'http://InternoCore-ALB-437730134.us-east-2.elb.amazonaws.com';

export const environment = {
  production: true,
  // Propiedades planas (usadas directamente por los servicios Angular)
  apiUrl:        ALB_BASE,
  authUrl:       ALB,
  assetsUrl:     ALB_BASE,
  masterDataUrl: ALB,
  inventoryUrl:  ALB,
  currencyUrl:   ALB,
  productionUrl: ALB,
  hrUrl:         ALB,
  wmsUrl:        ALB,
  ticketsUrl:    ALB,
  subscriptionUrl: ALB,
  // Map de servicios (compatibilidad con environment.services.auth etc)
  services: {
    auth:         ALB,
    subscription: ALB,
    masterData:   ALB,
    tickets:      ALB,
    production:   ALB,
    inventory:    ALB,
    wms:          ALB,
    currency:     ALB
  }
};
