import os
import json
import time
import argparse
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from groq import Groq, APIError, APIConnectionError, RateLimitError

@dataclass
class ClauseResult:
    clause_type: str = ""
    risk_level: str = ""
    flag_reason: str = ""
    recommended_action: str = ""
    confidence: str = ""
    error: Optional[str] = None

class ContractAnalyzer:
    def __init__(self, system_prompt_path: str = "system_prompt.txt"):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set. Please set it before running.")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        
        try:
            with open(system_prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"System prompt file not found at {system_prompt_path}")

    def analyze_clause(self, clause_text: str, max_retries: int = 3) -> ClauseResult:
        base_delay = 2
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"<clause>\n{clause_text}\n</clause>"}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content.strip()
                
                # Attempt to parse JSON
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    # Sometimes the model might wrap in ```json ... ``` despite instructions
                    if content.startswith("```json"):
                        content = content.replace("```json", "", 1)
                        if content.endswith("```"):
                            content = content[:-3]
                        content = content.strip()
                        parsed = json.loads(content)
                    else:
                        raise ValueError(f"Failed to parse JSON. Raw output: {content}")
                
                if "error" in parsed:
                    return ClauseResult(error=parsed["error"])
                
                # Validate required keys
                required_keys = {"clause_type", "risk_level", "flag_reason", "recommended_action", "confidence"}
                if not required_keys.issubset(parsed.keys()):
                    raise ValueError(f"Missing required keys in JSON output. Got: {list(parsed.keys())}")
                
                return ClauseResult(
                    clause_type=parsed["clause_type"],
                    risk_level=parsed["risk_level"],
                    flag_reason=parsed["flag_reason"],
                    recommended_action=parsed["recommended_action"],
                    confidence=parsed["confidence"]
                )
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed due to parsing error: {e}")
                if attempt == max_retries - 1:
                    return ClauseResult(error=f"Failed to parse model output after {max_retries} attempts.")
            except (APIError, APIConnectionError, RateLimitError) as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed due to API error: {e}")
                if attempt == max_retries - 1:
                    return ClauseResult(error=f"API request failed after {max_retries} attempts: {str(e)}")
                
            time.sleep(base_delay ** (attempt + 1)) # Exponential backoff

        return ClauseResult(error="Unknown error occurred during analysis.")

    def analyze_batch(self, clauses: List[Dict[str, str]]) -> Dict[str, Any]:
        results = []
        error_count = 0
        risk_distribution = {"High": 0, "Medium": 0, "Low": 0}
        type_distribution = {}
        
        for item in clauses:
            text = item.get("text", "")
            if not text:
                continue
            
            res = self.analyze_clause(text)
            res_dict = asdict(res)
            
            # Combine original item info with results
            output_item = {**item, "analysis": res_dict}
            results.append(output_item)
            
            if res.error:
                error_count += 1
            else:
                risk = res.risk_level
                if risk in risk_distribution:
                    risk_distribution[risk] += 1
                else:
                    risk_distribution[risk] = 1
                    
                ctype = res.clause_type
                type_distribution[ctype] = type_distribution.get(ctype, 0) + 1
                
        summary = {
            "total_clauses": len(clauses),
            "error_count": error_count,
            "risk_distribution": risk_distribution,
            "clause_type_distribution": type_distribution
        }
        
        return {
            "summary": summary,
            "results": results
        }

def main():
    parser = argparse.ArgumentParser(description="Contract Clause Risk Analyzer")
    parser.add_argument("--clause", type=str, help="Single clause text to analyze")
    parser.add_argument("--input", type=str, help="Path to JSON file containing a list of clauses")
    parser.add_argument("--output", type=str, default="results.json", help="Path to output JSON file (for batch mode)")
    
    args = parser.parse_args()
    
    if not args.clause and not args.input:
        parser.error("Must provide either --clause or --input")
        
    try:
        analyzer = ContractAnalyzer()
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
        
    if args.clause:
        print(f"Analyzing single clause...\n")
        res = analyzer.analyze_clause(args.clause)
        print(json.dumps(asdict(res), indent=2))
        
    elif args.input:
        print(f"Analyzing batch from {args.input}...")
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                clauses = json.load(f)
        except Exception as e:
            print(f"Error reading input file: {e}")
            exit(1)
            
        if not isinstance(clauses, list):
            print("Error: Input JSON must be a list of clause objects.")
            exit(1)
            
        batch_results = analyzer.analyze_batch(clauses)
        
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(batch_results, f, indent=2)
            print(f"Batch analysis complete. Results saved to {args.output}")
            print("Summary:")
            print(json.dumps(batch_results["summary"], indent=2))
        except Exception as e:
            print(f"Error writing output file: {e}")
            exit(1)

if __name__ == "__main__":
    main()
