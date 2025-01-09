from typing import Dict, List, Tuple, Annotated, TypedDict
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, Graph
from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain_core.tools import BaseTool, StructuredTool, tool

from engine.decomposer import QueryDecomposer
from engine.generator import SQLGenerator
from engine.executor import SQLExecutor
from engine.analyzer import SQLAnalyzer

class GraphState(TypedDict):
    query: str
    decomposed_queries: List[Dict]
    generated_sql: List[Dict]
    query_results: List[Dict]
    final_analysis: Dict
    error: str
    steps_output: List[Dict]  # Track detailed steps like test_workflow

class QueryOrchestrator:
    def __init__(self, llm: ChatAnthropic, db_connection):
        # Convert ChatAnthropic to compatible interface
        self.llm = self._create_compatible_llm(llm)
        self.decomposer = QueryDecomposer(self.llm)
        self.generator = SQLGenerator(self.llm)
        self.executor = SQLExecutor(db_connection)
        self.analyzer = SQLAnalyzer(self.llm)
        
        # Initialize graph
        self.workflow = self._create_workflow()

    def _create_compatible_llm(self, llm: ChatAnthropic):
        """Create a compatible LLM interface for core components"""
        return lambda prompt: llm.invoke(prompt).content

    def _decompose_step(self, state: GraphState) -> GraphState:
        """Handle query decomposition step"""
        try:
            # First decompose into sub-queries
            sub_queries = self.decomposer._decompose_complex_query(state["query"])
            
            decomposition_details = []
            for idx, query in enumerate(sub_queries, 1):
                # Get table for this sub-query
                table = self.decomposer._select_relevant_table(query)
                
                # Get entities for this sub-query
                table_info = self.decomposer.metadata.get_table_info(table)
                self.decomposer._initialize_matcher(table_info)
                entities = self.decomposer._extract_entities(query, table_info)
                
                detail = {
                    "sub_query_number": idx,
                    "query": query,
                    "table": table,
                    "entities": entities,
                    "table_info": table_info,
                    "type": "direct" if len(sub_queries) == 1 else "decomposed",
                    "explanation": f"Query processed using {table} table"
                }
                decomposition_details.append(detail)
            
            state["decomposed_queries"] = decomposition_details
            state["steps_output"].append({
                "step": "Query Understanding and Decomposition",
                "details": decomposition_details,
                "status": "completed"
            })
            return state
            
        except Exception as e:
            state["error"] = f"Decomposition failed: {str(e)}"
            state["steps_output"].append({
                "step": "Query Understanding and Decomposition",
                "error": str(e),
                "status": "failed"
            })
            return state

    def _generate_step(self, state: GraphState) -> GraphState:
        """Handle SQL generation step"""
        try:
            generated_queries = []
            for query_info in state["decomposed_queries"]:
                # Generate SQL for this sub-query
                query_data = {
                    'sub_query': query_info['query'],
                    'table': query_info['table'],
                    'entities': query_info['entities']
                }
                
                sql = self.generator.generate_sql(query_data)
                generated_queries.append({
                    **query_info,
                    "sql_query": sql
                })
            
            state["generated_sql"] = generated_queries
            state["steps_output"].append({
                "step": "SQL Generation",
                "queries": generated_queries,
                "status": "completed"
            })
            return state
            
        except Exception as e:
            state["error"] = f"SQL generation failed: {str(e)}"
            state["steps_output"].append({
                "step": "SQL Generation",
                "error": str(e),
                "status": "failed"
            })
            return state

    def _execute_step(self, state: GraphState) -> GraphState:
        """Handle SQL execution step"""
        try:
            execution_results = []
            for query_info in state["generated_sql"]:
                # Validate and execute SQL
                is_valid, error = self.executor.validate_query(query_info["sql_query"])
                if is_valid:
                    success, results, error = self.executor.execute_query(query_info["sql_query"])
                    execution_results.append({
                        **query_info,
                        "results": results if success else [],
                        "error": error if not success else None
                    })
                else:
                    execution_results.append({
                        **query_info,
                        "results": [],
                        "error": f"Validation failed: {error}"
                    })
            
            state["query_results"] = execution_results
            state["steps_output"].append({
                "step": "Query Execution",
                "results": execution_results,
                "status": "completed"
            })
            return state
            
        except Exception as e:
            state["error"] = f"Execution failed: {str(e)}"
            state["steps_output"].append({
                "step": "Query Execution",
                "error": str(e),
                "status": "failed"
            })
            return state

    def _analyze_step(self, state: GraphState) -> GraphState:
        """Handle results analysis step"""
        try:
            if state["query_results"]:
                query_info = {"original_query": state["query"]}
                analysis = self.analyzer.analyze_results(query_info, state["query_results"])
                state["final_analysis"] = analysis
                state["steps_output"].append({
                    "step": "Analysis",
                    "analysis": analysis,
                    "status": "completed"
                })
            return state
            
        except Exception as e:
            state["error"] = f"Analysis failed: {str(e)}"
            state["steps_output"].append({
                "step": "Analysis",
                "error": str(e),
                "status": "failed"
            })
            return state

    def _create_workflow(self) -> Graph:
        """Create the workflow graph"""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("decompose", self._decompose_step)
        workflow.add_node("generate", self._generate_step)
        workflow.add_node("execute", self._execute_step)
        workflow.add_node("analyze", self._analyze_step)
        
        # Add edges
        workflow.add_edge("decompose", "generate")
        workflow.add_edge("generate", "execute")
        workflow.add_edge("execute", "analyze")
        
        # Set entry and end points
        workflow.set_entry_point("decompose")
        workflow.set_finish_point("analyze")
        
        return workflow.compile()

    def process_query(self, query: str) -> Dict:
        """Process a natural language query following test workflow structure"""
        try:
            # Initialize state
            state = {
                "query": query,
                "decomposed_queries": [],
                "generated_sql": [],
                "query_results": [],
                "final_analysis": {},
                "error": "",
                "steps_output": []
            }
            
            # Run the workflow
            final_state = self.workflow.invoke(state)
            
            return {
                "success": not bool(final_state["error"]),
                "error": final_state["error"],
                "steps": final_state["steps_output"],
                "analysis": final_state.get("final_analysis", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "steps": state["steps_output"] if "state" in locals() else []
            } 