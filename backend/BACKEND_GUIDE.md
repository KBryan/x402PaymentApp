# Database Setup Guide

## Three Options for Database Setup

### Option 1: SQLite (Quickest - For Local Testing) 

**No installation needed!** SQLite creates a file-based database automatically.

```bash
cd backend

# Just set the environment variable
export DATABASE_URL="sqlite:///./skale_payments.db"

# Start the API - database will be created automatically
python main.py
```

**Pros:**
-  Zero setup required
-  Perfect for development/testing
-  No separate service to run
-  Database is just a file

**Cons:**
-  Not for production
-  Limited concurrency
-  No network access

---

### Option 2: PostgreSQL via Docker (Recommended) 

**Best balance of easy setup and production-like environment.**

```bash
# 1. Start PostgreSQL in Docker
docker run -d \
  --name skale-postgres \
  -e POSTGRES_DB=skale_payments \
  -e POSTGRES_USER=skale_user \
  -e POSTGRES_PASSWORD=skale_pass_2024 \
  -p 5432:5432 \
  postgres:15-alpine

# 2. Set environment variable
export DATABASE_URL="postgresql://skale_user:skale_pass_2024@localhost:5432/skale_payments"

# 3. Start API
cd backend
python main.py
```

**Database will be created automatically!**

**Useful Commands:**
```bash
# Stop database
docker stop skale-postgres

# Start database
docker start skale-postgres

# View logs
docker logs skale-postgres

# Remove database (careful!)
docker rm -f skale-postgres

# Connect to database
docker exec -it skale-postgres psql -U skale_user -d skale_payments
```

**Pros:**
-  Production-like environment
-  Easy to set up and tear down
-  Can handle concurrent connections
-  Full PostgreSQL features

**Cons:**
-  Requires Docker installed
-  Uses more resources than SQLite

---

### Option 3: PostgreSQL Native (Production) 

**For production or if you already have PostgreSQL installed.**

#### Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from [postgresql.org](https://www.postgresql.org/download/windows/)

#### Create Database

```bash
# Create database user
sudo -u postgres createuser skale_user

# Create database
sudo -u postgres createdb skale_payments

# Set password
sudo -u postgres psql -c "ALTER USER skale_user WITH PASSWORD 'skale_pass_2024';"

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE skale_payments TO skale_user;"
```

#### Set Environment Variable

```bash
export DATABASE_URL="postgresql://skale_user:skale_pass_2024@localhost:5432/skale_payments"
```

---

## Quick Start (Choose Your Option)

### For Immediate Testing (Option 1 - SQLite)

```bash
cd backend

# Create .env file
cat > .env << 'EOF'
DATABASE_URL=sqlite:///./skale_payments.db
SKALE_RPC_URL=http://127.0.0.1:8545
CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
CHAIN_ID=31337
EOF

# Start API (creates database automatically)
source venv/bin/activate
python main.py
```
 **That's it! Database created automatically.**

### For Docker Setup (Option 2 - Recommended)

```bash
# 1. Start PostgreSQL
docker run -d \
  --name skale-postgres \
  -e POSTGRES_DB=skale_payments \
  -e POSTGRES_USER=skale_user \
  -e POSTGRES_PASSWORD=skale_pass_2024 \
  -p 5432:5432 \
  postgres:15-alpine

# 2. Wait 5 seconds for startup
sleep 5

# 3. Create .env file
cd backend
cat > .env << 'EOF'
DATABASE_URL=postgresql://skale_user:skale_pass_2024@localhost:5432/skale_payments
SKALE_RPC_URL=http://127.0.0.1:8545
CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
CHAIN_ID=31337
EOF

# 4. Start API (creates tables automatically)
source venv/bin/activate
python main.py
```

 **Database ready!**

---

## Database Schema (Auto-Created)

When you start the API, these tables are created automatically:

```sql
-- Plans table
CREATE TABLE plans (
    plan_id VARCHAR PRIMARY KEY,
    contract_plan_id VARCHAR UNIQUE NOT NULL,
    token VARCHAR NOT NULL,
    amount BIGINT NOT NULL,
    interval_seconds INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
    grace_period_seconds INTEGER NOT NULL,
    encrypted_api_url VARCHAR NOT NULL,
    description VARCHAR,
    creator VARCHAR NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table
CREATE TABLE subscriptions (
    subscription_id VARCHAR PRIMARY KEY,
    plan_id VARCHAR NOT NULL,
    subscriber_address VARCHAR NOT NULL,
    contract_subscription_data VARCHAR,
    start_time TIMESTAMP NOT NULL,
    next_payment_due TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    total_paid BIGINT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    auto_renew BOOLEAN DEFAULT FALSE,
    transaction_hash VARCHAR
);

-- Payments table
CREATE TABLE payments (
    payment_id VARCHAR PRIMARY KEY,
    subscription_id VARCHAR NOT NULL,
    amount BIGINT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transaction_hash VARCHAR UNIQUE,
    payment_type VARCHAR,
    block_number INTEGER
);

-- Nonces table (for replay protection)
CREATE TABLE nonces (
    id INTEGER PRIMARY KEY,
    address VARCHAR NOT NULL,
    nonce VARCHAR NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(address, nonce)
);
```

**No manual setup needed - SQLAlchemy creates these automatically!**

---

## Verify Database Setup

### Check Tables Were Created

**SQLite:**
```bash
sqlite3 skale_payments.db ".tables"
# Should show: nonces  payments  plans  subscriptions
```

**PostgreSQL (Docker):**
```bash
docker exec -it skale-postgres psql -U skale_user -d skale_payments -c "\dt"
```

**PostgreSQL (Native):**
```bash
psql -U skale_user -d skale_payments -c "\dt"
```

### Check API Can Connect

```bash
# Start API
python main.py

# In another terminal, test
curl http://localhost:8000/health

# Should show:
# {
#   "status": "healthy",
#   "timestamp": "...",
#   "blockchain_connected": true/false
# }
```

### Check Database Stats

```bash
curl http://localhost:8000/admin/stats

# Should show:
# {
#   "total_plans": 0,
#   "active_plans": 0,
#   "total_subscriptions": 0,
#   "active_subscriptions": 0,
#   "blockchain_connected": false
# }
```

---

## Database Management

### View Data

**SQLite:**
```bash
sqlite3 skale_payments.db

# Inside sqlite3:
SELECT * FROM plans;
SELECT * FROM subscriptions;
SELECT * FROM payments;
.quit
```

**PostgreSQL:**
```bash
docker exec -it skale-postgres psql -U skale_user -d skale_payments

# Inside psql:
SELECT * FROM plans;
SELECT * FROM subscriptions;
SELECT * FROM payments;
\q
```

### Clear All Data

**SQLite:**
```bash
rm skale_payments.db
# Restart API to recreate
```

**PostgreSQL:**
```bash
docker exec -it skale-postgres psql -U skale_user -d skale_payments << 'EOF'
TRUNCATE TABLE payments CASCADE;
TRUNCATE TABLE subscriptions CASCADE;
TRUNCATE TABLE plans CASCADE;
TRUNCATE TABLE nonces CASCADE;
EOF
```

### Backup Database

**SQLite:**
```bash
cp skale_payments.db skale_payments_backup_$(date +%Y%m%d).db
```

**PostgreSQL:**
```bash
# Backup
docker exec skale-postgres pg_dump -U skale_user skale_payments > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i skale-postgres psql -U skale_user skale_payments < backup_20250316.sql
```

---

## Troubleshooting

### "Cannot connect to database"

**SQLite:**
- Check file permissions
- Make sure directory exists
- Try absolute path: `sqlite:////full/path/to/skale_payments.db`

**PostgreSQL:**
- Check Docker is running: `docker ps`
- Check port 5432 is not in use: `lsof -i :5432`
- Try connecting manually: `psql -U skale_user -d skale_payments -h localhost`

### "Tables not created"

```python
# Force table creation
python << 'EOF'
from backend.main import Base, engine

Base.metadata.create_all(engine)
print(" Tables created")
EOF
```

### "Permission denied"

**PostgreSQL:**
```bash
# Grant all permissions
docker exec -it skale-postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE skale_payments TO skale_user;"
docker exec -it skale-postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO skale_user;"
```

### Docker container won't start

```bash
# Check logs
docker logs skale-postgres

# Remove and recreate
docker rm -f skale-postgres
docker run -d --name skale-postgres \
  -e POSTGRES_DB=skale_payments \
  -e POSTGRES_USER=skale_user \
  -e POSTGRES_PASSWORD=skale_pass_2024 \
  -p 5432:5432 \
  postgres:15-alpine
```

---

## Complete Setup Script

Save this as `setup_database.sh`:

```bash
#!/bin/bash

echo "🗄️  Setting up SKALE Payment Tool Database"
echo ""

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "✓ Docker found - Using PostgreSQL in Docker"
    
    # Check if container exists
    if docker ps -a | grep -q skale-postgres; then
        echo "Container exists. Starting..."
        docker start skale-postgres
    else
        echo "Creating PostgreSQL container..."
        docker run -d \
          --name skale-postgres \
          -e POSTGRES_DB=skale_payments \
          -e POSTGRES_USER=skale_user \
          -e POSTGRES_PASSWORD=skale_pass_2024 \
          -p 5432:5432 \
          postgres:15-alpine
    fi
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
    
    # Create .env file
    cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://skale_user:skale_pass_2024@localhost:5432/skale_payments
SKALE_RPC_URL=http://127.0.0.1:8545
CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
CHAIN_ID=31337
EOF
    
    echo " PostgreSQL database ready!"
    echo "Connection: postgresql://skale_user:skale_pass_2024@localhost:5432/skale_payments"
else
    echo "Docker not found - Using SQLite"
    
    # Create .env file for SQLite
    cat > backend/.env << 'EOF'
DATABASE_URL=sqlite:///./skale_payments.db
SKALE_RPC_URL=http://127.0.0.1:8545
CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
CHAIN_ID=31337
EOF
    
    echo " SQLite database will be created automatically!"
    echo "Location: backend/skale_payments.db"
fi

echo ""
echo "Next steps:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python main.py"
```

Run it:
```bash
chmod +x setup_database.sh
./setup_database.sh
```

---

##  Comparison

| Feature | SQLite | PostgreSQL (Docker) | PostgreSQL (Native) |
|---------|--------|---------------------|---------------------|
| **Setup Time** | 0 seconds | 1 minute | 5-10 minutes |
| **Installation** | None | Docker only | PostgreSQL install |
| **Best For** | Testing | Development | Production |
| **Concurrent Users** | Limited | Good | Excellent |
| **Performance** | Fast (small data) | Fast | Fastest |
| **Backup** | Copy file | pg_dump | pg_dump |
| **Production Ready** | ❌ | ⚠️ (with volumes) | ✅ |

---

##  Recommendation

**For your current testing:** Use **Option 2 (Docker)** if you have Docker, or **Option 1 (SQLite)** if you don't.

**For production:** Use **Option 3 (PostgreSQL Native)** or managed database (AWS RDS, DigitalOcean, etc.)

---

##  Quick Start Command

**Just want to get started NOW?**

```bash
# Use SQLite (zero setup)
cd backend
export DATABASE_URL="sqlite:///./skale_payments.db"
python main.py

# Done! Database created automatically.
```

---

**Your database is ready!** 

Choose your option and run the commands. The API will create all tables automatically when it starts.