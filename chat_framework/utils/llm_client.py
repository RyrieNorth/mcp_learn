import os
import time
import json
from typing import Optional, Union, Generator, List, Dict
from openai import OpenAI, OpenAIError
from utils.env_utils import get_env_var
from utils.logger import logger
from utils.debug import is_debug_mode
from utils.tools_loader import get_openai_tool_specs, call_tool_by_name

def get_openai_client() -> OpenAI:
    """
    Initialize and return an OpenAI client instance.

    This function reads the API credentials from environment variables
    (`API_KEY` and `API_BASE`) and uses them to construct a client.

    Returns:
        OpenAI: A configured OpenAI client instance.

    Raises:
        EnvironmentError: If either `API_KEY` or `API_BASE` is missing in the environment.
    """
    api_key = get_env_var(key="API_KEY")
    api_base = get_env_var(key="API_BASE")
    
    if is_debug_mode():
        logger.debug("api_key_suffix: ****%s", api_key[-4:])
        logger.debug("api_base: %s", api_base)

    logger.info("Initializing OpenAI client...")
    return OpenAI(api_key=api_key, base_url=api_base)


def handle_tool_calls(client, messages, assistant_message, model, extra_body):
    """
    Handle tool call requests from the assistant, invoke the corresponding tools, 
    and send the results back to the model for further response.

    Args:
        client: OpenAI or compatible API client.
        messages (list): Chat message history.
        assistant_message: Response from the model containing tool calls.
        model (str): Model name to use for completion.
        extra_body (dict): Additional parameters for the API call.

    Returns:
        str | Generator: Final assistant message or generator yielding streamed content.
    """
    # Extract tool calls from assistant message
    tool_calls = getattr(assistant_message, "tool_calls", None)
        
    if tool_calls is None and isinstance(assistant_message, dict):
        tool_calls = assistant_message.get("tool_calls", [])
        
        if is_debug_mode():
            logger.debug("tool_calls: %s", tool_calls)

    for tool_call in tool_calls:
        # Support both object-style and dict-style tool call formats
        if isinstance(tool_call, dict):
            function = tool_call.get("function", {})
            tool_call_id = tool_call.get("id")
            name = function.get("name")
            arguments_raw = function.get("arguments") or "{}"
            
            if is_debug_mode():
                logger.debug("function: %s", function)
                logger.debug("tool_call_id: %s", tool_call_id)
                logger.debug("name: %s", name)
                logger.debug("arguments_raw: %s", arguments_raw)

        # Parse tool arguments from JSON
        try:
            if isinstance(arguments_raw, str):
                arguments = json.loads(arguments_raw)
                
                if is_debug_mode():
                    logger.debug("arguments: %s", arguments)
                
            elif isinstance(arguments_raw, dict):
                arguments = arguments_raw
    
                if is_debug_mode():
                    logger.debug("arguments: %s", arguments)
            else:
                raise ValueError("Unsupported tool_call argument type")
        except Exception as e:
            logger.error(f"Failed to parse arguments for tool '{name}': {e}")
            continue
        
        # Call the tool by name and store the result
        tool_result = call_tool_by_name(name, arguments)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(tool_result)
        })

    # Request the assistant's final or next message
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        extra_body=extra_body
    )
    # Yield streamed content token by token
    full_content = ""
    for chunk in response:
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                full_content += content
                yield content
    messages.append({"role": "assistant", "content": full_content})


def call_llm(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.6,
    thinking: bool = False,
    max_tokens: int = 8192,
    messages: Optional[List[Dict[str, str]]] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    timeout: float = 15.0,
) -> Union[str, Generator[str, None, None]]:
    """
    Generate a response from a language model (LLM) given a user prompt.

    Sends the prompt to the specified LLM model using the OpenAI client,
    supporting temperature control, and an optional enhanced reasoning mode ("thinking").

    Implements retry logic on failures and supports a timeout per request.

    Args:
        prompt (str): User input prompt to be sent to the model.
        model (str, optional): Model ID to use; if None, reads from the environment variable `MODEL`.
        temperature (float): Controls randomness in generation (0.0 to 1.0). Higher values yield more random results.
        thinking (bool): Enables model "thinking" mode if supported by backend.
        max_retries (int): Maximum number of retry attempts on API failure. Defaults to 3.
        retry_delay (float): Seconds to wait before retrying after failure. Defaults to 2.0 seconds.
        timeout (float): Timeout in seconds for each API call. Defaults to 15.0 seconds.

    Returns:
        Union[str, Generator[str, None, None]]: The complete response string if not streaming;
        or a generator yielding incremental strings if streaming is enabled.

    Raises:
        EnvironmentError: If required environment variables are missing.
        OpenAIError: If API calls repeatedly fail after retries.
    """
    # Get llm model name.
    if model is None:
        model = get_env_var("MODEL")

    if is_debug_mode():
        logger.debug("call_llm_model: %s", model)
        logger.debug("call_llm_thinking: %s", thinking)

    # Thinking extra body.
    extra_body = {
        "chat_template_kwargs": {"enable_thinking": thinking},
    }
    
    client = get_openai_client()

    # Initialize messages list.
    if messages is None:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a Kubernetes assistant."
                    "You have many tools to help you manage Kubernetes resources."
                    "Please return json schema, not return other things."
                    "Not use markdown output."
                    "Not use english answer."
                    "Every response with: Ciallo～(∠・ω<)⌒★"
                )
            },
        ]
    messages.append({"role": "user", "content": prompt})

    tools = get_openai_tool_specs()
    
    if is_debug_mode():  
        logger.debug("tool_lists: %s", tools)
    
    # Start chat
    attempt = 0
    while attempt < max_retries:
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                stream=True,
                max_tokens=max_tokens,
                messages=messages,
                extra_body=extra_body,
                tools=tools,
                tool_choice="auto",
                timeout=timeout
            )
            
            
            def stream_generator():
                logger.info("Streaming chat responses...")
                
                full_content = ""
                tool_calls: Dict[str, dict] = {}
                current_tool_call_id = None  # Activate tool_call
                
                for chunk in response:
                    if hasattr(chunk, "choices") and chunk.choices:
                        delta = chunk.choices[0].delta     
                                           
                        # Check tool_calls
                        if hasattr(delta, "tool_calls") and delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                tc_id = tool_call.id
                                if tc_id:
                                    current_tool_call_id = tc_id
                                    if tc_id not in tool_calls:
                                        tool_calls[tc_id] = {
                                            "id": tc_id,
                                            "type": tool_call.type,
                                            "function": {
                                                "name": None,
                                                "arguments": "",
                                            },
                                        }

                                    if tool_call.function.name:
                                        tool_calls[tc_id]["function"]["name"] = tool_call.function.name
                                    if tool_call.function.arguments:
                                        tool_calls[tc_id]["function"]["arguments"] += tool_call.function.arguments

                                else:
                                    if current_tool_call_id:
                                        if tool_call.function.arguments:
                                            tool_calls[current_tool_call_id]["function"]["arguments"] += tool_call.function.arguments


                        # Handle normal message content
                        content = getattr(delta, "content", None)
                        if content:
                            full_content += content
                            yield content
                messages.append({"role": "assistant", "content": full_content})
                    
                if tool_calls:
                    logger.info("Tool call detected, handling via handle_tool_calls()")
                    # Convert to list
                    tool_calls_list = list(tool_calls.values())
                    for piece in handle_tool_calls(client, messages, {"tool_calls": tool_calls_list}, model, extra_body):
                        yield piece
                else:
                    print()
                    logger.info("No tool call, completed stream.")      
            return stream_generator()

        except OpenAIError as e:
            logger.error(f"OpenAI API error on attempt {attempt + 1}/{max_retries}: {e}")
            attempt += 1
            if attempt >= max_retries:
                logger.error("Max retries exceeded, raising exception.")
                raise
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
