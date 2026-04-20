# Script para invalidar el cache de CloudFront (InternoCore Frontend)
$DISTRIBUTION_ID = "E23YTJF59L1IKO"

Write-Host ">> Invalidando cache de CloudFront (ID: $DISTRIBUTION_ID)..." -ForegroundColor Cyan
$INVALIDATION_ID = aws cloudfront create-invalidation `
    --distribution-id "$DISTRIBUTION_ID" `
    --paths "/*" `
    --query "Invalidation.Id" `
    --output text

Write-Host ">> Invalidadion creada: $INVALIDATION_ID" -ForegroundColor Green
Write-Host ">> Los cambios serán visibles en unos minutos." -ForegroundColor Yellow
