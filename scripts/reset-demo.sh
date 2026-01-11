#!/bin/bash
# Reset demo data script for Hospital Dashboard
# This script tears down and rebuilds the database with fresh demo data

set -e

echo "=========================================="
echo "Hospital Dashboard - Reset Demo Data"
echo "=========================================="
echo ""

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Step 1: Stop and remove all containers and volumes
echo "Step 1: Stopping and removing containers and volumes..."
docker compose -f docker-compose.dashboard.yml down -v
echo "✅ Containers and volumes removed"
echo ""

# Step 2: Start only the database
echo "Step 2: Starting database container..."
docker compose -f docker-compose.dashboard.yml up -d db
echo "Waiting for database to be ready..."

# Wait for database to be healthy
for i in {1..30}; do
  if docker compose -f docker-compose.dashboard.yml exec -T db pg_isready -U dashboard_user > /dev/null 2>&1; then
    echo "✅ Database is ready"
    break
  fi
  
  if [ $i -eq 30 ]; then
    echo "❌ Database failed to start within 30 seconds"
    exit 1
  fi
  
  sleep 1
done

echo ""

# Step 3: Run migrations
echo "Step 3: Running database migrations..."
docker compose -f docker-compose.dashboard.yml run --rm backend python src/scripts/init_db.py
echo "✅ Migrations completed"
echo ""

# Step 4: Seed demo data with deterministic seed
echo "Step 4: Seeding demo data (seed=42)..."
docker compose -f docker-compose.dashboard.yml run --rm backend python src/scripts/seed_demo_data.py --seed 42
echo "✅ Demo data seeded"
echo ""

# Step 5: Refresh materialized views
echo "Step 5: Refreshing materialized views..."
docker compose -f docker-compose.dashboard.yml run --rm backend python src/scripts/refresh_views.py
echo "✅ Materialized views refreshed"
echo ""

# Step 6: Start backend and frontend
echo "Step 6: Starting backend and frontend services..."
docker compose -f docker-compose.dashboard.yml up -d backend frontend
echo "✅ Services started"
echo ""

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

echo ""
echo "=========================================="
echo "Demo Reset Complete!"
echo "=========================================="
echo ""
echo "Dashboard is now available at:"
echo "  Frontend: http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Demo data details:"
echo "  - 5 units (ICU, ER, Surgery, Cardiology, Pediatrics)"
echo "  - 20 devices distributed across units"
echo "  - 7 days of historical data"
echo "  - ~1,120 sessions (20 devices × 8 sessions/day × 7 days)"
echo "  - ~6,720 steps (6 steps per session)"
echo "  - Deterministic seed (42) for reproducible data"
echo ""
echo "To view logs:"
echo "  docker compose -f docker-compose.dashboard.yml logs -f backend"
echo "  docker compose -f docker-compose.dashboard.yml logs -f frontend"
echo ""
echo "To stop services:"
echo "  docker compose -f docker-compose.dashboard.yml down"
echo ""
