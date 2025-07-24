from event_llm_core import generate_flyer_image, generate_banner_image
import argparse

def main():
    parser = argparse.ArgumentParser(description="Event Flyer/Banner Generation Service")
    parser.add_argument('--title', required=True, help='Event title')
    parser.add_argument('--description', required=True, help='Event description')
    parser.add_argument('--category', required=True, help='Event category')
    parser.add_argument('--event_type', required=True, help='Event type')
    parser.add_argument('--tone', required=True, help='Tone of the event')
    parser.add_argument('--visual_type', choices=['flyer', 'banner'], default='flyer', help='Type of visual to generate')
    parser.add_argument('--context', required=False, default=None, help='Optional context')
    parser.add_argument('--cost_mode', choices=['economy', 'balanced', 'premium'], default='balanced', help='Cost/quality mode')
    parser.add_argument('--image_size', default=None, help='Image size (auto-selected based on visual type if not specified)')
    
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
    if not args.visual_type or args.visual_type not in ["flyer", "banner"]:
        errors.append("Visual type must be either 'flyer' or 'banner'")
    
    if errors:
        print("[Flyer/Banner Service] Validation Errors:")
        for error in errors:
            print(f"  • {error}")
        exit(1)
    
    if not args.image_size:
        args.image_size = "1024x1792" if args.visual_type == "flyer" else "1792x1024"
    
    print(f"[Flyer/Banner Service] Generating {args.visual_type}")
    print(f"[Flyer/Banner Service] Title: {args.title}")
    print(f"[Flyer/Banner Service] Description: {args.description}")
    print(f"[Flyer/Banner Service] Category: {args.category}")
    print(f"[Flyer/Banner Service] Event Type: {args.event_type}")
    print(f"[Flyer/Banner Service] Tone: {args.tone}")
    print(f"[Flyer/Banner Service] Visual Type: {args.visual_type}")
    print(f"[Flyer/Banner Service] Context: {args.context}")
    print(f"[Flyer/Banner Service] Cost Mode: {args.cost_mode}")
    print(f"[Flyer/Banner Service] Image Size: {args.image_size}")
    print("-" * 50)
    
    if args.visual_type == "flyer":
        image_url, logs = generate_flyer_image(
            args.title,
            args.description,
            args.category,
            args.event_type,
            args.tone,
            args.context,
            args.cost_mode,
            args.image_size
        )
    else:
        image_url, logs = generate_banner_image(
            args.title,
            args.description,
            args.category,
            args.event_type,
            args.tone,
            args.context,
            args.cost_mode,
            args.image_size
        )
    
    print(f"[Flyer/Banner Service] Generation Logs:")
    for k, v in logs.items():
        print(f"  {k}: {v}")
    print(f"[Flyer/Banner Service] Generated {args.visual_type.title()} Image URL:")
    print(f"  {image_url}")

if __name__ == "__main__":
    main() 