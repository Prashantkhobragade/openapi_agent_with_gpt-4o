import requests
from crewai_tools import tool

#BASE_URL = "http://localhost:8000"
#base_url = ""

@tool("unified_endpoint_connector")
def unified_endpoint_connector(method: str, endpoint: str, base_url:str, params: dict = None) -> dict:
    """
    Handles GET and DELETE requests to a FastAPI endpoint.

    Args:
        method (str): The HTTP method to use ('GET' or 'DELETE').
        endpoint (str): The API endpoint to target (e.g., '/items/').
        base_url (str): The Base URL of the API.
        params (dict, optional): The parameters to include in the request (for GET) or specify the resource (for DELETE).
        
    Returns:
        dict: The response from the server, parsed into a Python dictionary.
    
    """
    
    
    # Replace placeholders in the endpoint with actual values from params
    if params:
        endpoint = endpoint.format(**params)
    url = f"{base_url}{endpoint}"
    print("base url", base_url)
    print("final url", url)

    try:
        if method.lower() == "get":
            response = requests.get(url, params=params)
        elif method.lower() == "delete":
            response = requests.delete(url, params=params)
        else:
            return {"error": "Invalid method. Use 'GET' or 'DELETE'."}
        
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return {"error": "404: Client Error, url is invalid"}
        else:
            return {"error": str(e)}
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


#BASE URL is Hard coded, need to work on it.