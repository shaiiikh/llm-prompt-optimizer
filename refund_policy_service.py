from event_llm_core import generate_refund_policy
import argparse

def main():
    parser = argparse.ArgumentParser(description="Event Refund Policy Generation Service")
    parser.add_argument('--title', required=True, help='Event title')
    parser.add_argument('--description', required=True, help='Event description')
    parser.add_argument('--category', required=True, help='Event category')
    parser.add_argument('--event_type', required=True, help='Event type')
    parser.add_argument('--tone', required=True, help='Tone of the event')
    parser.add_argument('--context', required=False, default=None, help='Optional context')
    parser.add_argument('--cost_mode', choices=['economy', 'balanced', 'premium'], default='balanced', help='Cost/quality mode')
    
    args = parser.parse_args()
    
    errors = []
    if not args.title or args.title.strip() == "":
        errors.append("Title is required")
    if not args.description or args.description.strip() == "":
        errors.append("Description is required")
    if not args.category or args.category.strip() == "":
        errors.append("Category is required")
    if not args.event_type or args.event_type.strip() == "":
        errors.append("Event type is required")
    if not args.tone or args.tone.strip() == "":
        errors.append("Tone is required")
    
    if errors:
        print("[Refund Policy Service] Validation Errors:")
        for error in errors:
            print(f"  • {error}")
        exit(1)
    
    print(f"[Refund Policy Service] Generating refund policy")
    print(f"[Refund Policy Service] Title: {args.title}")
    print(f"[Refund Policy Service] Description: {args.description}")
    print(f"[Refund Policy Service] Category: {args.category}")
    print(f"[Refund Policy Service] Event Type: {args.event_type}")
    print(f"[Refund Policy Service] Tone: {args.tone}")
    print(f"[Refund Policy Service] Context: {args.context}")
    print(f"[Refund Policy Service] Cost Mode: {args.cost_mode}")
    print("-" * 50)
    
    refund_policy, logs = generate_refund_policy(
        args.title,
        args.description,
        args.category,
        args.event_type,
        args.tone,
        args.context,
        args.cost_mode
    )
    
    print("[Refund Policy Service] Generation Logs:")
    for k, v in logs.items():
        print(f"  {k}: {v}")
    
    print(f"[Refund Policy Service] Generated Refund Policy:")
    
    print(refund_policy)

if __name__ == "__main__":
    main() 