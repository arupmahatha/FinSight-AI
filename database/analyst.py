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
            
            # Get orchestrator results
            results = self.orchestrator.process_query(query)
            
            # Merge steps
            if results.get("steps"):
                steps_output.extend(results["steps"])
            
            results["steps"] = steps_output
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "steps": steps_output if 'steps_output' in locals() else []
            }

    def format_output(self, results: Dict) -> str:
        """Format output to match test_workflow.py style"""
        output = []
        
        if steps := results.get("steps", []):
            for step in steps:
                step_name = step["step"]
                status = step.get("status", "unknown")
                
                # Print step header like test_workflow
                output.append(f"\n=== {step_name} ===")
                
                if status == "failed":
                    output.append(f"❌ Error: {step.get('error', 'Unknown error')}")
                    continue
                    
                if step_name == "Query Understanding":
                    output.append(f"Input Query: {step['input']}")
                    
                elif step_name == "Query Decomposition":
                    output.append(f"\nDecomposed into {len(step['details'])} sub-queries:")
                    for detail in step['details']:
                        output.append(f"\nSub-query {detail['sub_query_number']}:")
                        output.append(f"- Type: {detail['type']}")
                        output.append(f"- Query: {detail['query']}")
                        output.append(f"- Table: {detail['table']}")
                        
                        output.append("\nIdentified Entities:")
                        for entity in detail['entities']:
                            output.append(
                                f"- Found '{entity['search_term']}' in column '{entity['column']}'\n"
                                f"  Matched Value: '{entity['matched_value']}' (Score: {entity['score']})"
                            )
                        
                        output.append(f"- Total Entities: {detail['total_entities']}")
                        output.append(f"- Explanation: {detail['explanation']}")
                    
                elif step_name == "SQL Generation":
                    for query in step['queries']:
                        output.append(f"\nProcessing sub-query: {query['sub_query']}")
                        output.append(f"\nUsing table: {query['table']}")
                        
                        output.append("Available columns:")
                        for col, info in query['table_info'].columns.items():
                            output.append(f"- {col}: {info.description}")
                        
                        output.append(f"\nGenerated SQL: {query['sql_query']}")
                    
                elif step_name == "Query Execution":
                    for result in step['results']:
                        if 'error' in result:
                            output.append(f"\nExecution failed: {result['error']}")
                        else:
                            output.append(f"\nExecution successful: {len(result['results'])} rows returned")
                            if result['results']:
                                output.append("\nResults Preview:")
                                headers = result['results'][0].keys()
                                output.append(" | ".join(str(h) for h in headers))
                                output.append("-" * 50)
                                for row in result['results'][:3]:
                                    output.append(" | ".join(str(row[h]) for h in headers))
                    
                elif step_name == "Analysis" and step.get('analysis'):
                    analysis = step['analysis']
                    output.append("\nAnalysis Results:")
                    output.append(f"\nSuccess: {analysis['success']}")
                    output.append(f"Sub-query count: {analysis['sub_query_count']}")
                    output.append(f"Total result count: {analysis['total_result_count']}")
                    output.append("\nAnalysis:")
                    output.append(f"Summary: {analysis['analysis'].get('summary', 'N/A')}")
                    output.append(f"Insights: {analysis['analysis'].get('insights', 'N/A')}")
                    output.append(f"Trends: {analysis['analysis'].get('trends', 'N/A')}")
                    output.append(f"Implications: {analysis['analysis'].get('implications', 'N/A')}")
                    output.append(f"Relationships: {analysis['analysis'].get('relationships', 'N/A')}")
        
        # Add final error if process failed
        if not results.get("success", False):
            output.append(f"\n❌ Workflow failed: {results.get('error', 'Unknown error')}")
        
        return "\n".join(output) 