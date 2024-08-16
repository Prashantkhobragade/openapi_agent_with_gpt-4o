import streamlit as st
import json
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from tools.tool import unified_endpoint_connector
from azureai import AzureAI
from appconfig import AppConfig

# Load environment variables
load_dotenv()

# Create instances of AppConfig and AzureAI
config = AppConfig()
azure_ai = AzureAI(config)

# Set page title
st.set_page_config(page_title="SmartAPI Connect")
st.title("🤖 SmartAPI Connect")

# Sidebar for API key and base URL input
st.sidebar.header("Configuration")
base_url = st.sidebar.text_input("Enter Base URL or API URL")

# Store base_url in session state
if 'base_url' not in st.session_state:
    st.session_state['base_url'] = base_url

# File uploader for JSON file
uploaded_file = st.file_uploader("Choose a JSON file", type="json")

if uploaded_file is not None:
    try:
        data = json.loads(uploaded_file.getvalue())
        st.success("JSON file successfully loaded!")
    except json.JSONDecodeError:
        st.error("Invalid JSON file. Please upload a valid JSON file.")
        data = None

    if data:
        # Initialize LLM
        llm = azure_ai.get_client()

        # Define agents with optimized prompts
        openapi_analyst_agent = Agent(
            role="OpenAPI Analyst",
            goal="Analyze OpenAPI spec {data} for API structure",
            backstory="Expert API architect with 20 years of experience.",
            verbose=True,
            llm=llm,
            allow_delegation=False
        )

        user_request_interpreter_agent = Agent(
            role="Request Interpreter",
            goal="Match user request {request} to API endpoints",
            backstory="NLP and API integration expert with 10 years of experience.",
            tools=[unified_endpoint_connector],
            verbose=True,
            llm=llm,
            allow_delegation=False
        )

        api_call_agent = Agent(
            role="API Caller",
            goal="Make API calls using {base_url} and handle errors",
            backstory="Experienced in diverse API integrations.",
            tools=[unified_endpoint_connector],
            verbose=True,
            llm=llm,
            allow_delegation=False
        )

        # Define tasks with focused outputs
        analyze_openapi_task = Task(
            description="Analyze OpenAPI JSON data",
            expected_output = ,
            agent=openapi_analyst_agent
        )

        interpret_user_request_task = Task(
            description="Interpret user request and match to API endpoint",
            agent=user_request_interpreter_agent
        )

        api_call_task = Task(
            description="Make API call and handle response",
            agent=api_call_agent
        )

        # Create crew with parallel processing
        crew = Crew(
            agents=[openapi_analyst_agent, user_request_interpreter_agent, api_call_agent],
            tasks=[analyze_openapi_task, interpret_user_request_task, api_call_task],
            process=Process.parallel,
            verbose=True
        )

        # User input for request
        user_request = st.text_input("Enter your request:")

        if st.button("Process Request"):
            with st.spinner("Processing your request..."):
                try:
                    result = crew.kickoff(inputs={"data": data, "request": user_request, "base_url": st.session_state['base_url']})
                    st.success("Request processed successfully!")
                    with st.expander("View Complete output"):
                        st.write(result)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.write("Please check your inputs and try again.")

else:
    st.info("Please upload a JSON file to begin.")