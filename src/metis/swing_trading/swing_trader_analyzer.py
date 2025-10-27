"""
Swing Trader Analyzer - Main orchestrator for swing trading analysis.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import asyncio

from .signal_extractor import SignalExtractor
from .prompt_generator import PromptGenerator
from .models import SwingTradingSignals
from metis.assistants.generic_llm_agent import GenericLLMAgent


class SwingTraderAnalyzer:
    """Main orchestrator for swing trading analysis.
    Main orchestrator for swing trading analysis.
    
    Converts competitive intelligence reports into actionable swing trading signals
    and generates prompts for LLM-based analysis.
    """
    def __init__(self, template_path: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize analyzer.
        
        Args:
            template_path: Optional path to custom prompt template
            api_key: Optional OpenAI API key (defaults to environment variable)
        """
        self.prompt_generator = PromptGenerator(template_path)
        self.llm_agent = GenericLLMAgent(api_key=api_key)
    
    def analyze_from_json(self, json_path: str) -> SwingTradingSignals:
        """
        Analyze competitive intelligence report from JSON file.
        
        Args:
            json_path: Path to competitive intelligence JSON report
            
        Returns:
            SwingTradingSignals object with all trading signals
        """
        # Load JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        return self.analyze_from_dict(report_data)
    
    def analyze_from_dict(self, report_data: Dict[str, Any]) -> SwingTradingSignals:
        """
        Analyze competitive intelligence report from dictionary.
        
        Args:
            report_data: Competitive intelligence report as dictionary
            
        Returns:
            SwingTradingSignals object with all trading signals
        """
        extractor = SignalExtractor(report_data)
        return extractor.extract_all_signals()
    
    def generate_llm_prompt(self, report_data: Dict[str, Any]) -> str:
        """
        Generate populated LLM prompt from competitive intelligence report.
        
        Args:
            report_data: Competitive intelligence report as dictionary
            
        Returns:
            Populated prompt string ready for LLM
        """
        return self.prompt_generator.populate_template(report_data)
    
    def generate_llm_prompt_from_json(self, json_path: str) -> str:
        """
        Generate populated LLM prompt from JSON file.
        
        Args:
            json_path: Path to competitive intelligence JSON report
            
        Returns:
            Populated prompt string ready for LLM
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        with open(json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        return self.prompt_generator.populate_template(report_data)
    
    async def generate_trading_narrative(
        self,
        report_data: Dict[str, Any],
        model: str = "gpt-4",
        temperature: float = 0.7
    ) -> str:
        """
        Generate comprehensive trading narrative using LLM.
        
        Args:
            report_data: Competitive intelligence report as dictionary
            model: LLM model to use (default: gpt-4)
            temperature: Temperature for generation (default: 0.7)
            
        Returns:
            Generated trading analysis narrative
        """
        # Generate populated prompt
        populated_prompt = self.generate_llm_prompt(report_data)
        
        # System prompt for swing trading analysis
        system_prompt = """You are an experienced swing trader and financial analyst specializing in competitive intelligence analysis.

Your task is to analyze competitive intelligence data and generate a comprehensive swing trading report that includes:

1. **Key Trading Signals** - Valuation gaps, momentum indicators, hidden strengths
2. **Trading Setup Framework** - Entry/exit levels, support/resistance, fair value targets
3. **Risk Assessment** - Downside scenarios, stop-loss strategies, momentum risks
4. **Catalyst Calendar** - Upcoming events that could trigger price movements
5. **Practical Playbook** - Specific bullish/bearish/neutral scenarios with triggers and targets

Write in a direct, actionable style that helps traders make informed decisions. Include specific numbers, percentages, and price targets where applicable. Focus on the 3-12 month trading horizon."""
        
        # Generate narrative using LLM
        narrative = await self.llm_agent.generate_text(
            user_prompt=populated_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            model=model,
            agent_name="SwingTraderAnalyst"
        )
        
        return narrative
    
    def generate_trading_narrative_sync(
        self,
        report_data: Dict[str, Any],
        model: str = "gpt-4",
        temperature: float = 0.7
    ) -> str:
        """
        Generate comprehensive trading narrative using LLM (synchronous version).
        
        Args:
            report_data: Competitive intelligence report as dictionary
            model: LLM model to use (default: gpt-4)
            temperature: Temperature for generation (default: 0.7)
            
        Returns:
            Generated trading analysis narrative
        """
        # Generate populated prompt
        populated_prompt = self.generate_llm_prompt(report_data)
        
        # System prompt for swing trading analysis
        system_prompt = """You are an experienced swing trader and financial analyst specializing in competitive intelligence analysis.

Your task is to analyze competitive intelligence data and generate a comprehensive swing trading report that includes:

1. **Key Trading Signals** - Valuation gaps, momentum indicators, hidden strengths
2. **Trading Setup Framework** - Entry/exit levels, support/resistance, fair value targets
3. **Risk Assessment** - Downside scenarios, stop-loss strategies, momentum risks
4. **Catalyst Calendar** - Upcoming events that could trigger price movements
5. **Practical Playbook** - Specific bullish/bearish/neutral scenarios with triggers and targets

Write in a direct, actionable style that helps traders make informed decisions. Include specific numbers, percentages, and price targets where applicable. Focus on the 3-12 month trading horizon."""
        
        # Generate narrative using LLM
        narrative = self.llm_agent.generate_text_sync(
            user_prompt=populated_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            model=model,
            agent_name="SwingTraderAnalyst"
        )
        
        return narrative
    
    def full_analysis(
        self,
        report_data: Dict[str, Any],
        output_signals_path: Optional[str] = None,
        output_prompt_path: Optional[str] = None,
        output_narrative_path: Optional[str] = None,
        generate_narrative: bool = False,
        model: str = "gpt-4"
    ) -> tuple[SwingTradingSignals, str, Optional[str]]:
        """
        Perform complete analysis: extract signals + generate LLM prompt + optional narrative.
        
        Args:
            report_data: Competitive intelligence report as dictionary
            output_signals_path: Optional path to save signals JSON
            output_prompt_path: Optional path to save populated prompt
            output_narrative_path: Optional path to save LLM-generated narrative
            generate_narrative: Whether to generate LLM narrative (default: False)
            model: LLM model to use if generating narrative (default: gpt-4)
            
        Returns:
            Tuple of (SwingTradingSignals, populated_prompt, optional_narrative)
        """
        # Extract signals
        signals = self.analyze_from_dict(report_data)
        
        # Generate prompt
        prompt = self.generate_llm_prompt(report_data)
        
        # Generate narrative if requested
        narrative = None
        if generate_narrative:
            narrative = self.generate_trading_narrative_sync(report_data, model=model)
        
        # Save outputs if requested
        if output_signals_path:
            with open(output_signals_path, 'w', encoding='utf-8') as f:
                json.dump(signals.model_dump(), f, indent=2)
        
        if output_prompt_path:
            with open(output_prompt_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
        
        if output_narrative_path and narrative:
            with open(output_narrative_path, 'w', encoding='utf-8') as f:
                f.write(narrative)
        
        return signals, prompt, narrative
