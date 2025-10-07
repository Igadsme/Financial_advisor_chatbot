# Financial Advisor Chatbot
The bot collects a quick financial profile, computes how much the user can save each month, and returns tailored suggestions.

## Features

- Natural-language understanding for common personal finance intents (budgeting, savings, emergency fund, and investment questions).
- A multi-turn form that captures monthly income, essential expenses, savings goals, and risk tolerance.
- Custom action logic that summarises the user's financial capacity, highlights emergency fund targets, and shares portfolio recommendations that align with the user's risk profile.
- Ready-to-use training configuration, stories, and rules for Rasa 3.x.
- Lightweight CLI for chatting with the trained model.

## Getting Started

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Train the model**

   ```bash
   rasa train
   ```

3. **Start the action server** (new terminal):

   ```bash
   rasa run actions
   ```

4. **Chat with the bot** (optional CLI helper):

   ```bash
   python app.py
   ```

   Type `exit` or `quit` to leave the conversation.

## Project Structure

- `config.yml` – NLU pipeline and dialogue policy configuration.
- `domain.yml` – Intents, entities, slots, responses, and actions available to the assistant.
- `nlu.yml` – Training data for intents and entities.
- `stories.yml` – Example conversations that guide dialogue management.
- `rules.yml` – Deterministic rules for forms, FAQs, and fallbacks.
- `actions.py` – Custom action server logic, including financial plan generation and form validation.
- `app.py` – Simple asynchronous CLI wrapper around the trained Rasa agent.
- `endpoints.yml` – Configuration pointing to the local action server.
- `requirements.txt` – Python dependencies required for training and serving the bot.

## Next Steps

- Expand the NLU dataset with domain-specific questions from your users.
- Enrich the custom action with integrations (e.g., Google Sheets, budgeting APIs) for live data.
- Deploy the assistant using `rasa run` with a channel such as REST, Slack, or Twilio once you are satisfied with local testing.
