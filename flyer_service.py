from event_llm_core import generate_flyer_image
import argparse

def main():
    parser = argparse.ArgumentParser(description="Event Flyer/Banner Generation Service")
    parser.add_argument('--title', required=True, help='Event title')
    parser.add_argument('--description', required=True, help='Event description')
    parser.add_argument('--category', required=True, help='Event category')
    parser.add_argument('--event_type', required=True, help='Event type')
    parser.add_argument('--tone', required=True, help='Tone of the event')
    parser.add_argument('--context', required=False, default=None, help='Optional context')
    parser.add_argument('--cost_mode', choices=['economy', 'balanced', 'premium'], default='balanced', help='Cost/quality mode')
    args = parser.parse_args()
    print(f"[Flyer Service] Generating flyer/banner image")
    print(f"[Flyer Service] Title: {args.title}")
    print(f"[Flyer Service] Description: {args.description}")
    print(f"[Flyer Service] Category: {args.category}")
    print(f"[Flyer Service] Event Type: {args.event_type}")
    print(f"[Flyer Service] Tone: {args.tone}")
    print(f"[Flyer Service] Context: {args.context}")
    print(f"[Flyer Service] Cost Mode: {args.cost_mode}")
    print("-" * 50)
    image_url, logs = generate_flyer_image(
        args.title,
        args.description,
        args.category,
        args.event_type,
        args.tone,
        args.context,
        args.cost_mode
    )
    print("[Flyer Service] Generation Logs:")
    for k, v in logs.items():
        print(f"  {k}: {v}")
    print(f"[Flyer Service] Generated Flyer/Banner Image URL:")
    print(f"  {image_url}")

if __name__ == "__main__":
    main() 