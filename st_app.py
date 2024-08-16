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

print("base url", base_url)

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
            goal="Analyze OpenAPI spec {data} for API structure and create a comprehensive understanding of the API structure",
            backstory="Expert API architect with 20 years of experience.You are a seasoned API architect experienced in designing and documenting APIs",
            verbose=True,
            llm=llm,
            allow_delegation=False
        )

        user_request_interpreter_agent = Agent(
            role="Request Interpreter",
            goal="""Interpret user request {request}, identify the method, parameters, and match them to appropriate API endpoints based on 
                    the OpenAPI specification.""",
            backstory="""NLP and API integration expert with 10 years of experience. you excel at translating user requests into 
                        structured data.""",
            tools=[unified_endpoint_connector],
            verbose=True,
            llm=llm,
            allow_delegation=False
        )

        api_call_agent = Agent(
            role="API Caller",
            goal="To efficiently and accurately interact with various API endpoints using the base url {base_url}. and handle error gracefully ",
            backstory="""As a seasoned API Integration Specialist, I have extensive experience in working with diverse APIs across 
                        multiple domains. My expertise lies in understanding API structures, authentication methods, and data formats.""",
            tools=[unified_endpoint_connector],
            verbose=True,
            llm=llm,
            allow_delegation=False
        )

        # Define tasks with focused outputs
        analyze_openapi_task = Task(
            description="Analyze OpenAPI JSON data. Understand all endpoints, their purposes, parameters, request bodies, and response structures.",
            expected_output = "A comprehensive breakdown of the API structure, including List of all available endpoints with HTTP methods and purpose of each end point.",
            agent=openapi_analyst_agent
        )

        interpret_user_request_task = Task(
            description="Listen to user request {request} Identify the Method, params and determine which API endpoint(s) would be most appropriate to fulfill their needs.",
            expected_output = "For each user request, A clear interpretation of the user intention and Identification of most appropriate API endpoint(s) to fullfill the request.",
            agent=user_request_interpreter_agent
        )

        api_call_task = Task(
            description="""analyze the output of previous Agents and Tasks, create a dynamic url based on params and appropriate endpoint.. 
                    Then, make a call to API. 
                    Ensure that errors are handled gracefully and return clear messages like if url is not found then return error: 404""",
            expected_output = "A clear message indicating the result of the API call, including any errors message if applicable",
            agent=api_call_agent
        )

        # Create crew with parallel processing
        crew = Crew(
            agents=[openapi_analyst_agent, user_request_interpreter_agent, api_call_agent],
            tasks=[analyze_openapi_task, interpret_user_request_task, api_call_task],
            process=Process.sequential,
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