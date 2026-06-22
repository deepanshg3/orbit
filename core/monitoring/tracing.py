import time
import traceback
from contextlib import contextmanager
from langsmith import Client

# Initialize the LangSmith client once globally to save connection overhead
ls_client = Client()

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
    Orbit Universal LLM Tracing - Expert Level

    Args:
        name: Name of the trace (e.g., 'Trend Ranking', 'Content Generation')
        inputs: Dictionary of what went into the prompt (system, user, context)
        tags: Taxonomy tags for LangSmith filtering (e.g., ['strategy', 'weekly'])
        metadata: Explicit tracking vars (e.g., {'epoch_id': 5, 'content_type': 'thread'})
    """
    
    # 1. Initialize the run in LangSmith
    run = ls_client.create_run(
        name=name,
        run_type="llm",
        inputs=inputs,
        tags=tags or [],
        extra={"metadata": metadata or {}}
    )

    state = GeminiTraceState()
    start_time = time.time()

    try:
        # Yield control back to your Orbit engines (Generator, Community Manager, etc.)
        yield state
        
        # 2. If execution reaches here, the LLM call and JSON parsing were successful
        end_time = time.time()
        
        # LangSmith natively parses a "usage" dict inside outputs for token graphs
        if "usage" not in state.outputs:
            state.outputs["usage"] = {
                "prompt_tokens": state.prompt_tokens,
                "completion_tokens": state.completion_tokens,
                "total_tokens": state.total_tokens
            }

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
        # 3. If Gemini 503s OR your JSON parsing fails, catch it and flag the trace RED
        end_time = time.time()
        error_stack = traceback.format_exc()
        
        ls_client.update_run(
            run.id,
            error=str(e),
            outputs={"traceback": error_stack}, # Puts the raw Python error directly in the LangSmith UI
            end_time=end_time,
            extra={
                "metadata": {
                    **(metadata or {}),
                    "latency_seconds": round(end_time - start_time, 2),
                    "status": "failed"
                }
            }
        )
        
        # Re-raise the exception so your Exponential Backoff logic can still catch it!
        raise