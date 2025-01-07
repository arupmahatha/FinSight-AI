from typing import Dict, List
from anthropic import Anthropic

class SQLAnalyzer:
    def __init__(self, llm: Anthropic):
        self.llm = llm

    def analyze_results(self, query_info: Dict, sub_query_results: List[Dict]) -> Dict:
        """Analyze SQL query results from multiple sub-queries and generate comprehensive insights"""
        try:
            # Format all sub-query results
            formatted_results = []
            for result in sub_query_results:
                formatted_result = self._format_results_for_prompt(result.get('results', []))
                formatted_results.append({
                    'sub_query': result.get('sub_query', ''),
                    'sql_query': result.get('sql_query', ''),
                    'results': formatted_result
                })
            
            prompt = f"""Analyze the following set of query results and provide comprehensive insights:

Original User Question: {query_info.get('original_query', '')}

Sub-queries and their results:
{self._format_sub_queries_for_prompt(formatted_results)}

Format the response as JSON with these keys:
- summary: Overall summary of all results
- insights: Key patterns and findings
- trends: Notable trends and anomalies
- implications: Business implications
- relationships: Connections between sub-query results"""

            # Use the new Anthropic client method
            message = self.llm.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse JSON response
            analysis = eval(message.content[0].text.strip())
            
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