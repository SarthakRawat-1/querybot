# Enhanced QueryBot - AI-Powered Data Analysis Agent

A sophisticated LangGraph-based agent that transforms natural language questions into comprehensive data analysis, complete with insights, visualizations, and intelligent routing.

## 🚀 Key Features

### 🧠 Intelligent Question Classification
- **Smart Routing**: Automatically classifies questions as chart, table, general, or irrelevant
- **Context-Aware Processing**: Different workflows for different question types
- **Polite Handling**: Professional responses for non-data-related questions

### 📊 Advanced Data Visualization
- **Smart Chart Selection**: AI-powered visualization recommendations based on data analysis
- **Seaborn & Matplotlib**: Professional-quality charts with modern styling
- **Multiple Chart Types**: Line, bar, scatter, pie, heatmap, box plots, histograms
- **Data-Driven Decisions**: Analyzes data structure, patterns, and question intent

### 💡 Automatic Insights Generation
- **Data Analyst AI**: Generates key insights with statistical analysis
- **Narrative Explanations**: Story-like data interpretations
- **Pattern Recognition**: Identifies trends, anomalies, and correlations
- **Professional Format**: Emoji-enhanced, bullet-pointed insights

### 📋 Smart Table Formatting
- **Readable Tables**: Clean, structured data presentation
- **Pandas Integration**: Advanced data manipulation capabilities
- **Performance Optimized**: Handles large datasets efficiently

### 🔄 Complex Graph Architecture
- **Conditional Routing**: LangGraph with intelligent decision points
- **Dynamic Processing**: Skips unnecessary steps based on question type
- **Error Resilience**: Graceful failure handling throughout workflow
- **Resource Efficiency**: Only processes what's needed

## 📈 Example Outputs

### Chart Question
```
📤 Question: "Show me sales by region"

📋 Response:
Based on your question 'Show me sales by region', I analyzed the regional sales data.

📖 Analysis: Sales data reveals strong performance in western markets, 
likely driven by higher population density and marketing investments.

📊 Key Insights:
• West region dominates with 34% of total sales ($2.3M)
• East region follows with 28% ($1.9M) 
• Sales dropped 12% in February across all regions
• No strong correlation between region size and revenue

📊 Chart generated successfully (base64 encoded)
```

### Table Question
```
📤 Question: "List all high-value customers"

📋 Data Table:
Customer_Name    | Order_Value | Order_Date  
-----------------|-------------|-------------
Acme Corp        | $4,500      | 2024-11-01
TechStart Inc    | $3,200      | 2024-11-05
[... 15 rows total]

📊 Key Insights:
• 15 customers exceed $1000 threshold (12% of customer base)
• Average high-value order: $1,847
• Top customer: Acme Corp with $4,500 order
```

## 🛠️ Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd QueryBot/langgraph_agent

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Add your Google Gemini API key to .env
```

### Basic Usage
```python
from querybot_agent.agent import QueryBotAgent

# Initialize the agent
agent = QueryBotAgent()

# Ask questions and get comprehensive analysis
result = agent.query("Show me sales trends over time", "your-database-uuid")

# Access rich response components
print(result["answer"])           # Comprehensive answer with narrative
print(result["insights"])         # Key insights with emojis
print(result["data_narrative"])   # Story explanation
print(result["formatted_table"])  # Table if applicable
print(result["chart_image_base64"]) # Chart as base64 data
```

### Response Structure
```python
{
    "answer": "Comprehensive response with narrative and insights",
    "insights": "📊 Key Insights: • Point 1 • Point 2 • Point 3",
    "data_narrative": "Story-like explanation of data patterns",
    "formatted_table": "Readable table format (if applicable)", 
    "chart_image_base64": "iVBORw0KGgoAAAANSUhEUgAA...base64data...",
    "visualization": "bar|line|scatter|pie|etc",
    "visualization_reason": "Explanation for chart choice",
    "chart_generation_error": None,
    "insights_error": None
}
```

## 🎯 Advanced Features

### Visualization Intelligence
- **Data Structure Analysis**: Automatically detects numeric vs categorical data
- **Pattern Recognition**: Identifies temporal, correlational, and distributional patterns
- **Question Intent**: Analyzes question keywords for visualization hints
- **Seaborn Integration**: Uses appropriate seaborn functions for optimal charts

### Processing Workflow
```
START → classify_question → is_relevant?
  ├─ irrelevant → polite_redirect → END  
  └─ relevant → SQL_processing → should_generate_chart?
                                 ├─ yes → enhanced_chart
                                 └─ no → skip_chart
                                 ↓
                               should_format_table?
                                 ├─ yes → format_table
                                 └─ no → skip_table  
                                 ↓
                               generate_insights → finalize → END
```

### Chart Types Supported
- **Line Charts**: Time series, trends, continuous data
- **Bar Charts**: Categorical comparisons, rankings
- **Scatter Plots**: Relationships, correlations
- **Pie Charts**: Proportions, parts-of-whole
- **Heatmaps**: Correlation matrices, pivot data
- **Box Plots**: Distribution analysis
- **Histograms**: Single variable distributions

## 🔧 Technical Architecture

### Core Components
- `question_classifier.py`: AI-powered question analysis and routing
- `insights_generator.py`: Data insights and narrative generation
- `response_finalizer.py`: Output combination and error handling
- `sql_agent.py`: Enhanced SQL processing with smart visualization
- `chart_generator.py`: Advanced chart creation with seaborn/matplotlib

### Dependencies
- **LangGraph**: Complex workflow orchestration
- **LangChain**: LLM integration and prompting
- **Pandas**: Data manipulation and analysis
- **Seaborn/Matplotlib**: Professional data visualization
- **Google Gemini**: Language model for analysis and insights

## 🎉 Benefits

✅ **Acts like a data analyst**: Provides insights, not just charts  
✅ **Intelligent routing**: Processes questions appropriately  
✅ **Comprehensive outputs**: Rich, multi-faceted responses  
✅ **Professional handling**: Polite management of irrelevant queries  
✅ **Flexible architecture**: Easy to extend and maintain  
✅ **Error resilient**: Graceful failure handling  
✅ **Performance optimized**: Conditional processing saves resources  

## 🧪 Testing

```bash
# Run comprehensive tests
uv run python test_enhanced_querybot.py

# See example usage
uv run python enhanced_example_usage.py
```

## 📝 License

[Add your license information here]

---

*Enhanced QueryBot provides a complete data analysis experience, combining LangGraph's conditional routing with intelligent insights generation to deliver professional, analyst-quality responses.*