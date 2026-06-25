import sys
from core.utils.logger import get_logger
from core.analytics_engine.storage import Storage
from core.analytics_engine.calculator import ImpactCalculator
from core.strategy_engine.orchestrator import StrategyOrchestrator

# --- NEW IMPORT ---
from core.monitoring.tracing import flush_traces

# Initialize the master logger for the Sunday Pipeline
logger = get_logger("orbit.sunday_strategy")

def main():
    logger.info("==================================================")
    logger.info("🚀 INITIATING ORBIT SUNDAY STRATEGY PIPELINE 🚀")
    logger.info("==================================================")

    try:
        # ---------------------------------------------------------
        # PHASE 1: PRE-FLIGHT DATABASE CLEANUP
        # ---------------------------------------------------------
        logger.info("\n>>> [PHASE 1] Running Pre-Flight Database Cleanup...")
        storage = Storage(logger)
        calculator = ImpactCalculator(logger, storage.client)
        
        # Guarantees no posts from the week are left ungraded due to server crashes
        calculator.sweep_orphaned_posts() 
        logger.info(">>> [PHASE 1] Cleanup complete. Database is perfectly graded.\n")

        # ---------------------------------------------------------
        # PHASE 2: GENERATE THE AI PLAYBOOK
        # ---------------------------------------------------------
        logger.info(">>> [PHASE 2] Initializing Strategy Engine...")
        strategy_engine = StrategyOrchestrator(logger, storage.client)
        
        # Calculates weekly totals, finds Top 5/Bottom 5, calls Gemini, saves the Epoch.
        strategy_engine.execute_weekly_strategy()
        
        logger.info(">>> [PHASE 2] AI Playbook successfully generated and saved.\n")

        logger.info("==================================================")
        logger.info("✅ SUNDAY STRATEGY PIPELINE COMPLETE ✅")
        logger.info("==================================================")

    except Exception as e:
        # Catch any fatal errors so the cron job fails gracefully
        logger.error(f"❌ CRITICAL PIPELINE FAILURE: {str(e)}")
        sys.exit(1)
        
    finally:
        # ---------------------------------------------------------
        # PHASE 3: OBSERVABILITY FLUSH (DO NOT REMOVE)
        # ---------------------------------------------------------
        logger.info("Holding process to flush LangSmith telemetry...")
        flush_traces()
        logger.info("Strategy execution complete. Terminating.")

if __name__ == "__main__":
    main()