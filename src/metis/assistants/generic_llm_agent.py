# intelligent_validation_framework/generic_llm_agent.py
"""
Generic LLM Agent for Text Generation
Provides a reusable function to generate text using OpenAI Agents SDK with custom prompts and settings
"""

import json
import logging
import os
import re
import time
from typing import Dict, List, Optional, Type

from agents import Agent, ModelSettings, Runner, set_default_openai_key
from agents.agent_output import AgentOutputSchema  # For non-strict schemas
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GenericLLMAgent:
    """
    Generic LLM agent for text generation with customizable prompts and settings
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the generic LLM agent

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
        """
        # Load environment variables
        load_dotenv()

        # Get API key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        # Set the default OpenAI key for agents framework
        set_default_openai_key(self.api_key)

        # Initialize direct OpenAI client for JSON output (non-structured)
        self.openai_client = OpenAI(api_key=self.api_key)

        logger.info("GenericLLMAgent initialized successfully")

    async def generate_text(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: Optional[float] = 0.7,
        model: str = "gpt-4",
        agent_name: str = "TextGenerator",
    ) -> str:
        """
        Generate text using the OpenAI Agents SDK

        Args:
            user_prompt: The user message/prompt
            system_prompt: The system instructions for the agent
            temperature: Temperature setting for response creativity (0.0-1.0). Set to None for models that don't support it.
            model: Model to use (default: gpt-4)
            agent_name: Name for the agent (for logging/debugging)

        Returns:
            Generated text response as string
        """
        try:
            # Create agent with custom settings
            # Some models (like GPT-5 Nano) don't support temperature
            if temperature is not None:
                agent = Agent(
                    name=agent_name,
                    instructions=system_prompt,
                    model=model,
                    model_settings=ModelSettings(temperature=temperature),
                )
                logger.info(
                    f"Generating text with agent '{agent_name}' using model '{model}' at temperature {temperature}"
                )
            else:
                agent = Agent(
                    name=agent_name,
                    instructions=system_prompt,
                    model=model
                    # No model_settings for models that don't support temperature
                )
                logger.info(
                    f"Generating text with agent '{agent_name}' using model '{model}' (no temperature)"
                )

            # Run the agent
            result = await Runner.run(agent, user_prompt)

            # Extract the response
            response_text = result.final_output

            logger.info(
                f"Text generation completed. Response length: {len(response_text)} characters"
            )
            return response_text

        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    def generate_structured_output(
        self,
        user_prompt: str,
        system_prompt: str,
        response_format: Type[BaseModel],
        model: str = "gpt-5-mini",
        temperature: Optional[float] = 0.7,
        agent_name: str = "StructuredGenerator",
    ) -> BaseModel:
        """
        Generate structured output using Pydantic schema with OpenAI Agents SDK

        Args:
            user_prompt: The user message/prompt
            system_prompt: The system instructions
            response_format: Pydantic model class for structured output
            model: Model to use (default: gpt-5-mini for structured output)
            temperature: Temperature setting for response creativity (0.0-1.0)
            agent_name: Name for the agent (for logging/debugging)

        Returns:
            Parsed response as Pydantic model instance
        """
        try:
            # Create agent with structured output_type
            if temperature is not None:
                agent = Agent(
                    name=agent_name,
                    instructions=system_prompt,
                    model=model,
                    model_settings=ModelSettings(temperature=temperature),
                    output_type=response_format,
                )
            else:
                agent = Agent(
                    name=agent_name,
                    instructions=system_prompt,
                    model=model,
                    output_type=response_format,
                )

            logger.info(
                f"Generating structured output with agent '{agent_name}' using model '{model}'"
            )

            # Run the agent synchronously
            result = Runner.run_sync(agent, user_prompt)

            # The final_output will be the structured object
            structured_response = result.final_output

            logger.info(
                f"Structured output generation completed using Agents SDK. Type: {type(structured_response)}"
            )
            return structured_response

        except Exception as e:
            logger.error(
                f"Error generating structured output with Agents SDK: {str(e)}"
            )
            raise

    async def generate_structured_output(
        self,
        prompt: str,
        response_format: Type[BaseModel],
        model: str = "gpt-5-mini",
        temperature: Optional[float] = 0.7,
        agent_name: str = "StructuredGenerator",
    ) -> BaseModel:
        """
        Generate structured output using Pydantic schema (convenience async method).
        
        This is a simplified interface where the prompt contains both system and user content.
        
        Args:
            prompt: The complete prompt (treated as user message)
            response_format: Pydantic model class for structured output
            model: Model to use (default: gpt-5-mini for structured output)
            temperature: Temperature setting for response creativity (0.0-1.0)
            agent_name: Name for the agent (for logging/debugging)

        Returns:
            Parsed response as Pydantic model instance
        """
        # Default system prompt for competitive intelligence reports
        system_prompt = (
            "You are an expert financial analyst specializing in competitive intelligence. "
            "Generate detailed, data-driven analysis following the exact structure provided. "
            "Ensure all outputs are factual, well-supported, and actionable."
        )
        
        return await self.generate_structured_output_async(
            user_prompt=prompt,
            system_prompt=system_prompt,
            response_format=response_format,
            model=model,
            temperature=temperature,
            agent_name=agent_name,
        )

    async def generate_structured_output_async(
        self,
        user_prompt: str,
        system_prompt: str,
        response_format: Type[BaseModel],
        model: str = "gpt-5-mini",
        temperature: Optional[float] = 0.7,
        agent_name: str = "StructuredGenerator",
    ) -> BaseModel:
        """
        Generate structured output using Pydantic schema with OpenAI Agents SDK (async)

        Args:
            user_prompt: The user message/prompt
            system_prompt: The system instructions
            response_format: Pydantic model class for structured output
            model: Model to use (default: gpt-5-mini for structured output)
            temperature: Temperature setting for response creativity (0.0-1.0)
            agent_name: Name for the agent (for logging/debugging)

        Returns:
            Parsed response as Pydantic model instance
        """
        try:
            # Wrap output type with AgentOutputSchema to disable strict JSON schema
            # This is needed for schemas with Dict[str, Any] or similar flexible types
            output_schema = AgentOutputSchema(response_format, strict_json_schema=False)
            
            # Create agent with structured output_type
            if temperature is not None:
                agent = Agent(
                    name=agent_name,
                    instructions=system_prompt,
                    model=model,
                    model_settings=ModelSettings(temperature=temperature),
                    output_type=output_schema,
                )
            else:
                agent = Agent(
                    name=agent_name,
                    instructions=system_prompt,
                    model=model,
                    output_type=output_schema,
                )

            logger.info(
                f"Generating structured output (async) with agent '{agent_name}' using model '{model}'"
            )

            # Run the agent asynchronously
            result = await Runner.run(agent, user_prompt)

            # The final_output will be the structured object
            structured_response = result.final_output

            logger.info(
                f"Structured output generation completed using Agents SDK. Type: {type(structured_response)}"
            )
            return structured_response

        except Exception as e:
            logger.error(
                f"Error generating structured output (async) with Agents SDK: {str(e)}"
            )
            raise

    def generate_json_output(
        self,
        user_prompt: str,
        system_prompt: str,
        model: str = "gpt-5-mini",
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> List[Dict]:
        """
        Generate JSON output with retry logic for workflow extraction

        Args:
            user_prompt: The user message/prompt
            system_prompt: The system instructions
            model: Model to use (default: gpt-5-mini)
            max_retries: Maximum retry attempts
            base_delay: Base delay for exponential backoff

        Returns:
            Parsed JSON as list of dictionaries
        """
        # Retry logic with exponential backoff
        for attempt in range(1, max_retries + 1):
            t0 = time.perf_counter()
            try:
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                )

                dt = time.perf_counter() - t0
                text = response.choices[0].message.content.strip()

                logger.debug(
                    f"JSON generation completed ({dt:.2f}s), chars_out={len(text)}"
                )

                # Parse JSON from response
                if text.startswith("```"):
                    text = re.sub(r"^```(\w+)?\n", "", text).strip()
                    text = re.sub(r"```$", "", text).strip()

                first = text.find("[")
                last = text.rfind("]")
                payload = text[first : last + 1] if first >= 0 else "[]"
                data = json.loads(payload)

                if isinstance(data, dict):
                    data = [data]
                return data if isinstance(data, list) else []

            except Exception as e:
                dt = time.perf_counter() - t0
                if attempt <= max_retries:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"JSON generation failed (try {attempt}/{max_retries}, {dt:.2f}s): {str(e)} - retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    continue
                logger.error(
                    f"JSON generation failed after {attempt - 1} attempts ({dt:.2f}s): {str(e)}"
                )
                return []

    def generate_mermaid_diagram(
        self,
        workflow_data: List[Dict],
        model: str = "gpt-5-mini",
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> str:
        """
        Generate intelligent Mermaid diagram from workflow data with LLM optimization
        
        Args:
            workflow_data: List of workflow dictionaries from JSON
            model: Model to use (default: gpt-5-mini)
            max_retries: Maximum retry attempts
            base_delay: Base delay for exponential backoff
        
        Returns:
            Optimized Mermaid diagram syntax as string
        """
        workflow_count = len(workflow_data) if isinstance(workflow_data, list) else 1
        
        system_prompt = """You are a workflow visualization expert specializing in creating optimized Mermaid flowchart diagrams.

Your task is to analyze workflows and create intelligent, readable Mermaid diagrams that:
1. Group related processes into logical business functions (8-15 subgraphs max)
2. Create meaningful decision points with Yes/No branching where business logic diverges
3. Keep total diagram edges under 400 to ensure renderability
4. Use proper Mermaid syntax with subgraphs, decision diamonds, and clear flow

Mermaid syntax rules:
- Use "graph TD" for top-down flowcharts
- Subgraphs: subgraph ID["Title"]
- Decision diamonds: ID{"Question?"}
- Process boxes: ID["Process step"]
- Start/End nodes: ID(["Text"])
- Outputs: ID[["Output text"]]
- Connections: ID1 --> ID2
- Conditional paths: ID -->|Yes| ID2

Focus on business value and readability over technical completeness."""
        
        user_prompt = f"""Analyze these {workflow_count} workflows and generate an optimized Mermaid flowchart:

Requirements:
- Group related workflows into logical business functions
- Create decision points where processes branch
- Keep total edges under 400 for renderability  
- Use clear, business-friendly labels
- Include triggers, key steps, and outcomes

Workflow Data:
{json.dumps(workflow_data, indent=2)}

Generate valid Mermaid flowchart syntax:"""
        
        # Retry logic with exponential backoff
        for attempt in range(1, max_retries + 1):
            t0 = time.perf_counter()
            try:
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,  # Lower temperature for consistent diagram generation
                    max_tokens=4000,   # Larger token limit for complex diagrams
                )

                dt = time.perf_counter() - t0
                text = response.choices[0].message.content.strip()

                logger.debug(
                    f"Mermaid generation completed ({dt:.2f}s), chars_out={len(text)}"
                )

                # Clean up Mermaid code blocks
                if text.startswith("```"):
                    text = re.sub(r"^```(mermaid)?\n", "", text).strip()
                    text = re.sub(r"```$", "", text).strip()
                
                # Ensure it starts with graph directive
                if not text.startswith("graph ") and not text.startswith("flowchart "):
                    # Find the first graph/flowchart directive
                    graph_start = text.find("graph ")
                    flowchart_start = text.find("flowchart ")
                    
                    if graph_start >= 0:
                        text = text[graph_start:]
                    elif flowchart_start >= 0:
                        text = text[flowchart_start:]
                    else:
                        # Add graph directive if missing
                        text = "graph TD\n\n" + text
                
                return text

            except Exception as e:
                dt = time.perf_counter() - t0
                if attempt <= max_retries:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Mermaid generation failed (try {attempt}/{max_retries}, {dt:.2f}s): {str(e)} - retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    continue
                logger.error(
                    f"Mermaid generation failed after {attempt - 1} attempts ({dt:.2f}s): {str(e)}"
                )
                return "graph TD\n    Start([Error generating diagram])\n    Start --> End([Please check logs])"

    def generate_text_sync(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: Optional[float] = 0.7,
        model: str = "gpt-4",
        agent_name: str = "TextGenerator",
    ) -> str:
        """
        Synchronous version of generate_text for non-async environments

        Args:
            user_prompt: The user message/prompt
            system_prompt: The system instructions for the agent
            temperature: Temperature setting for response creativity (0.0-1.0). Set to None for models that don't support it.
            model: Model to use (default: gpt-4)
            agent_name: Name for the agent (for logging/debugging)

        Returns:
            Generated text response as string
        """
        try:
            # Create agent with custom settings
            # Some models (like GPT-5 Nano) don't support temperature
            if temperature is not None:
                agent = Agent(
                    name=agent_name,
                    instructions=system_prompt,
                    model=model,
                    model_settings=ModelSettings(temperature=temperature),
                )
                logger.info(
                    f"Generating text (sync) with agent '{agent_name}' using model '{model}' at temperature {temperature}"
                )
            else:
                agent = Agent(
                    name=agent_name,
                    instructions=system_prompt,
                    model=model
                    # No model_settings for models that don't support temperature
                )
                logger.info(
                    f"Generating text (sync) with agent '{agent_name}' using model '{model}' (no temperature)"
                )

            # Run the agent synchronously
            result = Runner.run_sync(agent, user_prompt)

            # Extract the response
            response_text = result.final_output

            logger.info(
                f"Text generation completed. Response length: {len(response_text)} characters"
            )
            return response_text

        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    def research_company_with_web_search(
        self,
        symbol: str,
        company_name: str,
        industry: str,
        sector: str,
        model: str = "o4-mini",
        temperature: float = 0.5,
        allowed_domains: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        Research company information using web search capabilities.
        
        Uses OpenAI's Responses API with web_search tool to gather current,
        authoritative information about a company from the internet.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'WRB')
            company_name: Full company name (e.g., 'W.R. Berkley Corporation')
            industry: Industry classification (e.g., 'Property & Casualty Insurance')
            sector: Sector classification (e.g., 'Financials')
            model: Model to use (default: 'gpt-5' for web search)
            temperature: Temperature for generation (default: 0.5 for factual research)
            allowed_domains: Optional list of allowed domains to restrict search
                           (e.g., ['sec.gov', 'investor.company.com'])
        
        Returns:
            Dictionary containing:
                - company_overview: Generated overview text (200-400 words)
                - sources: List of URLs consulted
                - search_metadata: Information about the search process
        """
        try:
            logger.info(f"Starting web search research for {symbol} ({company_name})")
            
            # Load prompt template
            from src.metis.utils.prompt_loader import PromptLoader
            prompt_loader = PromptLoader()
            prompt_template = prompt_loader.load_prompt(
                "company_research", 
                "company_profile_web_search.txt"
            )
            
            # Format prompt with company data
            formatted_prompt = prompt_template.format(
                symbol=symbol,
                company_name=company_name,
                industry=industry,
                sector=sector
            )
            
            # Configure web search tool
            tools = [{
                "type": "web_search"
            }]
            
            # Add domain filtering if specified
            if allowed_domains:
                tools[0]["filters"] = {
                    "allowed_domains": allowed_domains
                }
                logger.info(f"Using domain filter: {allowed_domains}")
            
            # Make API call using Responses API with web search
            response = self.openai_client.responses.create(
                model=model,
                tools=tools,
                tool_choice="auto",
                include=["web_search_call.action.sources"],  # Include sources
                input=formatted_prompt,
            )
            
            # Extract company overview from response
            company_overview = response.output_text
            
            # Extract sources from web search results
            sources = []
            for output_item in response.output:
                if hasattr(output_item, 'type') and output_item.type == 'web_search_call':
                    if hasattr(output_item, 'action') and hasattr(output_item.action, 'sources'):
                        sources = output_item.action.sources or []
                        break
            
            # Extract citations from annotations
            citations = []
            for output_item in response.output:
                if hasattr(output_item, 'type') and output_item.type == 'message':
                    for content in output_item.content:
                        if hasattr(content, 'annotations'):
                            for annotation in content.annotations:
                                if annotation.type == 'url_citation':
                                    citations.append({
                                        'url': annotation.url,
                                        'title': annotation.title,
                                        'text_excerpt': company_overview[annotation.start_index:annotation.end_index]
                                    })
            
            logger.info(
                f"Web search completed. Overview: {len(company_overview)} chars, "
                f"Sources: {len(sources)}, Citations: {len(citations)}"
            )
            
            return {
                "company_overview": company_overview,
                "sources": sources,
                "citations": citations,
                "search_metadata": {
                    "symbol": symbol,
                    "company_name": company_name,
                    "industry": industry,
                    "sector": sector,
                    "model": model,
                    "sources_count": len(sources),
                    "citations_count": len(citations),
                    "domain_filter_applied": allowed_domains is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in web search research for {symbol}: {str(e)}")
            raise


# Convenience functions for direct usage
async def generate_text_async(
    user_prompt: str,
    system_prompt: str,
    temperature: Optional[float] = 0.7,
    model: str = "gpt-4",
    agent_name: str = "TextGenerator",
    api_key: Optional[str] = None,
) -> str:
    """
    Convenience function for async text generation without class instantiation

    Args:
        user_prompt: The user message/prompt
        system_prompt: The system instructions for the agent
        temperature: Temperature setting for response creativity (0.0-1.0). Set to None for models that don't support it.
        model: Model to use (default: gpt-4)
        agent_name: Name for the agent (for logging/debugging)
        api_key: OpenAI API key (optional)

    Returns:
        Generated text response as string
    """
    agent_instance = GenericLLMAgent(api_key=api_key)
    return await agent_instance.generate_text(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        model=model,
        agent_name=agent_name,
    )


def generate_text_sync(
    user_prompt: str,
    system_prompt: str,
    temperature: float = 0.7,
    model: str = "gpt-4",
    agent_name: str = "TextGenerator",
    api_key: Optional[str] = None,
) -> str:
    """
    Convenience function for sync text generation without class instantiation

    Args:
        user_prompt: The user message/prompt
        system_prompt: The system instructions for the agent
        temperature: Temperature setting for response creativity (0.0-1.0)
        model: Model to use (default: gpt-4)
        agent_name: Name for the agent (for logging/debugging)
        api_key: OpenAI API key (optional)

    Returns:
        Generated text response as string
    """
    agent_instance = GenericLLMAgent(api_key=api_key)
    return agent_instance.generate_text_sync(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        model=model,
        agent_name=agent_name,
    )


def main() -> None:
    """
    Test function for generic LLM agent
    Tests both async and sync text generation with sample prompts
    """
    import asyncio

    # Sample prompts for testing
    system_prompt = """You are a professional financial analyst writing for Barron's magazine.
    You provide clear, authoritative analysis with specific data points and actionable insights.
    Keep your tone professional and confident."""

    user_prompt = """Analyze the following market scenario:
    - Stock XYZ is trading at $50, up 5% today
    - RSI is at 65 (strong momentum)
    - Volume is 200% above average
    - Earnings are next week

    Write a brief analysis paragraph."""

    async def test_async():
        """Test async generation"""
        print("=" * 60)
        print("TESTING ASYNC TEXT GENERATION")
        print("=" * 60)

        try:
            response = await generate_text_async(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                agent_name="BarronsAnalyst",
            )

            print("✅ Async Generation Successful")
            print(f"Response Length: {len(response)} characters")
            print("\nGenerated Text:")
            print("-" * 40)
            print(response)
            print("-" * 40)

        except Exception as e:
            print(f"❌ Async Generation Failed: {str(e)}")

    def test_sync():
        """Test sync generation"""
        print("\n" + "=" * 60)
        print("TESTING SYNC TEXT GENERATION")
        print("=" * 60)

        try:
            response = generate_text_sync(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                agent_name="BarronsAnalyst",
            )

            print("✅ Sync Generation Successful")
            print(f"Response Length: {len(response)} characters")
            print("\nGenerated Text:")
            print("-" * 40)
            print(response)
            print("-" * 40)

        except Exception as e:
            print(f"❌ Sync Generation Failed: {str(e)}")

    def test_class_usage():
        """Test class-based usage"""
        print("\n" + "=" * 60)
        print("TESTING CLASS-BASED USAGE")
        print("=" * 60)

        try:
            # Initialize the agent
            llm_agent = GenericLLMAgent()

            # Generate text using class method
            response = llm_agent.generate_text_sync(
                user_prompt="What are the key factors to consider when analyzing a stock?",
                system_prompt="You are a helpful financial education assistant.",
                temperature=0.5,
                agent_name="EducationAssistant",
            )

            print("✅ Class-based Generation Successful")
            print(f"Response Length: {len(response)} characters")
            print("\nGenerated Text:")
            print("-" * 40)
            print(response)
            print("-" * 40)

        except Exception as e:
            print(f"❌ Class-based Generation Failed: {str(e)}")

    # Run tests
    print("🚀 Starting Generic LLM Agent Tests")

    # Test sync function
    test_sync()

    # Test class usage
    test_class_usage()

    # Test async function
    print("\n🔄 Running async test...")
    asyncio.run(test_async())

    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    main()