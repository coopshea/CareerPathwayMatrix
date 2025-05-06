# CareerPath Navigator: User Guide

This guide walks you through using the CareerPath Navigator MVP to explore career pathways, analyze skills, and create personalized roadmaps.

## Getting Started

1. Launch the application using Streamlit:
   ```
   streamlit run app.py
   ```

2. The application opens to the main dashboard with multiple tabs for different features.

## Main Features

### Career Matrix Visualization

1. **Navigate to the main dashboard tab**
2. **Explore the 2x2 matrix**:
   - Each dot represents a career pathway
   - Hover over dots to see basic information
   - Click on dots to view detailed pathway information
3. **Use the sidebar filters** to customize the visualization:
   - Select different metrics for X and Y axes
   - Filter pathways by category
   - Adjust other display options

### Personalized Recommendations

1. **Navigate to the Recommendations tab**
2. **Set your preferences**:
   - Use sliders to indicate your preferred range for each metric
   - Adjust importance weights to prioritize factors that matter most to you
3. **View recommended pathways** based on your preferences
4. **Explore match explanations** to understand why specific pathways are recommended

### Job Posting Analysis

1. **Navigate to the Job Postings tab**
2. **Add job postings** in one of two ways:
   - Paste a job description directly into the text area
   - Enter a URL to scrape job details automatically
3. **Click "Analyze Job Posting"** to extract key information
4. **Review the analysis** and click "Add to Pathways" to convert the job to a comparable pathway
5. **Return to the main visualization** to see your job posting (marked with a gold star) in context

### Skills Profile Management

1. **Navigate to the Skills Graph tab**
2. **Upload your resume** (PDF, DOCX, or TXT format)
3. **Click "Extract Skills from Resume"** to automatically identify and rate your skills
4. **Manually edit your skills profile**:
   - Adjust skill ratings using sliders
   - Edit experience descriptions
   - Add new skills using the "Add Skill Manually" section
   - Remove skills you no longer want to include
5. **Skills are automatically saved** to the database when changes are made

### Skill Visualization and Gap Analysis

1. **Navigate to the Skill Graph tab**
2. **Select the "Skill Graph" sub-tab**
3. **Use sidebar filters** to customize the visualization:
   - Filter by skill type (Required, Preferred, All)
   - Filter by job category
   - Adjust the number of job skills to include
4. **Explore the interactive graph**:
   - Green nodes: Your skills
   - Orange nodes: Skills required in job postings
   - Purple nodes: Your skills that are also required in jobs
   - Node size indicates skill level or job demand
5. **Review the Skill Gap Analysis** section to see which high-demand skills you're missing

### Skill Roadmaps

1. **Navigate to the Skill Graph tab**
2. **Select the "Skill Roadmaps" sub-tab**
3. **Choose a skill** you want to learn from the dropdown
4. **Review the personalized roadmap** with steps to acquire the skill
5. **Click "Add This Roadmap to My Profile"** to save it for future reference

### Project Portfolio

1. **Navigate to the Skill Graph tab**
2. **Select the "My Projects" sub-tab**
3. **Add new projects**:
   - Enter a project name, description, and optional link
   - Click "Add Project" to analyze and add it to your portfolio
4. **View project details and associated skills**
5. **Note that your skills profile is automatically updated** based on projects you add

## Tips for Effective Use

- **Start with resume upload** to quickly build an initial skills profile
- **Add real job postings** that interest you to see how they compare to other options
- **Regularly update your skills and projects** to keep your profile current
- **Experiment with different preference settings** to discover diverse career options
- **Focus on acquiring high-demand skills** identified in the gap analysis
- **Use the roadmaps as structured learning guides** to systematically build your capabilities

## Troubleshooting

- If **OpenAI integration is not working**, ensure you have set the OPENAI_API_KEY environment variable
- If **job posting analysis fails**, try simplifying the text or providing a cleaner URL
- If **visualization doesn't appear**, try refreshing the page or adjusting filters
- If **database errors occur**, check the database connection settings in the configuration

## Data Privacy

- Your skills data and projects are stored in the local PostgreSQL database
- Resume contents are processed but not stored in their entirety
- No data is shared with external services except for AI processing (with OpenAI)

---

For more detailed information about the platform's vision and capabilities, please refer to the README.md file.