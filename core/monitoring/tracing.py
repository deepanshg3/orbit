import time
import traceback
from contextlib import contextmanager
from langsmith import Client
from langsmith.run_trees import RunTree

# Safely initialize client to prevent crashes if environment keys are missing entirely
try:
    ls_client = Client()
except Exception:
    ls_client = None

class GeminiTraceState:
    """
    A mutable state object injected into the context manager.
    Allows Orbit's engines to safely pass outputs and token data back to LangSmith 
    without leaking observability logic into the core business logic.
    """
    def __init__(self):
        self.outputs: dict = {}
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_tokens: int = 0

    def extract_usage(self, response):
        """
        Safely extracts token usage directly from the modern google-genai SDK response object.
        """
        try:
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                self.prompt_tokens = response.usage_metadata.prompt_token_count or 0
                self.completion_tokens = response.usage_metadata.candidates_token_count or 0
                self.total_tokens = response.usage_metadata.total_token_count or 0
        except Exception:
            pass 


@contextmanager
def trace_gemini_call(name: str, inputs: dict, tags: list[str] = None, metadata: dict = None):
    """
    Orbit Universal LLM Tracing - RunTree Architecture.
    Guarantees completion transmission by forcing thread synchronization via `.wait()`.
    """
    state = GeminiTraceState()
    start_time = time.time()
    rt = None

    # 1. Initialize and post the run asynchronously
    if ls_client:
        try:
            rt = RunTree(
                name=name,
                run_type="llm",
                inputs=inputs,
                tags=tags or [],
                extra={"metadata": metadata or {}},
                client=ls_client
            )
            rt.post()
        except Exception as e:
            print(f"[TRACKING WARNING] Failed to initialize RunTree: {str(e)}")
            rt = None

    try:
        # Yield control back to Orbit's engine
        yield state
        
        # 2. Guarded Run Completion Check
        if rt is not None:
            if "usage" not in state.outputs:
                state.outputs["usage"] = {
                    "prompt_tokens": state.prompt_tokens,
                    "completion_tokens": state.completion_tokens,
                    "total_tokens": state.total_tokens
                }

            try:
                # rt.end() natively formats timestamps correctly for the backend
                rt.end(outputs=state.outputs)
                
                # Safely update latency metadata
                rt.extra.setdefault("metadata", {})
                rt.extra["metadata"]["latency_seconds"] = round(time.time() - start_time, 2)
                
                rt.patch() 
                rt.wait() # CRITICAL: Blocks execution until the network POST is confirmed
            except Exception as e:
                print(f"[TRACKING WARNING] Failed to patch RunTree: {str(e)}")

    except Exception as e:
        # 3. Guarded Run Failure Catch
        if rt is not None:
            try:
                rt.extra.setdefault("metadata", {})
                rt.extra["metadata"]["latency_seconds"] = round(time.time() - start_time, 2)
                rt.extra["metadata"]["status"] = "failed"
                
                rt.end(error=str(e), outputs={"traceback": traceback.format_exc()})
                rt.patch()
                rt.wait() # CRITICAL: Ensure error trace isn't killed by a pipeline exit
            except Exception:
                pass
        
        # Bubble up exception to core engine
        raise e

def flush_traces():
    """
    With RunTree.wait(), traces are synchronized intrinsically per-call. 
    Kept for architectural compatibility with main.py.
    """
    print("[TRACKING] Telemetry intrinsically secured via RunTree synchronization.")