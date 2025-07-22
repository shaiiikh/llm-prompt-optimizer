from event_llm_core import generate_description
import argparse

def main():
    parser = argparse.ArgumentParser(description="Event Description Generation Service")
    parser.add_argument('--title', required=True, help='Event title')
    parser.add_argument('--category', required=True, help='Event category')
    parser.add_argument('--event_type', required=True, help='Event type')
    parser.add_argument('--tone', required=True, help='Tone of the event')
    parser.add_argument('--context', required=False, default=None, help='Optional context')
    parser.add_argument('--max_chars', type=int, default=800, help='Maximum characters (max 2000)')
    
    args = parser.parse_args()
    
    max_chars = max(100, min(args.max_chars, 2000))
    
    print(f"[Description Service] Generating description")
    print(f"[Description Service] Title: {args.title}")
    print(f"[Description Service] Category: {args.category}")
    print(f"[Description Service] Event Type: {args.event_type}")
    print(f"[Description Service] Tone: {args.tone}")
    print(f"[Description Service] Context: {args.context}")
    print(f"[Description Service] Max Characters: {max_chars}")
    print("-" * 50)
    
    description, logs = generate_description(args.title, args.category, args.event_type, args.tone, args.context, max_chars)
    
    print("[Description Service] Generation Logs:")
    for k, v in logs.items():
        print(f"  {k}: {v}")
    
    print(f"[Description Service] Generated Description:")
    print(f"  {description}")
    print(f"[Description Service] Actual Length: {len(description)} characters")

if __name__ == "__main__":
    main() 