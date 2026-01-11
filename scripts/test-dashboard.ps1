# Test script to verify frontend-backend integration
Write-Host "Testing Hospital Dashboard API..." -ForegroundColor Cyan

# Step 1: Login and get token
Write-Host "`n1. Logging in as admin..." -ForegroundColor Yellow
$loginBody = @{
    email = "admin@hospital.com"
    password = "admin123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginBody
    
    $token = $loginResponse.access_token
    Write-Host "Success: Login successful!" -ForegroundColor Green
} catch {
    Write-Host "Failed: Login failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Fetch analytics overview
Write-Host "`n2. Fetching analytics overview..." -ForegroundColor Yellow
$headers = @{
    "Authorization" = "Bearer $token"
    "Accept" = "application/json"
}

$uri = "http://localhost:8000/api/v1/analytics/overview?date_from=2026-01-10&date_to=2026-01-10"

try {
    $analytics = Invoke-RestMethod -Uri $uri `
        -Method GET `
        -Headers $headers
    
    Write-Host "Success: Analytics retrieved successfully!" -ForegroundColor Green
    Write-Host "`nKey Metrics:" -ForegroundColor Cyan
    Write-Host "  - Avg Wash Time: $($analytics.average_wash_time_ms)ms"
    Write-Host "  - Quality Rate: $([Math]::Round($analytics.quality_rate, 2))%"
    Write-Host "  - Total Devices: $($analytics.device_summary.total_devices)"
    Write-Host "  - Online Devices: $($analytics.device_summary.online_devices)"
    Write-Host "  - Compliance Trend Items: $($analytics.compliance_trend.Count)"
    
    if ($analytics.most_missed_step) {
        Write-Host "  - Most Missed Step: Step $($analytics.most_missed_step.step_id) - $($analytics.most_missed_step.step_name)"
    }
    
    Write-Host "`nSuccess: All tests passed! Frontend should be able to fetch data." -ForegroundColor Green
    Write-Host "`nFrontend URL: http://localhost:5173" -ForegroundColor Cyan
    
} catch {
    Write-Host "Failed: Analytics fetch failed: $_" -ForegroundColor Red
    exit 1
}
