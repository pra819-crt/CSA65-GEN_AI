# ---------------------------------------------------------
# Sentiment Analysis Using an LLM API
# Generative AI Assessment - Question 1
# ---------------------------------------------------------

import os
from google import genai


# ---------------------------------------------------------
# Function 1: Create Gemini Client
# ---------------------------------------------------------
def create_client():
    """
    Creates and returns a Gemini API client.

    The API key is read from the GEMINI_API_KEY
    environment variable.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Gemini API key was not found.")

    return genai.Client(api_key=api_key)


# ---------------------------------------------------------
# Function 2: Validate User Review
# ---------------------------------------------------------
def validate_review(review):
    """
    Checks whether the user entered a valid review.
    """

    if not review.strip():
        return False

    return True


# ---------------------------------------------------------
# Function 3: Analyze Sentiment
# ---------------------------------------------------------
def analyze_sentiment(client, review):
    """
    Sends the review to Gemini and asks the LLM
    to classify the sentiment as Positive, Negative,
    or Neutral with a short explanation.
    """

    prompt = f"""
You are a sentiment analysis assistant.

Analyze the following user review.

Classify the sentiment into ONLY ONE of these categories:
Positive
Negative
Neutral

Then provide a short explanation.

Return the answer in exactly this format:

Sentiment: <Positive/Negative/Neutral>
Explanation: <short explanation>

User Review:
{review}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text


# ---------------------------------------------------------
# Main Program
# ---------------------------------------------------------
def main():

    print("=" * 60)
    print("       SENTIMENT ANALYSIS USING GEMINI LLM")
    print("=" * 60)

    # Create Gemini client
    try:
        client = create_client()

    except ValueError as error:
        print("\nERROR:", error)
        print("Please configure the GEMINI_API_KEY.")
        return

    # Get review from user
    review = input("\nEnter your review: ").strip()

    # Validate review
    if not validate_review(review):
        print("\nERROR: Review cannot be empty.")
        print("Please enter a valid review.")
        return

    print("\nAnalyzing sentiment...")
    print("Please wait...\n")

    # Call Gemini API
    try:
        result = analyze_sentiment(client, review)

        print("-" * 60)
        print("RESULT")
        print("-" * 60)
        print(result)
        print("-" * 60)

    except Exception as error:
        print("\nERROR: Unable to analyze the review.")
        print("Reason:", error)
        print("Please check your internet connection and API key.")


# ---------------------------------------------------------
# Program Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    main()