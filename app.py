import streamlit as st
import os

try:
    from event_llm_core import generate_titles, generate_description, fuzzy_correct
except Exception as e:
    st.error("**Configuration Error**")
    st.error("OpenAI API key is missing or invalid.")
    st.markdown("""
    ### How to fix this:
    
    **For Streamlit Cloud:**
    1. Go to your app settings
    2. Click on "Secrets" 
    3. Add: `OPENAI_API_KEY = "your_api_key_here"`
    
    **For local development:**
    1. Create a `.env` file
    2. Add: `OPENAI_API_KEY=your_api_key_here`
    
    **Get your API key:**
    - Visit: https://platform.openai.com/api-keys
    - Create a new secret key
    - Copy and paste it in the configuration above
    """)
    st.stop()

st.set_page_config(page_title="EC - Title & Desc Gen", layout="wide")

st.markdown("""
<style>
section.main > div:first-child {background: #f8fafc; border-radius: 12px; padding: 2rem 2rem 1rem 2rem; box-shadow: 0 2px 8px #0001;}
.stSelectbox [data-baseweb="select"] > div {border-radius: 8px;}
.stButton > button {border-radius: 8px; background: #2563eb; color: #fff; font-weight: 600;}
.stSlider > div {color: #2563eb;}
.stTextInput > div > input {border-radius: 8px;}
.stTextArea > div > textarea {border-radius: 8px;}

.generated-title {
    background: var(--background-color) !important; 
    padding: 1rem !important; 
    border-radius: 8px !important; 
    margin: 0.8rem 0 !important; 
    border: 2px solid #2563eb !important; 
    color: var(--text-color) !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
}
@media (prefers-color-scheme: light) {
    .generated-title {
        background: #ffffff !important;
        color: #1a1a1a !important;
        border: 2px solid #2563eb !important;
    }
}
@media (prefers-color-scheme: dark) {
    .generated-title {
        background: #2d3748 !important;
        color: #ffffff !important;
        border: 2px solid #4299e1 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
    }
}

.optimization-tip {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #4299e1;
}
</style>
""", unsafe_allow_html=True)

st.title("EC - Title & Desc Gen")
st.write("Generate event titles and descriptions with advanced prompt engineering.")

def get_optimization_tip(category, event_type, tone):
    tips = {
        ("Technology", "Conference", "Professional"): "Pro tip: Technology conferences perform best with titles that emphasize innovation, future trends, and networking opportunities.",
        ("Business", "Workshop", "Formal"): "Pro tip: Formal business workshops should highlight specific skills, ROI, and executive-level insights.",
        ("Education", "Seminar", "Creative"): "Pro tip: Creative education seminars work best when titles suggest transformation and hands-on learning.",
    }
    
    key = (category, event_type, tone)
    if key in tips:
        return tips[key]
    
    return f"Pro tip: {tone} {event_type}s in {category} perform best when titles clearly communicate the unique value and target outcome."

def suggest_optimal_settings(category, event_type):
    suggestions = {
        ("Technology", "Conference"): {"tone": "Professional", "titles": 5, "desc_length": 1200},
        ("Technology", "Workshop"): {"tone": "Creative", "titles": 4, "desc_length": 800},
        ("Business", "Seminar"): {"tone": "Formal", "titles": 3, "desc_length": 1000},
        ("Education", "Conference"): {"tone": "Innovative", "titles": 5, "desc_length": 1400},
        ("Health", "Workshop"): {"tone": "Friendly", "titles": 4, "desc_length": 900},
    }
    
    key = (category, event_type)
    return suggestions.get(key, {"tone": "Professional", "titles": 3, "desc_length": 800})

if 'generated_titles' not in st.session_state:
    st.session_state.generated_titles = []
if 'selected_title' not in st.session_state:
    st.session_state.selected_title = ""
if 'custom_title' not in st.session_state:
    st.session_state.custom_title = ""
if 'final_title' not in st.session_state:
    st.session_state.final_title = ""
if 'description' not in st.session_state:
    st.session_state.description = ""
if 'title_logs' not in st.session_state:
    st.session_state.title_logs = None
if 'desc_logs' not in st.session_state:
    st.session_state.desc_logs = None
if 'show_title_logs' not in st.session_state:
    st.session_state.show_title_logs = False
if 'show_desc_logs' not in st.session_state:
    st.session_state.show_desc_logs = False

category_options = ["Select event category", "Technology", "Business", "Education", "Health", "Entertainment", "Sports", "Arts & Culture", "Other"]
event_type_options = ["Select event type", "Conference", "Workshop", "Seminar", "Webinar", "Festival", "Exhibition", "Meetup", "Other"]
tone_options = ["Select tone of event", "Professional", "Casual", "Formal", "Creative", "Premium", "Innovative", "Friendly", "Corporate", "Other"]



st.markdown("## Title Generation")

col1, col2, col3 = st.columns(3)

with col1:
    title_category = st.selectbox("Category for Titles", category_options, index=0, key="title_category")
    if title_category == "Other":
        custom_title_category = st.text_input("Custom category", key="custom_title_category")
        if custom_title_category:
            suggestion = fuzzy_correct(custom_title_category, category_options[1:-1])
            if suggestion != custom_title_category:
                st.info(f"Did you mean: {suggestion}?")

with col2:
    title_event_type = st.selectbox("Event Type for Titles", event_type_options, index=0, key="title_event_type")
    if title_event_type == "Other":
        custom_title_event_type = st.text_input("Custom event type", key="custom_title_event_type")
        if custom_title_event_type:
            suggestion = fuzzy_correct(custom_title_event_type, event_type_options[1:-1])
            if suggestion != custom_title_event_type:
                st.info(f"Did you mean: {suggestion}?")

with col3:
    title_tone = st.selectbox("Tone for Titles", tone_options, index=0, key="title_tone")
    if title_tone == "Other":
        custom_title_tone = st.text_input("Custom tone", key="custom_title_tone")
        if custom_title_tone:
            suggestion = fuzzy_correct(custom_title_tone, tone_options[1:-1])
            if suggestion != custom_title_tone:
                st.info(f"Did you mean: {suggestion}?")

if title_category != "Select event category" and title_event_type != "Select event type":
    optimal = suggest_optimal_settings(title_category, title_event_type)
    st.markdown(f'<div class="optimization-tip">Optimization Suggestion: For {title_category} {title_event_type}s, consider using {optimal["tone"]} tone with {optimal["titles"]} titles for best results.</div>', unsafe_allow_html=True)

col_cost, col_test = st.columns(2)
with col_cost:
    cost_mode = st.selectbox("Cost Optimization", ["balanced", "economy", "premium"], 
                            help="Economy: Lower cost, basic quality | Balanced: Good cost/quality ratio | Premium: Higher cost, best quality")
with col_test:
    if st.button("Run A/B Tests", help="Run comprehensive testing of all input combinations"):
        with st.spinner("Running comprehensive tests..."):
            from event_llm_core import run_comprehensive_tests
            test_results = run_comprehensive_tests()
            st.success(f"Tests completed: {len([r for r in test_results if 'PASS' in r])} passed, {len([r for r in test_results if 'FAIL' in r])} failed")
            with st.expander("View Test Results"):
                for result in test_results:
                    if "PASS" in result:
                        st.success(result)
                    else:
                        st.error(result)

with st.form("title_form"):
    col4, col5 = st.columns(2)
    with col4:
        num_titles = st.slider("Number of Titles (max 5)", min_value=1, max_value=5, value=3)
    with col5:
        title_context = st.text_input("Context for Titles (optional)", placeholder="e.g., Focus on AI and machine learning trends")
    
    generate_titles_btn = st.form_submit_button("Generate Titles", use_container_width=True)

if generate_titles_btn:
    if title_category == "Select event category":
        st.error("Please select a category for title generation.")
    elif title_event_type == "Select event type":
        st.error("Please select an event type for title generation.")
    elif title_tone == "Select tone of event":
        st.error("Please select a tone for title generation.")
    else:
        final_title_category = custom_title_category if title_category == "Other" and 'custom_title_category' in locals() and custom_title_category else title_category
        final_title_event_type = custom_title_event_type if title_event_type == "Other" and 'custom_title_event_type' in locals() and custom_title_event_type else title_event_type
        final_title_tone = custom_title_tone if title_tone == "Other" and 'custom_title_tone' in locals() and custom_title_tone else title_tone
        
        if title_category != "Select event category" and title_event_type != "Select event type" and title_tone != "Select tone of event":
            tip = get_optimization_tip(final_title_category, final_title_event_type, final_title_tone)
            st.info(tip)
        
        cost_info = {"economy": "low cost, basic quality", "balanced": "optimal cost/quality", "premium": "high cost, best quality"}
        st.info(f"Using {cost_mode} mode: {cost_info[cost_mode]}")
        
        with st.spinner("Generating high-quality titles using advanced prompt engineering..."):
            titles, logs = generate_titles(
                final_title_category, 
                final_title_event_type, 
                final_title_tone, 
                num_titles, 
                title_context if title_context else None,
                cost_mode
            )
            st.session_state.generated_titles = titles
            st.session_state.title_logs = logs
            st.session_state.selected_title = ""
            st.session_state.custom_title = ""
            st.session_state.final_title = ""

if st.session_state.generated_titles:
    st.markdown("### Generated Titles:")
    for i, title in enumerate(st.session_state.generated_titles):
        st.markdown(f'<div class="generated-title"><span style="font-weight: 600 !important;">{i+1}. {title}</span></div>', unsafe_allow_html=True)
    # Title analytics button and display (only in main area)
    if st.session_state.title_logs:
        if st.button("View Title Generation Analytics", key="title_analytics_btn", use_container_width=True):
            st.markdown("### Title Generation Analytics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Prompt Tokens", st.session_state.title_logs['Prompt tokens'])
                st.metric("Total Tokens", st.session_state.title_logs['Total tokens'])
            with col2:
                st.metric("Completion Tokens", st.session_state.title_logs['Completion tokens'])
                st.metric("Generation Time", f"{st.session_state.title_logs['Time taken (s)']}s")
            st.metric("Cost", st.session_state.title_logs['Estimated cost ($)'])
            if st.session_state.generated_titles:
                total_title_chars = sum(len(title) for title in st.session_state.generated_titles)
                avg_title_length = total_title_chars / len(st.session_state.generated_titles)
                st.metric("Total Characters Generated", total_title_chars)
                st.metric("Average Title Length", f"{avg_title_length:.1f} chars")
            st.markdown(f"**Model Used:** {st.session_state.title_logs.get('Model', 'gpt-3.5-turbo')}")
            with st.expander("Show Prompt Preview"):
                st.markdown(f"""
**System Prompt:**
```
{st.session_state.title_logs.get('System prompt', '')}
```
**User Prompt:**
```
{st.session_state.title_logs.get('User prompt', '')}
```
""", unsafe_allow_html=True)
    
    st.markdown("### Select or Create Your Title:")
    
    title_options = ["Select a title option..."] + [f"Use: {title}" for title in st.session_state.generated_titles] + ["Write my own custom title"]
    
    title_choice = st.selectbox("Choose how you want to proceed:", title_options, key="title_choice")
    
    final_title_input = ""
    
    if title_choice.startswith("Use: "):
        selected_generated_title = title_choice[5:]
        st.info(f"Selected title: **{selected_generated_title}**")
        
        edit_option = st.radio("What would you like to do?", 
                              ["Use this title as-is", "Edit this title"], 
                              key="edit_option")
        
        if edit_option == "Use this title as-is":
            final_title_input = selected_generated_title
            st.session_state.final_title = selected_generated_title
            st.success(f"Final title: **{selected_generated_title}**")
        else:
            edited_title = st.text_input("Edit the title:", 
                                       value=selected_generated_title, 
                                       key="edit_selected_title")
            if edited_title and edited_title != selected_generated_title:
                final_title_input = edited_title
                st.session_state.final_title = edited_title
                st.success(f"Final edited title: **{edited_title}**")
            elif edited_title:
                final_title_input = edited_title
                st.session_state.final_title = edited_title
    
    elif title_choice == "Write my own custom title":
        custom_title = st.text_input("Write your own title:", 
                                   placeholder="Enter your custom event title...", 
                                   key="custom_title_input")
        if custom_title:
            all_generated_titles = st.session_state.generated_titles
            suggestion = fuzzy_correct(custom_title, all_generated_titles)
            if suggestion != custom_title and suggestion in all_generated_titles:
                st.info(f"Did you mean one of our generated titles: **{suggestion}**?")
                use_suggestion = st.checkbox(f"Use '{suggestion}' instead?", key="use_fuzzy_suggestion")
                if use_suggestion:
                    final_title_input = suggestion
                    st.session_state.final_title = suggestion
                    st.success(f"Final title (suggested): **{suggestion}**")
                else:
                    final_title_input = custom_title
                    st.session_state.final_title = custom_title
                    st.success(f"Final custom title: **{custom_title}**")
            else:
                final_title_input = custom_title
                st.session_state.final_title = custom_title
                st.success(f"Final custom title: **{custom_title}**")
    
    if not final_title_input and title_choice != "Select a title option...":
        st.warning("Please complete your title selection to proceed to description generation.")

if st.session_state.final_title:
    st.markdown("## Description Generation")
    
    with st.form("description_form"):
        st.write(f"**Generating description for:** {st.session_state.final_title}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            desc_category = st.selectbox("Category for Description", category_options, index=0, key="desc_category")
            if desc_category == "Other":
                custom_desc_category = st.text_input("Custom category", key="custom_desc_category")
                if custom_desc_category:
                    suggestion = fuzzy_correct(custom_desc_category, category_options[1:-1])
                    if suggestion != custom_desc_category:
                        st.info(f"Did you mean: {suggestion}?")
        
        with col2:
            desc_event_type = st.selectbox("Event Type for Description", event_type_options, index=0, key="desc_event_type")
            if desc_event_type == "Other":
                custom_desc_event_type = st.text_input("Custom event type", key="custom_desc_event_type")
                if custom_desc_event_type:
                    suggestion = fuzzy_correct(custom_desc_event_type, event_type_options[1:-1])
                    if suggestion != custom_desc_event_type:
                        st.info(f"Did you mean: {suggestion}?")
        
        with col3:
            desc_tone = st.selectbox("Tone for Description", tone_options, index=0, key="desc_tone")
            if desc_tone == "Other":
                custom_desc_tone = st.text_input("Custom tone", key="custom_desc_tone")
                if custom_desc_tone:
                    suggestion = fuzzy_correct(custom_desc_tone, tone_options[1:-1])
                    if suggestion != custom_desc_tone:
                        st.info(f"Did you mean: {suggestion}?")
        
        col4, col5, col6 = st.columns(3)
        with col4:
            max_chars = st.slider("Description Length (characters)", min_value=100, max_value=2000, value=800)
        with col5:
            desc_context = st.text_input("Context for Description (optional)", placeholder="e.g., Emphasize networking opportunities and practical takeaways")
        with col6:
            desc_cost_mode = st.selectbox("Cost Mode", ["balanced", "economy", "premium"], key="desc_cost_mode")
        
        generate_desc_btn = st.form_submit_button("Generate Description", use_container_width=True)

    if generate_desc_btn:
        if desc_category == "Select event category":
            st.error("Please select a category for description generation.")
        elif desc_event_type == "Select event type":
            st.error("Please select an event type for description generation.")
        elif desc_tone == "Select tone of event":
            st.error("Please select a tone for description generation.")
        else:
            final_desc_category = custom_desc_category if desc_category == "Other" and 'custom_desc_category' in locals() and custom_desc_category else desc_category
            final_desc_event_type = custom_desc_event_type if desc_event_type == "Other" and 'custom_desc_event_type' in locals() and custom_desc_event_type else desc_event_type
            final_desc_tone = custom_desc_tone if desc_tone == "Other" and 'custom_desc_tone' in locals() and custom_desc_tone else desc_tone
            
            desc_cost_info = {"economy": "low cost, basic quality", "balanced": "optimal cost/quality", "premium": "high cost, best quality"}
            st.info(f"Using {desc_cost_mode} mode: {desc_cost_info[desc_cost_mode]}")
            
            with st.spinner("Generating compelling description using advanced copywriting techniques..."):
                description, logs = generate_description(
                    st.session_state.final_title,
                    final_desc_category,
                    final_desc_event_type, 
                    final_desc_tone,
                    desc_context if desc_context else None,
                    max_chars,
                    desc_cost_mode
                )
                st.session_state.description = description
                st.session_state.desc_logs = logs

if st.session_state.description:
    st.markdown("### Generated Description:")
    st.markdown(f'<div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #28a745; color: #333;">{st.session_state.description}</div>', unsafe_allow_html=True)
    st.info(f"Description length: {len(st.session_state.description)} characters")

    # Copy-to-Clipboard button
    st.code(st.session_state.description, language=None)
    st.button("Copy Description", on_click=lambda: st.session_state.update({'_clipboard': st.session_state.description}), key="copy_desc_btn")

    # Download as TXT
    st.download_button("Download as .txt", st.session_state.description, file_name="event_description.txt", mime="text/plain", key="download_desc_btn")

    # Paraphrase button
    if st.button("Paraphrase Description", key="paraphrase_desc_btn"):
        description, logs = generate_description(
            st.session_state.final_title,
            st.session_state.desc_logs.get('category', ''),
            st.session_state.desc_logs.get('event_type', ''),
            st.session_state.desc_logs.get('tone', ''),
            st.session_state.desc_logs.get('context', None),
            st.session_state.desc_logs.get('max_chars', 2000),
            st.session_state.desc_logs.get('Cost mode', 'balanced')
        )
        st.session_state.description = description
        st.session_state.desc_logs = logs

    # Character utilization progress bar
    if st.session_state.desc_logs:
        utilization = len(st.session_state.description) / st.session_state.desc_logs.get('max_chars', 2000)
        st.progress(min(int(utilization*100), 100), text=f"Character Utilization: {len(st.session_state.description)}/{st.session_state.desc_logs.get('max_chars', 2000)}")
        if utilization >= 0.95:
            st.success("✔️ Description is within 95%+ of requested length.")

    if st.session_state.desc_logs and st.session_state.desc_logs.get("Shorter than requested"):
        st.warning("Description is shorter than requested. Try increasing the length or re-generating.")
        if st.button("Regenerate Description", key="regenerate_desc_btn"):
            description, logs = generate_description(
                st.session_state.final_title,
                st.session_state.desc_logs.get('category', ''),
                st.session_state.desc_logs.get('event_type', ''),
                st.session_state.desc_logs.get('tone', ''),
                st.session_state.desc_logs.get('context', None),
                st.session_state.desc_logs.get('max_chars', 2000),
                st.session_state.desc_logs.get('Cost mode', 'balanced')
            )
            st.session_state.description = description
            st.session_state.desc_logs = logs

    # Description analytics button and display (only in main area)
    if st.session_state.desc_logs:
        st.markdown(f"**Model Used:** {st.session_state.desc_logs.get('model', 'gpt-3.5-turbo')}")
        with st.expander("Show Prompt Preview"):
            st.markdown(f"""
**System Prompt:**
```
{st.session_state.desc_logs.get('system_prompt', '')}
```
**User Prompt:**
```
{st.session_state.desc_logs.get('user_prompt', '')}
```
""", unsafe_allow_html=True)
        if st.button("View Description Generation Analytics", key="desc_analytics_btn", use_container_width=True):
            st.markdown("### Description Generation Analytics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Prompt Tokens", st.session_state.desc_logs['Prompt tokens'])
                st.metric("Total Tokens", st.session_state.desc_logs['Total tokens'])
            with col2:
                st.metric("Completion Tokens", st.session_state.desc_logs['Completion tokens'])
                st.metric("Generation Time", f"{st.session_state.desc_logs['Time taken (s)']}s")
            st.metric("Cost", st.session_state.desc_logs['Estimated cost ($)'])
            if st.session_state.description:
                desc_length = len(st.session_state.description)
                words = len(st.session_state.description.split())
                char_per_token_ratio = desc_length / st.session_state.desc_logs['Completion tokens'] if st.session_state.desc_logs['Completion tokens'] > 0 else 0
                col3, col4 = st.columns(2)
                with col3:
                    st.metric("Characters Generated", desc_length)
                    st.metric("Word Count", words)
                with col4:
                    st.metric("Chars per Token", f"{char_per_token_ratio:.2f}")
                    efficiency = (desc_length / st.session_state.desc_logs['Total tokens']) if st.session_state.desc_logs['Total tokens'] > 0 else 0
                    st.metric("Overall Efficiency", f"{efficiency:.2f} chars/token")

st.markdown("---")
st.markdown("**Ready for Flask integration:** This system supports independent title and description generation with separate parameters.")