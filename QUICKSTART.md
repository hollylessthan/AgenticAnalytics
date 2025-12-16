# Quick Start Guide

Get started with Agentic Analytics in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- OpenAI API key

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure API Key

Create a `.env` file in the project root:

```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

Or set it as an environment variable:

```bash
export OPENAI_API_KEY=your_api_key_here
```

## Step 3: Run the Application

```bash
streamlit run app.py
```

## Step 4: Use the Chatbot

1. Open your browser to `http://localhost:8501`
2. Enter your API key in the sidebar (if not set in .env)
3. Click "🔄 Initialize System"
4. Start asking questions!

## Example Questions

### Data Retrieval
- "What products do we have?"
- "Show me all sales data"
- "List the top 5 products by revenue"

### Analysis
- "What are the total sales by product?"
- "Calculate the average price by category"
- "Which product has the highest stock?"

### Visualization
- "Create a bar chart of sales by product"
- "Show me a pie chart of revenue by category"
- "Visualize the price distribution"

### Complex Queries
- "Show me sales trends and create a line chart"
- "Analyze which products are selling best and visualize it"
- "Compare products by price and show a scatter plot"

## Troubleshooting

### "OpenAI API key not found"
Make sure you've set the `OPENAI_API_KEY` in your `.env` file or entered it in the sidebar.

### "Database not found"
The system will automatically create a sample database on first run. If you see this error, click "Initialize System" in the sidebar.

### "Import errors"
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Next Steps

- Explore the [full README](README.md) for detailed documentation
- Learn about the [architecture](README.md#architecture)
- Try adding your own database by modifying the `DATABASE_PATH` in `.env`
- Customize agents in the `agentic_analytics/agents/` directory

## Need Help?

Open an issue on GitHub for support!
