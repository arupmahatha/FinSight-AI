from typing import Dict, List
from anthropic import Anthropic

class SQLAnalyzer:
    def __init__(self, llm: Anthropic):
        self.llm = llm

    def analyze_results(self, query_info: Dict, sub_query_results: List[Dict]) -> Dict:
        """Analyze SQL query results from multiple sub-queries and generate comprehensive insights"""
        try:
            # Format results for prompt
            formatted_results = self._format_sub_queries_for_prompt(sub_query_results)
            
            # Create prompt for analysis
            prompt = f"""
            Analyze the following SQL query results and provide insights:
            
            Original Query: {query_info['original_query']}
            
            Results:
            {formatted_results}
            
            Provide analysis in the following JSON format:
            {{
                "summary": "Overall summary of the results",
                "insights": "Key insights from the data",
                "trends": "Any noticeable trends",
                "implications": "Business implications",
                "relationships": "Notable relationships between data points"
            }}
            """
            
            # Get analysis from LLM
            if callable(self.llm):
                response = self.llm(prompt)
                response_text = response
            else:
                response = self.llm.invoke(prompt)
                response_text = response.content[0].text if hasattr(response, 'content') else response.content

            # Clean and parse the response
            import json
            import ast

            try:
                # First try to parse as JSON
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                try:
                    # If JSON fails, try to find and parse dictionary string
                    dict_str = response_text.strip()
                    # Remove any markdown code block markers if present
                    dict_str = dict_str.replace('```json', '').replace('```', '').strip()
                    analysis = ast.literal_eval(dict_str)
                except:
                    # If both parsing attempts fail, create a basic analysis
                    analysis = {
                        "summary": "Unable to parse analysis results",
                        "insights": "Analysis format error",
                        "trends": "Analysis format error",
                        "implications": "Analysis format error",
                        "relationships": "Analysis format error"
                    }
            
            return {
                "success": True,
                "analysis": analysis,
                "sub_query_count": len(sub_query_results),
                "total_result_count": sum(len(r.get('results', [])) for r in sub_query_results),
                "query_info": query_info
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_info": query_info
            }

    def _format_sub_queries_for_prompt(self, formatted_results: List[Dict]) -> str:
        """Format multiple sub-query results for the analysis prompt"""
        output = []
        for idx, result in enumerate(formatted_results, 1):
            output.append(f"""
Sub-query {idx}:
Question: {result['sub_query']}
SQL Query: {result['sql_query']}
Results:
{result['results']}
""")
        return "\n".join(output)

    def _format_results_for_prompt(self, results: List[Dict]) -> str:
        """Format individual result set for the analysis prompt"""
        if not results:
            return "No results found"
            
        # Limit to first 10 rows for analysis
        sample_results = results[:10]
        formatted = []
        
        for row in sample_results:
            formatted.append(str(row))
            
        return "\n".join(formatted) 