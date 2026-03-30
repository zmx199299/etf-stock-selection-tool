import sys
import logging
from engine.server import JSONRPCServer, fetch_legal_tax_rates, get_fund_list, get_dashboard_signals, get_screening_results, get_scoring_data, get_scheduler_data

# Basic logging to stderr so it doesn't mess up JSON-RPC on stdout
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ping():
    return "pong"

def get_engine_status():
    return {"status": "running", "version": "1.0.0"}

def main():
    logger.info("Starting Python ETF Engine...")
    server = JSONRPCServer()
    
    # Register core methods
    server.register_method("ping", ping)
    server.register_method("get_engine_status", get_engine_status)
    server.register_method("fetch_legal_tax_rates", fetch_legal_tax_rates)
    server.register_method("get_fund_list", get_fund_list)
    server.register_method("get_dashboard_signals", get_dashboard_signals)
    server.register_method("get_screening_results", get_screening_results)
    server.register_method("get_scoring_data", get_scoring_data)
    server.register_method("get_scheduler_data", get_scheduler_data)
    
    # Block and run on stdio
    logger.info("Engine listening on stdin...")
    server.run_stdio()

if __name__ == "__main__":
    main()
