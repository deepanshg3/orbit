import time
import traceback
from contextlib import contextmanager
from langsmith import Client

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
        Fails silently if the API doesn't return metadata (e.g., during a 503 error).
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
    Orbit Universal LLM Tracing - Fully Guarded Fault-Tolerant Version.
    Guarantees that a missing, failed, or NoneType run object never crashes the core pipeline.
    """
    run = None
    state = GeminiTraceState()
    start_time = time.time()

    # 1. Attempt to log the run initiation, catch initialization bugs cleanly
    if ls_client:
        try:
            run = ls_client.create_run(
                name=name,
                run_type="llm",
                inputs=inputs,
                tags=tags or [],
                extra={"metadata": metadata or {}}
            )
        except Exception as e:
            print(f"[TRACKING WARNING] Failed to initialize LangSmith trace: {str(e)}")
            run = None # Explicitly ensure it stays None if the call itself fails

    try:
        # Yield control back to Orbit's engine
        yield state
        
        # 2. Guarded Run Completion Check
        if ls_client and run is not None:
            end_time = time.time()
            if "usage" not in state.outputs:
                state.outputs["usage"] = {
                    "prompt_tokens": state.prompt_tokens,
                    "completion_tokens": state.completion_tokens,
                    "total_tokens": state.total_tokens
                }

            try:
                ls_client.update_run(
                    run.id,
                    outputs=state.outputs,
                    end_time=end_time,
                    extra={
                        "metadata": {
                            **(metadata or {}),
                            "latency_seconds": round(end_time - start_time, 2)
                        }
                    }
                )
            except Exception as e:
                print(f"[TRACKING WARNING] Failed to update active LangSmith trace: {str(e)}")

    except Exception as e:
        # 3. Guarded Run Failure Catch
        if ls_client and run is not None:
            try:
                end_time = time.time()
                error_stack = traceback.format_exc()
                ls_client.update_run(
                    run.id,
                    error=str(e),
                    outputs={"traceback": error_stack},
                    end_time=end_time,
                    extra={
                        "metadata": {
                            **(metadata or {}),
                            "latency_seconds": round(end_time - start_time, 2),
                            "status": "failed"
                        }
                    }
                )
            except Exception:
                pass
        
        # Always bubble up the actual core LLM exception so Orbit can handle retries natively
        raise e