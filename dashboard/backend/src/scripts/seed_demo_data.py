#!/usr/bin/env python3
"""
Seed demo data script.

Generates synthetic data for dashboard demonstrations with configurable parameters.
Uses bulk insert optimization for performance.
"""
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session as SessionType

from src.database import engine, SessionLocal
from src.services.demo_data_service import (
    set_seed,
    generate_units,
    generate_devices,
    generate_sessions,
    generate_steps,
    generate_heartbeats,
    validate_generated_data
)


def bulk_insert_sessions(db: SessionType, sessions: list, batch_size: int = 1000) -> None:
    """
    Bulk insert sessions using SQLAlchemy bulk_insert_mappings in batches.
    
    Args:
        db: Database session
        sessions: List of session dictionaries
        batch_size: Number of records per batch (default: 1000)
    """
    from src.models.session import Session as SessionModel
    
    # Convert UUID objects to strings for bulk insert
    sessions_data = []
    for session in sessions:
        session_data = session.copy()
        session_data['id'] = str(session_data['id'])
        session_data['device_id'] = str(session_data['device_id'])
        sessions_data.append(session_data)
    
    # Bulk insert in batches
    for i in range(0, len(sessions_data), batch_size):
        batch = sessions_data[i:i + batch_size]
        db.bulk_insert_mappings(SessionModel, batch)
        db.commit()


def bulk_insert_steps(db: SessionType, steps: list, batch_size: int = 5000) -> None:
    """
    Bulk insert steps using SQLAlchemy bulk_insert_mappings in batches.
    
    Args:
        db: Database session
        steps: List of step dictionaries
        batch_size: Number of records per batch (default: 5000)
    """
    from src.models.step import Step
    
    # Convert UUID objects to strings for bulk insert
    steps_data = []
    for step in steps:
        step_data = step.copy()
        step_data['id'] = str(step_data['id'])
        step_data['session_id'] = str(step_data['session_id'])
        steps_data.append(step_data)
    
    # Bulk insert in batches
    for i in range(0, len(steps_data), batch_size):
        batch = steps_data[i:i + batch_size]
        db.bulk_insert_mappings(Step, batch)
        db.commit()


def bulk_insert_heartbeats(db: SessionType, heartbeats: list, batch_size: int = 1000) -> None:
    """
    Bulk insert heartbeats using SQLAlchemy bulk_insert_mappings in batches.
    
    Args:
        db: Database session
        heartbeats: List of heartbeat dictionaries
        batch_size: Number of records per batch (default: 1000)
    """
    from src.models.heartbeat import Heartbeat
    
    # Convert UUID objects to strings for bulk insert
    heartbeats_data = []
    for heartbeat in heartbeats:
        heartbeat_data = heartbeat.copy()
        heartbeat_data['id'] = str(heartbeat_data['id'])
        heartbeat_data['device_id'] = str(heartbeat_data['device_id'])
        heartbeats_data.append(heartbeat_data)
    
    # Bulk insert in batches
    for i in range(0, len(heartbeats_data), batch_size):
        batch = heartbeats_data[i:i + batch_size]
        db.bulk_insert_mappings(Heartbeat, batch)
        db.commit()


def seed_demo_data(args):
    """
    Main function to seed demo data with configurable parameters.
    
    Args:
        args: Parsed command-line arguments
    """
    print("=" * 80)
    print("Seeding Demo Data for Hospital Dashboard")
    print("=" * 80)
    
    # Display configuration
    print("\nConfiguration:")
    print(f"  Devices: {args.devices}")
    print(f"  Days: {args.days}")
    print(f"  Sessions per day (per device): {args.sessions_per_day}")
    print(f"  Miss rate: {args.miss_rate * 100:.1f}%")
    print(f"  Low quality rate: {args.low_quality_rate * 100:.1f}%")
    print(f"  Offline rate: {args.offline_rate * 100:.1f}%")
    print(f"  Random seed: {args.seed}")
    print()
    
    # Set seed for reproducibility
    set_seed(args.seed)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Calculate start date
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=args.days)
        
        # Step 1: Generate units
        print("Generating units...")
        unit_data = generate_units(db, num_units=8)
        print(f"✅ Created {len(unit_data)} units")
        
        # Step 2: Generate devices
        print(f"\nGenerating {args.devices} devices...")
        device_data = generate_devices(db, unit_data, args.devices)
        print(f"✅ Created {len(device_data)} devices")
        
        # Step 3: Generate sessions
        print(f"\nGenerating sessions for {args.days} days...")
        sessions = generate_sessions(
            db,
            device_data,
            start_date,
            args.days,
            args.sessions_per_day,
            args.miss_rate,
            args.low_quality_rate
        )
        print(f"  Generated {len(sessions)} sessions in memory")
        
        # Step 4: Generate steps (also updates session durations)
        print("Generating steps for sessions...")
        steps = generate_steps(db, sessions, args.miss_rate)
        print(f"  Generated {len(steps)} steps in memory")
        
        # Step 5: Bulk insert sessions
        print("\nBulk inserting sessions...")
        bulk_insert_sessions(db, sessions)
        print(f"✅ Inserted {len(sessions)} sessions")
        
        # Step 6: Bulk insert steps
        print("Bulk inserting steps...")
        bulk_insert_steps(db, steps)
        print(f"✅ Inserted {len(steps)} steps")
        
        # Step 7: Generate and bulk insert heartbeats
        print(f"\nGenerating heartbeats (5-minute intervals)...")
        heartbeats = generate_heartbeats(
            db,
            device_data,
            start_date,
            args.days,
            args.offline_rate
        )
        print(f"  Generated {len(heartbeats)} heartbeats in memory")
        
        print("Bulk inserting heartbeats...")
        bulk_insert_heartbeats(db, heartbeats)
        print(f"✅ Inserted {len(heartbeats)} heartbeats")
        
        # Step 8: Validate data meets requirements
        print("\nValidating generated data...")
        validate_generated_data(len(device_data), len(sessions), args.days)
        print("✅ Data validation passed")
        
        # Summary
        print("\n" + "=" * 80)
        print("Demo Data Generation Summary")
        print("=" * 80)
        print(f"  Units created:      {len(unit_data)}")
        print(f"  Devices created:    {len(device_data)}")
        print(f"  Sessions created:   {len(sessions)}")
        print(f"  Steps created:      {len(steps)}")
        print(f"  Heartbeats created: {len(heartbeats)}")
        print(f"  Date range:         {start_date.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}")
        print()
        
        # Calculate statistics
        compliant_sessions = sum(1 for s in sessions if s['compliant'])
        low_quality_sessions = sum(1 for s in sessions if s['low_quality'])
        compliance_rate = (compliant_sessions / len(sessions)) * 100 if sessions else 0
        
        print("Data Statistics:")
        print(f"  Compliant sessions:    {compliant_sessions} ({compliance_rate:.1f}%)")
        print(f"  Non-compliant sessions: {len(sessions) - compliant_sessions} ({100 - compliance_rate:.1f}%)")
        print(f"  Low quality sessions:   {low_quality_sessions} ({(low_quality_sessions / len(sessions)) * 100:.1f}%)")
        print()
        
        # Session distribution by shift
        morning_sessions = sum(1 for s in sessions if 7 <= s['timestamp'].hour < 15)
        afternoon_sessions = sum(1 for s in sessions if 15 <= s['timestamp'].hour < 23)
        night_sessions = sum(1 for s in sessions if s['timestamp'].hour >= 23 or s['timestamp'].hour < 7)
        
        print("Session Distribution by Shift:")
        print(f"  Morning (7am-3pm):     {morning_sessions} ({morning_sessions / len(sessions) * 100:.1f}%)")
        print(f"  Afternoon (3pm-11pm):  {afternoon_sessions} ({afternoon_sessions / len(sessions) * 100:.1f}%)")
        print(f"  Night (11pm-7am):      {night_sessions} ({night_sessions / len(sessions) * 100:.1f}%)")
        print()
        
        print("✅ Demo data seeding completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during data generation: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


def main():
    """Parse arguments and run seeding."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic demo data for Hospital Dashboard",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--devices",
        type=int,
        default=20,
        help="Number of devices to create"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days of historical data"
    )
    
    parser.add_argument(
        "--sessions-per-day",
        type=int,
        default=8,
        help="Average sessions per device per day"
    )
    
    parser.add_argument(
        "--miss-rate",
        type=float,
        default=0.15,
        help="Probability of missing steps (0.0-1.0)"
    )
    
    parser.add_argument(
        "--low-quality-rate",
        type=float,
        default=0.08,
        help="Probability of low-quality sessions (0.0-1.0)"
    )
    
    parser.add_argument(
        "--offline-rate",
        type=float,
        default=0.08,
        help="Probability of device being offline (0.0-1.0)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.devices < 1:
        print("Error: --devices must be at least 1")
        sys.exit(1)
    
    if args.days < 1:
        print("Error: --days must be at least 1")
        sys.exit(1)
    
    if not (0.0 <= args.miss_rate <= 1.0):
        print("Error: --miss-rate must be between 0.0 and 1.0")
        sys.exit(1)
    
    if not (0.0 <= args.low_quality_rate <= 1.0):
        print("Error: --low-quality-rate must be between 0.0 and 1.0")
        sys.exit(1)
    
    if not (0.0 <= args.offline_rate <= 1.0):
        print("Error: --offline-rate must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Run seeding
    seed_demo_data(args)


if __name__ == "__main__":
    main()
