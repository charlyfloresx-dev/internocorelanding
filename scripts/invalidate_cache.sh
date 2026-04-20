#!/bin/bash
# Script para invalidar el cache de CloudFront (InternoCore Frontend)
DISTRIBUTION_ID="E23YTJF59L1IKO"

echo ">> Invalidando cache de CloudFront (ID: $DISTRIBUTION_ID)..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*" \
    --query "Invalidation.Id" \
    --output text)

echo ">> Invalidadion creada: $INVALIDATION_ID"
echo ">> Los cambios serán visibles en unos minutos."
