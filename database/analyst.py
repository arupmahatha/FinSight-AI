import sqlite3
from typing import Dict
from config import Config
from engine.orchestrator import QueryOrchestrator
from langchain_anthropic import ChatAnthropic

class DatabaseAnalyst:
    def __init__(self, config: Config):
        self.config = config
        self.connection = self._create_connection()
        self.llm = ChatAnthropic(
            model=config.model_name,
            anthropic_api_key=config.api_key,
            max_tokens=4096
        )
        self.orchestrator = QueryOrchestrator(self.llm, self.connection)

    def _create_connection(self):
        """Create SQLite database connection"""
        try:
            return sqlite3.connect(self.config.db_path)
        except Exception as e:
            raise Exception(f"Failed to connect to database: {str(e)}")

    def process_query(self, query: str) -> Dict:
        """Process a natural language query"""
        try:
            steps_output = []
            
            # Step 1: Query Understanding
            steps_output.append({
                "step": "Query Understanding",
                "description": "Analyzing the input query",
                "input": query,
                "status": "completed"
            })
            
            # Step 2: Entity Recognition
            try:
                entity_matches = self.orchestrator.decomposer.find_entities(query)
                steps_output.append({
                    "step": "Entity Recognition",
                    "description": "Identifying database entities in the query",
                    "entities": entity_matches,
                    "status": "completed"
                })
            except Exception as e:
                steps_output.append({
                    "step": "Entity Recognition",
                    "description": "Identifying database entities in the query",
                    "error": str(e),
                    "status": "failed"
                })
                raise
                
            results = self.orchestrator.process_query(query)
            results["steps"] = steps_output
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "steps": steps_output if 'steps_output' in locals() else []
            }

    def format_output(self, results: Dict) -> str:
        """Format query results for display with detailed steps"""
        output = []
        
        # Process each step
        if steps := results.get("steps", []):
            for step in steps:
                step_name = step["step"]
                status = step.get("status", "unknown")
                status_emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
                
                output.append(f"\n### Step: {step_name} {status_emoji}")
                output.append(f"_{step['description']}_\n")
                
                if status == "failed":
                    output.append(f"**Error:** {step.get('error', 'Unknown error')}\n")
                    
                if step_name == "Query Understanding":
                    output.append(f"📝 **Input Query:** {step['input']}\n")
                    
                elif step_name == "Entity Recognition" and status == "completed":
                    output.append("🔍 **Identified Entities:**")
                    for entity in step['entities']:
                        output.append(f"- Table: `{entity['table']}`, Column: `{entity['column']}`")
                        output.append(f"  - Matched: '{entity['matched_value']}' (Score: {entity['score']})")
                    output.append("")
                    
                elif step_name == "Query Decomposition" and status == "completed":
                    output.append("📋 **Sub-queries:**")
                    for i, sub_query in enumerate(step['sub_queries'], 1):
                        output.append(f"{i}. {sub_query}")
                    output.append("")
                    
                elif step_name == "SQL Generation":
                    output.append("💻 **Generated SQL:**")
                    if status == "completed":
                        for query in step['queries']:
                            output.append(f"\nFor: _{query['sub_query']}_")
                            output.append(f"```sql\n{query['sql_query']}\n```")
                    elif status == "failed" and step.get('partial_queries'):
                        output.append("\n**Partial Results Before Error:**")
                        for query in step['partial_queries']:
                            output.append(f"\nFor: _{query['sub_query']}_")
                            output.append(f"```sql\n{query['sql_query']}\n```")
                    output.append("")
                    
                elif step_name == "Query Execution" and status == "completed":
                    output.append("📊 **Query Results:**")
                    for result in step['results']:
                        output.append(f"\nQuery: _{result['sub_query']}_")
                        if result.get('error'):
                            output.append(f"❌ Error: {result['error']}")
                        else:
                            output.append("Results:")
                            results_data = result['results']
                            if results_data:
                                # Format as markdown table
                                headers = results_data[0].keys()
                                output.append("\n| " + " | ".join(headers) + " |")
                                output.append("| " + " | ".join(["---"] * len(headers)) + " |")
                                for row in results_data:
                                    output.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
                            else:
                                output.append("_No results found_")
                        output.append("")
                    
                elif step_name == "Analysis" and status == "completed":
                    if analysis := step.get('analysis', {}).get('analysis', {}):
                        output.append("🎯 **Analysis Results:**")
                        output.append(f"\n**Summary:** {analysis.get('summary', 'No summary available')}")
                        
                        if insights := analysis.get('insights'):
                            output.append("\n**Key Insights:**")
                            output.append(f"- {insights}")
                        
                        if trends := analysis.get('trends'):
                            output.append("\n**Trends:**")
                            output.append(f"- {trends}")
                        
                        if implications := analysis.get('implications'):
                            output.append("\n**Business Implications:**")
                            output.append(f"- {implications}")
                            
                        if relationships := analysis.get('relationships'):
                            output.append("\n**Relationships:**")
                            output.append(f"- {relationships}")

        # Add final error message if process failed
        if not results.get("success", False):
            output.append(f"\n❌ **Final Error:** {results.get('error', 'Unknown error')}")

        return "\n".join(output) 