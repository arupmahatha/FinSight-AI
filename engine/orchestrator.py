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

class QueryOrchestrator:
    def __init__(self, llm: ChatAnthropic, db_connection):
        self.decomposer = QueryDecomposer(llm)
        self.generator = SQLGenerator(llm)
        self.executor = SQLExecutor(db_connection)
        self.analyzer = SQLAnalyzer(llm)
        
        # Initialize graph
        self.workflow = self._create_workflow()

    def _create_decomposer_tool(self) -> BaseTool:
        @tool("query_decomposer")
        def decompose_query(query: str) -> List[Dict]:
            """Decompose complex query into simpler sub-queries"""
            return self.decomposer.decompose_query(query)
        return decompose_query

    def _create_generator_tool(self) -> BaseTool:
        @tool("sql_generator")
        def generate_sql(query_info: Dict) -> str:
            """Generate SQL from natural language query"""
            return self.generator.generate_sql(query_info)
        return generate_sql

    def _create_executor_tool(self) -> BaseTool:
        @tool("sql_executor")
        def execute_sql(sql_query: str) -> Tuple[bool, List[Dict], str]:
            """Execute SQL query safely"""
            return self.executor.execute_query(sql_query)
        return execute_sql

    def _create_analyzer_tool(self) -> BaseTool:
        @tool("result_analyzer")
        def analyze_results(query_info: Dict, results: List[Dict]) -> Dict:
            """Analyze query results and generate insights"""
            return self.analyzer.analyze_results(query_info, results)
        return analyze_results

    def _decompose_step(self, state: GraphState) -> GraphState:
        """Handle query decomposition step"""
        try:
            decomposed = self.decomposer.decompose_query(state["query"])
            state["decomposed_queries"] = decomposed
            return state
        except Exception as e:
            state["error"] = f"Decomposition failed: {str(e)}"
            return state

    def _generate_step(self, state: GraphState) -> GraphState:
        """Handle SQL generation step"""
        try:
            generated_queries = []
            for query_info in state["decomposed_queries"]:
                sql = self.generator.generate_sql(query_info)
                generated_queries.append({
                    **query_info,
                    "sql_query": sql
                })
            state["generated_sql"] = generated_queries
            return state
        except Exception as e:
            state["error"] = f"SQL generation failed: {str(e)}"
            return state

    def _execute_step(self, state: GraphState) -> GraphState:
        """Handle SQL execution step"""
        try:
            results = []
            for query_info in state["generated_sql"]:
                success, query_results, error = self.executor.execute_query(query_info["sql_query"])
                if not success:
                    raise Exception(error)
                results.append({
                    **query_info,
                    "results": query_results
                })
            state["query_results"] = results
            return state
        except Exception as e:
            state["error"] = f"Execution failed: {str(e)}"
            return state

    def _analyze_step(self, state: GraphState) -> GraphState:
        """Handle results analysis step"""
        try:
            if state["query_results"]:
                query_info = {"original_query": state["query"]}
                analysis = self.analyzer.analyze_results(query_info, state["query_results"])
                state["final_analysis"] = analysis
            return state
        except Exception as e:
            state["error"] = f"Analysis failed: {str(e)}"
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
                "query_results": [],
                "final_analysis": {},
                "error": "",
                "steps_output": []  # Track detailed steps like test_workflow
            }

            # Step 1: Query Understanding and Decomposition
            state["steps_output"].append({
                "step": "Query Understanding",
                "description": "Analyzing input query",
                "input": query,
                "status": "completed"
            })

            try:
                # Decompose the query first
                decomposed_results = self.decomposer.decompose_query(query)
                
                decomposition_details = []
                for idx, decomposed in enumerate(decomposed_results, 1):
                    # Find entities for this specific sub-query
                    entities = self.decomposer.find_entities(decomposed['sub_query'])
                    decomposed['entities'] = entities  # Store entities with each sub-query
                    
                    detail = {
                        "sub_query_number": idx,
                        "type": decomposed['type'],
                        "query": decomposed['sub_query'],
                        "table": decomposed['table'],
                        "entities": entities,
                        "total_entities": len(entities),
                        "explanation": decomposed['explanation']
                    }
                    decomposition_details.append(detail)

                state["decomposed_queries"] = decomposed_results
                state["steps_output"].append({
                    "step": "Query Decomposition",
                    "description": "Breaking down complex query into simpler parts",
                    "details": decomposition_details,
                    "status": "completed"
                })

            except Exception as e:
                state["steps_output"].append({
                    "step": "Query Decomposition",
                    "description": "Breaking down complex query into simpler parts",
                    "error": str(e),
                    "status": "failed"
                })
                raise

            # Step 2: SQL Generation
            try:
                generated_queries = []
                for decomposed in state["decomposed_queries"]:
                    # Get table metadata for the generator
                    table_info = self.generator.metadata.get_table_info(decomposed['table'])
                    
                    # Generate SQL using the decomposed query with its entities
                    sql_query = self.generator.generate_sql(decomposed)
                    
                    generated_queries.append({
                        "sub_query": decomposed['sub_query'],
                        "table": decomposed['table'],
                        "table_info": table_info,
                        "sql_query": sql_query
                    })

                state["steps_output"].append({
                    "step": "SQL Generation",
                    "description": "Converting natural language to SQL",
                    "queries": generated_queries,
                    "status": "completed"
                })

            except Exception as e:
                state["steps_output"].append({
                    "step": "SQL Generation",
                    "description": "Converting natural language to SQL",
                    "error": str(e),
                    "status": "failed"
                })
                raise

            # Step 3: Query Execution
            try:
                all_results = []
                for query_info in generated_queries:
                    # First validate the query
                    is_valid, error = self.executor.validate_query(query_info['sql_query'])
                    
                    if not is_valid:
                        raise ValueError(f"SQL validation failed: {error}")
                    
                    success, results, error = self.executor.execute_query(query_info['sql_query'])
                    if not success:
                        raise ValueError(f"Query execution failed: {error}")
                    
                    all_results.append({
                        'sub_query': query_info['sub_query'],
                        'sql_query': query_info['sql_query'],
                        'results': results
                    })

                state["query_results"] = all_results
                state["steps_output"].append({
                    "step": "Query Execution",
                    "description": "Executing SQL queries and fetching results",
                    "results": all_results,
                    "status": "completed"
                })

            except Exception as e:
                state["steps_output"].append({
                    "step": "Query Execution",
                    "description": "Executing SQL queries and fetching results",
                    "error": str(e),
                    "status": "failed"
                })
                raise

            # Step 4: Analysis
            if state["query_results"]:
                try:
                    analysis = self.analyzer.analyze_results(
                        {'original_query': query},
                        state["query_results"]
                    )
                    
                    state["final_analysis"] = analysis
                    state["steps_output"].append({
                        "step": "Analysis",
                        "description": "Analyzing query results and generating insights",
                        "analysis": analysis,
                        "status": "completed"
                    })

                except Exception as e:
                    state["steps_output"].append({
                        "step": "Analysis",
                        "description": "Analyzing query results and generating insights",
                        "error": str(e),
                        "status": "failed"
                    })
                    raise

            return {
                "success": True,
                "state": state,
                "steps": state["steps_output"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "state": state if 'state' in locals() else {},
                "steps": state["steps_output"] if 'state' in locals() else []
            } 