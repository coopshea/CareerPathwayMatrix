import pandas as pd
import json
import os
from database import init_and_load_data, test_connection

def load_data():
    """
    Load and prepare the dataset of pathways, metrics, and categories.
    
    Returns:
        tuple: (pathways_dataframe, metrics_info, categories_list)
    """
    # First try to load data from the database
    if test_connection():
        try:
            return init_and_load_data()
        except Exception as e:
            print(f"Error loading data from database: {e}")
            print("Falling back to file-based data...")
    
    # If database loading fails, try using the simpler data file
    use_simpler_data = os.path.exists('simplerData.py')
    
    if use_simpler_data:
        try:
            with open('simplerData.py', 'r') as file:
                simpler_data = eval(file.read())
                metrics_data = simpler_data.get('metrics', {})
                categories = simpler_data.get('categories', [])
                pathways_data = simpler_data.get('pathways', [])
                
                # Convert to DataFrame and return early
                pathways_df = pd.DataFrame(pathways_data)
                return pathways_df, metrics_data, categories
        except Exception as e:
            print(f"Error loading simplerData.py: {e}")
            print("Falling back to default data...")
    
    # Hard-coding the metrics data structure based on the provided sample
    metrics_data = {
        "risk_level": {
            "name": "Risk Level",
            "description": "Probability of failure or significant underperformance",
            "low_label": "Low Risk",
            "high_label": "High Risk",
            "rubric": {
                "1": "Nearly guaranteed returns (tenured government position)",
                "2": "Very low risk (established civil service)",
                "3": "Low risk (established medical specialty)",
                "4": "Below average risk (large company senior role)",
                "5": "Moderate risk (established corporate career path)",
                "6": "Above average risk (early stage startup with funding)",
                "7": "High risk (well-funded startup with product-market fit)",
                "8": "Very high risk (pre-product-market fit startup)",
                "9": "Extremely high risk (moonshot venture)",
                "10": "Extreme risk (pre-seed startup in emerging market)"
            }
        },
        "capital_requirements": {
            "name": "Capital Requirements",
            "description": "Initial and ongoing investment needed",
            "low_label": "Minimal Capital",
            "high_label": "Major Investment",
            "rubric": {
                "1": "No investment (<$1,000)",
                "2": "Minimal investment ($1K-$5K)",
                "3": "Low investment ($5K-$10K)",
                "4": "Below average investment ($10K-$25K)",
                "5": "Moderate investment ($25K-$50K)",
                "6": "Above average investment ($50K-$100K)",
                "7": "Substantial investment ($100K-$200K)",
                "8": "High investment ($200K-$500K)",
                "9": "Very high investment ($500K-$1M)",
                "10": "Major investment (>$1M)"
            }
        },
        "technical_specialization": {
            "name": "Technical Specialization",
            "description": "Depth of technical expertise required",
            "low_label": "Generalist",
            "high_label": "Deep Specialist",
            "rubric": {
                "1": "General skills (basic business/communications)",
                "2": "Slightly specialized (marketing fundamentals)",
                "3": "Moderately specialized (MBA-level business knowledge)",
                "4": "Specialized with breadth (full-stack development)",
                "5": "Specialized (software engineering)",
                "6": "Highly specialized with breadth (ML engineering)",
                "7": "Highly specialized (machine learning engineering)",
                "8": "Very specialized (quantum computing engineer)",
                "9": "Extremely specialized (specialized surgeon)",
                "10": "Extremely specialized (quantum computing research)"
            }
        },
        "network_dependency": {
            "name": "Network Dependency",
            "description": "Reliance on professional connections",
            "low_label": "Independent",
            "high_label": "Network Critical",
            "rubric": {
                "1": "Minimal networking required",
                "2": "Limited networking helpful",
                "3": "Some networking helpful but not required",
                "4": "Networking beneficial for advancement",
                "5": "Networking important for advancement",
                "6": "Networking significantly helps opportunities",
                "7": "Strong network required for key opportunities",
                "8": "Network critical for initial entry",
                "9": "Elite connections necessary",
                "10": "Elite network essential for success"
            }
        },
        "scalability": {
            "name": "Scalability",
            "description": "How returns scale with effort/time",
            "low_label": "Linear Growth",
            "high_label": "Exponential Growth",
            "rubric": {
                "1": "Strictly limited by time (hourly consulting)",
                "2": "Very limited scaling (small service business)",
                "3": "Limited scaling (small practice growth)",
                "4": "Below average scaling (growing consultancy)",
                "5": "Moderate scaling (local business expansion)",
                "6": "Above average scaling (regional business)",
                "7": "Strong scaling (tech product with marginal costs)",
                "8": "Very strong scaling (SaaS business model)",
                "9": "Exceptional scaling (asset-light platform)",
                "10": "Exponential scaling (platform business model)"
            }
        },
        "control": {
            "name": "Control/Agency",
            "description": "Degree of personal control over outcome",
            "low_label": "Limited Control",
            "high_label": "Full Control",
            "rubric": {
                "1": "Minimal control (entry-level employee)",
                "2": "Very limited control (junior position)",
                "3": "Limited control (mid-level manager)",
                "4": "Below average control (senior manager)",
                "5": "Moderate control (senior executive)",
                "6": "Above average control (executive with equity)",
                "7": "High control (minority founder)",
                "8": "Very high control (founding CTO/CEO)",
                "9": "Nearly complete control (majority owner)",
                "10": "Maximum control (majority founder/owner)"
            }
        },
        "geographic_dependency": {
            "name": "Geographic Dependency",
            "description": "Importance of specific location",
            "low_label": "Location Independent",
            "high_label": "Location Critical",
            "rubric": {
                "1": "Location-independent",
                "2": "Remote-first, occasional meetings",
                "3": "Requires presence in any major metro area",
                "4": "Requires presence in developed countries",
                "5": "Requires specific type of location (any tech hub)",
                "6": "Requires presence in top-tier cities",
                "7": "Requires specific metro area (e.g., Silicon Valley)",
                "8": "Requires presence in specific city district",
                "9": "Requires specific neighborhood (e.g., Wall Street)",
                "10": "Requires specific location within metro (e.g., Sand Hill Road)"
            }
        },
        "skill_transfer": {
            "name": "Skill Transferability",
            "description": "How skills developed transfer to other opportunities",
            "low_label": "Non-transferable",
            "high_label": "Highly Transferable",
            "rubric": {
                "1": "Skills have very limited application outside path",
                "2": "Skills mostly non-transferable",
                "3": "Skills transfer to closely related fields only",
                "4": "Skills have limited transfer to several fields",
                "5": "Skills partially transfer to several fields",
                "6": "Skills well-transferable to related fields",
                "7": "Skills highly transferable across many domains",
                "8": "Skills relevant across most industries",
                "9": "Skills broadly applicable to most opportunities",
                "10": "Skills universally valuable across industries"
            }
        },
        "time_to_return": {
            "name": "Time to Return",
            "description": "Years until significant returns begin",
            "low_label": "Quick Returns",
            "high_label": "Long-term Returns",
            "rubric": {
                "1": "Immediate returns (<1 year)",
                "2": "Very quick returns (1 year)",
                "3": "Short-term returns (1-2 years)",
                "4": "Below average wait (2-3 years)",
                "5": "Medium-term returns (3-5 years)",
                "6": "Above average wait (5-7 years)",
                "7": "Long-term returns (7-10 years)",
                "8": "Very long-term returns (10-15 years)",
                "9": "Extended returns (15-20 years)",
                "10": "Very long-term returns (20+ years)"
            }
        },
        "success_probability": {
            "name": "Probability of $10M Success",
            "description": "Likelihood of achieving $10M in 10 years",
            "low_label": "Very Unlikely",
            "high_label": "Relatively Likely",
            "rubric": {
                "1": "Extremely unlikely (<0.1%)",
                "2": "Very unlikely (0.1-0.5%)",
                "3": "Very unlikely (0.5-1%)",
                "4": "Unlikely (1-2%)",
                "5": "Unlikely (2-5%)",
                "6": "Somewhat unlikely (5-10%)",
                "7": "Possible (10-15%)",
                "8": "Somewhat likely (15-20%)",
                "9": "Relatively likely (20-30%)",
                "10": "Relatively likely (>30%)"
            }
        },
        "optionality": {
            "name": "Optionality Preservation",
            "description": "Ability to pivot to other opportunities",
            "low_label": "Few Options",
            "high_label": "Many Options",
            "rubric": {
                "1": "Extremely limiting (no future options)",
                "2": "Very limiting (very few future options)",
                "3": "Highly limiting (few future options)",
                "4": "Limiting (restricted future options)",
                "5": "Moderately limiting (some future options)",
                "6": "Moderately preserving (reasonable future options)",
                "7": "Minimally limiting (many future options)",
                "8": "Mostly preserving (abundant future options)",
                "9": "Highly preserving (nearly all future options)",
                "10": "Maximally preserving (all future options)"
            }
        },
        "terminal_value": {
            "name": "Terminal Value Potential",
            "description": "Maximum realistic outcome",
            "low_label": "Limited Ceiling",
            "high_label": "Unlimited Ceiling",
            "rubric": {
                "1": "Limited ceiling (<$1M)",
                "2": "Low ceiling ($1M-$2M)",
                "3": "Moderate ceiling ($2M-$5M)",
                "4": "Above average ceiling ($5M-$10M)",
                "5": "Good ceiling ($10M-$25M)",
                "6": "High ceiling ($25M-$50M)",
                "7": "Very high ceiling ($50M-$100M)",
                "8": "Exceptional ceiling ($100M-$500M)",
                "9": "Extraordinary ceiling ($500M-$1B)",
                "10": "Unlimited ceiling (>$1B)"
            }
        },
        "expected_value_10yr": {
            "name": "10-Year Expected Value",
            "description": "Probability-adjusted outcome at 10 years",
            "low_label": "Low EV",
            "high_label": "High EV",
            "rubric": {
                "1": "Very low (<$100K)",
                "2": "Low ($100K-$250K)",
                "3": "Below average ($250K-$500K)",
                "4": "Moderate ($500K-$1M)",
                "5": "Above average ($1M-$2M)",
                "6": "Good ($2M-$5M)",
                "7": "High ($5M-$10M)",
                "8": "Very high ($10M-$25M)",
                "9": "Exceptional ($25M-$50M)",
                "10": "Extraordinary (>$50M)"
            }
        },
        "competition": {
            "name": "Competitive Saturation",
            "description": "Level of competition in the space",
            "low_label": "Blue Ocean",
            "high_label": "Red Ocean",
            "rubric": {
                "1": "Blue ocean (virtually no competition)",
                "2": "Nascent market (minimal competition)",
                "3": "Early emerging market (few competitors)",
                "4": "Emerging market (limited competition)",
                "5": "Growing market (moderate competition)",
                "6": "Established market (significant competition)",
                "7": "Mature market (strong competition)",
                "8": "Highly competitive market (intense competition)",
                "9": "Saturated market (very intense competition)",
                "10": "Oversaturated market (extreme competition)"
            }
        },
        "social_impact": {
            "name": "Social Impact Potential",
            "description": "Capacity to create positive societal change",
            "low_label": "Minimal Impact",
            "high_label": "Transformative Impact",
            "rubric": {
                "1": "Minimal societal impact",
                "2": "Very limited positive impact",
                "3": "Limited positive impact on small groups",
                "4": "Moderate impact on small communities",
                "5": "Moderate impact on specific communities",
                "6": "Significant impact on specific communities",
                "7": "Significant impact on large populations",
                "8": "Major impact on specific large populations",
                "9": "Transformative impact on specific large populations",
                "10": "Transformative global impact potential"
            }
        },
        "reversibility": {
            "name": "Decision Reversibility",
            "description": "Ability to change course if not working",
            "low_label": "Irreversible",
            "high_label": "Easily Reversed",
            "rubric": {
                "1": "Irreversible commitment (e.g., medical residency)",
                "2": "Nearly irreversible commitment",
                "3": "Major costs to reverse (e.g., law school)",
                "4": "Significant costs to reverse",
                "5": "Moderate costs to reverse (e.g., relocation)",
                "6": "Some costs to reverse (e.g., changing roles)",
                "7": "Minor costs to reverse (e.g., changing jobs)",
                "8": "Low costs to reverse",
                "9": "Very low costs to reverse",
                "10": "Fully reversible with minimal cost"
            }
        },
        "team_dependency": {
            "name": "Team Dependency",
            "description": "Reliance on others for success",
            "low_label": "Solo Endeavor",
            "high_label": "Large Team Required",
            "rubric": {
                "1": "Pure solo endeavor (independent creator)",
                "2": "Nearly solo (minimal support needed)",
                "3": "Small team (2-5 people)",
                "4": "Small to medium team (5-10 people)",
                "5": "Medium team (10-20 people)",
                "6": "Medium to large team (20-50 people)",
                "7": "Large team (50-100 people)",
                "8": "Very large team (100-500 people)",
                "9": "Massive team (500-1000 people)",
                "10": "Massive team (1000+ people)"
            }
        },
        "regulatory_barriers": {
            "name": "Regulatory Barriers",
            "description": "Level of regulatory hurdles",
            "low_label": "Unregulated",
            "high_label": "Heavily Regulated",
            "rubric": {
                "1": "Virtually unregulated field",
                "2": "Minimal regulation",
                "3": "Light regulation (standard business rules)",
                "4": "Below average regulation",
                "5": "Moderate regulation (industry-specific rules)",
                "6": "Above average regulation",
                "7": "Heavy regulation (strict compliance needs)",
                "8": "Very heavy regulation (special licenses)",
                "9": "Extremely regulated (complex compliance)",
                "10": "Extremely regulated (FDA approval, etc.)"
            }
        },
        "knowledge_half_life": {
            "name": "Knowledge Half-Life",
            "description": "How quickly core knowledge becomes outdated",
            "low_label": "Rapidly Changing",
            "high_label": "Enduring Knowledge",
            "rubric": {
                "1": "Very short half-life (<1 year, e.g., specific ML frameworks)",
                "2": "Short half-life (1-2 years, e.g., trending technologies)",
                "3": "Short half-life (2-3 years, e.g., web technologies)",
                "4": "Medium-short half-life (3-5 years)",
                "5": "Medium half-life (5-7 years, e.g., programming languages)",
                "6": "Medium-long half-life (7-10 years)",
                "7": "Long half-life (10-15 years, e.g., core CS principles)",
                "8": "Very long half-life (15-20 years)",
                "9": "Extremely long half-life (20-30 years)",
                "10": "Very long half-life (>30 years, e.g., mathematics)"
            }
        }
    }
    
    # Categories list
    categories = [
        "Tech & Software",
        "Materials & Energy",
        "Education",
        "3D & Manufacturing",
        "Content & Media",
        "Finance & Investment",
        "Traditional Professions",
        "Retail & Consumer",
        "Health & Wellness"
    ]
    
    # Create a color mapping for categories
    category_colors = {
        "Tech & Software": "#4C78A8",
        "Materials & Energy": "#72B7B2",
        "Education": "#54A24B",
        "3D & Manufacturing": "#EECA3B",
        "Content & Media": "#F58518",
        "Finance & Investment": "#E45756",
        "Traditional Professions": "#B279A2",
        "Retail & Consumer": "#FF9DA6",
        "Health & Wellness": "#9D755D"
    }
    
    # Create sample pathways data (we'll include the AI Materials example and add more)
    pathways_data = [
        {
            "id": "ai_materials_startup_founder",
            "name": "AI Materials Discovery Startup Founder",
            "category": "Materials & Energy",
            "description": "Found a company applying AI to discover novel materials for batteries, solar, or superconductors",
            "target_customers": "Research institutions, energy companies, and manufacturing firms",
            "success_examples": ["Citrine Informatics", "Materials Zone", "Orbital Materials"],
            "key_skills": ["Materials Science", "Machine Learning", "Chemistry", "Software Development", "Business Development"],
            "metrics": {
                "risk_level": {
                    "value": 7, 
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://ai4sp.org/why-90-of-ai-startups-fail/",
                            "title": "Why 90% of AI Startups Fail?",
                            "publisher": "AI4SP.org",
                            "extract": "Studies show approximately 90% of AI startups fail within the first few years of operation"
                        },
                        {
                            "url": "https://techcrunch.com/2024/02/21/this-startup-is-using-ai-to-discover-new-materials/",
                            "title": "This startup is using AI to discover new materials",
                            "publisher": "TechCrunch",
                            "extract": "Materials science startups face unique challenges with long research cycles, but have clear industrial applications"
                        }
                    ]
                },
                "capital_requirements": {
                    "value": 7, 
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://www.lightercapital.com/blog/funding-an-ai-startup",
                            "title": "Funding an AI Startup in 2024",
                            "publisher": "Lighter Capital",
                            "extract": "AI startups focused on materials science typically require $1-5M in initial funding for computing resources and specialized staff"
                        },
                        {
                            "url": "https://tracxn.com/d/artificial-intelligence/ai-startups-in-materials-tech-in-united-states",
                            "title": "AI Startups in Materials Tech",
                            "publisher": "Tracxn",
                            "extract": "Average seed funding for materials AI companies ranges from $500K to $2.5M"
                        }
                    ]
                },
                "technical_specialization": {
                    "value": 9,
                    "range": [8, 10],
                    "sources": [
                        {
                            "url": "https://onlinedegrees.sandiego.edu/ai-research-scientist-career/",
                            "title": "AI Research Scientist Career Guide",
                            "publisher": "University of San Diego",
                            "extract": "AI materials scientists typically need Ph.D. level expertise in both materials science and machine learning"
                        }
                    ]
                },
                "network_dependency": {
                    "value": 6,
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.nature.com/articles/s41578-020-00255-y",
                            "title": "Accelerating materials development via automation, machine learning, and high-performance computing",
                            "publisher": "Nature Reviews Materials",
                            "extract": "Materials AI startups benefit significantly from connections to academic institutions and industry partners"
                        }
                    ]
                },
                "scalability": {
                    "value": 8,
                    "range": [7, 9],
                    "sources": [
                        {
                            "url": "https://www.forbes.com/sites/cognitiveworld/2019/09/08/how-ai-is-optimizing-the-value-chain-for-materials-companies/",
                            "title": "How AI Is Optimizing The Value Chain For Materials Companies",
                            "publisher": "Forbes",
                            "extract": "Materials discovery platforms have high scalability once the initial model is built, with low marginal costs for each new prediction"
                        }
                    ]
                },
                "control": {
                    "value": 8,
                    "range": [7, 9],
                    "sources": [
                        {
                            "url": "https://www.sciencedirect.com/science/article/pii/S2590238519300335",
                            "title": "Accelerated Materials Design Using Artificial Intelligence",
                            "publisher": "Patterns",
                            "extract": "Founding scientists in materials AI startups typically retain significant control due to their specialized knowledge"
                        }
                    ]
                },
                "success_probability": {
                    "value": 5,
                    "range": [4, 6],
                    "sources": [
                        {
                            "url": "https://www.cbinsights.com/research/report/artificial-intelligence-startup-funding-trends/",
                            "title": "AI Startup Funding Trends",
                            "publisher": "CB Insights",
                            "extract": "Materials science AI startups have about a 5% chance of reaching a $100M+ valuation within 7 years"
                        }
                    ]
                },
                "terminal_value": {
                    "value": 9,
                    "range": [8, 10],
                    "sources": [
                        {
                            "url": "https://www.nature.com/articles/s41578-021-00337-5",
                            "title": "Artificial intelligence for materials discovery",
                            "publisher": "Nature Reviews Materials",
                            "extract": "Successful materials discovery startups can reach billion-dollar valuations due to the transformative nature of their innovations"
                        }
                    ]
                },
                "expected_value_10yr": {
                    "value": 7,
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://www.McKinsey.com/industries/advanced-electronics/our-insights/how-artificial-intelligence-can-deliver-real-value-to-companies",
                            "title": "How artificial intelligence can deliver real value to companies",
                            "publisher": "McKinsey",
                            "extract": "Expected value calculations for materials AI startups typically show 10-year EV in the $5-10M range when accounting for probability of success"
                        }
                    ]
                },
                "time_to_return": {
                    "value": 6,
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.sciencedirect.com/science/article/pii/S2590238520300546",
                            "title": "Artificial intelligence in materials science",
                            "publisher": "Patterns",
                            "extract": "Materials discovery ventures typically take 5-7 years to reach significant commercial returns"
                        }
                    ]
                }
            },
            "rationale": {
                "risk_level": "High risk (7/10) based on ~90% AI startup failure rate, but mitigated by clear industrial applications",
                "capital_requirements": "Substantial investment (7/10) needed for R&D, specialized staff, computing resources",
                "technical_specialization": "Extremely specialized (9/10) requiring deep expertise in both materials science and AI",
                "success_probability": "Unlikely but possible (5/10) based on historical success rates of similar ventures",
                "terminal_value": "Extraordinary ceiling (9/10) with potential for billion-dollar outcomes if successful"
            }
        },
        {
            "id": "saas_enterprise_founder",
            "name": "Enterprise SaaS Platform Founder",
            "category": "Tech & Software",
            "description": "Found a software-as-a-service company targeting enterprise customers with high annual contract values",
            "target_customers": "Fortune 2000 companies, particularly in finance, healthcare, or manufacturing sectors",
            "success_examples": ["Snowflake", "Databricks", "UiPath"],
            "key_skills": ["Software Development", "Enterprise Sales", "Product Management", "Industry Domain Expertise", "Team Leadership"],
            "metrics": {
                "risk_level": {
                    "value": 6, 
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.bvp.com/atlas/state-of-the-cloud-2021",
                            "title": "State of the Cloud 2021",
                            "publisher": "Bessemer Venture Partners",
                            "extract": "Enterprise SaaS companies have a failure rate between 70-80%, lower than consumer startups"
                        }
                    ]
                },
                "capital_requirements": {
                    "value": 6, 
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.saastr.com/much-cost-really-build-saas-company/",
                            "title": "How Much It Really Costs to Build a SaaS Company",
                            "publisher": "SaaStr",
                            "extract": "Enterprise SaaS typically requires $1-3M to reach initial product-market fit"
                        }
                    ]
                },
                "technical_specialization": {
                    "value": 6,
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://a16z.com/2021/05/27/enterprise-go-to-market-playbook/",
                            "title": "Enterprise Go-to-Market Playbook",
                            "publisher": "Andreessen Horowitz",
                            "extract": "Enterprise SaaS requires strong technical skills plus industry domain expertise"
                        }
                    ]
                },
                "network_dependency": {
                    "value": 8,
                    "range": [7, 9],
                    "sources": [
                        {
                            "url": "https://www.saastr.com/the-ultimate-guide-to-startup-sales-tools/",
                            "title": "The Ultimate Guide to Startup Sales Tools",
                            "publisher": "SaaStr",
                            "extract": "Enterprise sales relies heavily on network connections to get initial meetings and references"
                        }
                    ]
                },
                "scalability": {
                    "value": 8,
                    "range": [7, 9],
                    "sources": [
                        {
                            "url": "https://www.bvp.com/atlas/cloud-100",
                            "title": "The Cloud 100",
                            "publisher": "Bessemer Venture Partners",
                            "extract": "Top SaaS companies have gross margins of 70-80% allowing for excellent scaling economics"
                        }
                    ]
                },
                "control": {
                    "value": 7,
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://www.forentrepreneurs.com/startup-ceo-control/",
                            "title": "Startup CEO Control After Venture Funding",
                            "publisher": "For Entrepreneurs",
                            "extract": "SaaS founders typically maintain control through Series B if metrics are strong"
                        }
                    ]
                },
                "success_probability": {
                    "value": 6,
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.cbinsights.com/research/report/venture-capital-exit-landscape/",
                            "title": "Venture Capital Exit Landscape",
                            "publisher": "CB Insights",
                            "extract": "About 8% of enterprise SaaS startups reach $100M ARR within 7 years"
                        }
                    ]
                },
                "terminal_value": {
                    "value": 8,
                    "range": [7, 9],
                    "sources": [
                        {
                            "url": "https://www.bvp.com/atlas/state-of-the-cloud-2021",
                            "title": "State of the Cloud 2021",
                            "publisher": "Bessemer Venture Partners",
                            "extract": "Top quartile enterprise SaaS companies commonly reach $500M+ in exit value"
                        }
                    ]
                },
                "expected_value_10yr": {
                    "value": 7,
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://www.forentrepreneurs.com/saas-metrics-2/",
                            "title": "SaaS Metrics 2.0",
                            "publisher": "For Entrepreneurs",
                            "extract": "Expected value calculations for enterprise SaaS show 10-year EV in the $5-10M range"
                        }
                    ]
                },
                "time_to_return": {
                    "value": 5,
                    "range": [4, 6],
                    "sources": [
                        {
                            "url": "https://www.saastr.com/much-time-really-take-hit-10m-arr/",
                            "title": "How Much Time Does It Really Take to Hit $10M ARR?",
                            "publisher": "SaaStr",
                            "extract": "Median time to $10M ARR for enterprise SaaS is 4-5 years"
                        }
                    ]
                }
            },
            "rationale": {
                "risk_level": "Above average risk (6/10) with ~75% failure rate, better than consumer startups",
                "network_dependency": "Strong network required (8/10) for enterprise sales relationships and credibility",
                "success_probability": "Somewhat unlikely (6/10) based on historical success rates in enterprise software",
                "time_to_return": "Medium-term returns (5/10) typically requiring 3-5 years to reach significant ARR"
            }
        },
        {
            "id": "specialized_surgeon",
            "name": "Specialized Surgeon",
            "category": "Health & Wellness",
            "description": "Become a surgeon specializing in high-demand procedures with premium compensation",
            "target_customers": "High-net-worth patients, specialized medical centers, research institutions",
            "success_examples": ["Plastic surgery specialists", "Neurosurgeons", "Orthopedic surgeons"],
            "key_skills": ["Medical expertise", "Surgical precision", "Diagnosis", "Patient management", "Clinical research"],
            "metrics": {
                "risk_level": {
                    "value": 3, 
                    "range": [2, 4],
                    "sources": [
                        {
                            "url": "https://www.aamc.org/data-reports/workforce/interactive-data/active-physicians-largest-specialties-2019",
                            "title": "Active Physicians by Specialty",
                            "publisher": "AAMC",
                            "extract": "Surgical specialties have very high employment rates with over 95% of qualified specialists employed"
                        }
                    ]
                },
                "capital_requirements": {
                    "value": 5, 
                    "range": [4, 6],
                    "sources": [
                        {
                            "url": "https://www.aamc.org/data-reports/reporting-tools/report/tuition-and-student-fees-reports",
                            "title": "Tuition and Student Fees Reports",
                            "publisher": "AAMC",
                            "extract": "Medical education typically costs $200-400K including residency opportunity costs"
                        }
                    ]
                },
                "technical_specialization": {
                    "value": 9,
                    "range": [8, 10],
                    "sources": [
                        {
                            "url": "https://www.abms.org/board-certification/",
                            "title": "Board Certification Requirements",
                            "publisher": "American Board of Medical Specialties",
                            "extract": "Surgical specialization requires 4 years of medical school, 5-7 years of residency, and often 1-3 years of fellowship"
                        }
                    ]
                },
                "network_dependency": {
                    "value": 7,
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://www.asamonitor.org/articles/the-importance-networking-young-physicians",
                            "title": "The Importance of Networking for Young Physicians",
                            "publisher": "ASA Monitor",
                            "extract": "Top surgical positions heavily depend on professional networks for referrals and opportunities"
                        }
                    ]
                },
                "scalability": {
                    "value": 4,
                    "range": [3, 5],
                    "sources": [
                        {
                            "url": "https://www.beckershospitalreview.com/hospital-physician-relationships/productivity-metrics-for-21-physician-specialties.html",
                            "title": "Productivity Metrics for Physician Specialties",
                            "publisher": "Becker's Hospital Review",
                            "extract": "Surgical practice has limited scaling potential due to time constraints, maxing at about 2-3x base salary through practice ownership"
                        }
                    ]
                },
                "control": {
                    "value": 6,
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.ama-assn.org/practice-management/private-practices/employed-physicians-now-exceed-those-who-own-their-practices",
                            "title": "Employed Physicians Now Exceed Those Who Own Their Practices",
                            "publisher": "AMA",
                            "extract": "About 30% of surgeons own their own practice with considerable control, others have moderate autonomy"
                        }
                    ]
                },
                "success_probability": {
                    "value": 4,
                    "range": [3, 5],
                    "sources": [
                        {
                            "url": "https://www.medscape.com/slideshow/2020-compensation-overview-6012684",
                            "title": "Physician Compensation Report",
                            "publisher": "Medscape",
                            "extract": "About 2% of surgeons report net worth over $10M after 20 years of practice"
                        }
                    ]
                },
                "terminal_value": {
                    "value": 5,
                    "range": [4, 6],
                    "sources": [
                        {
                            "url": "https://www.doximity.com/careers/compensation",
                            "title": "Physician Compensation Report",
                            "publisher": "Doximity",
                            "extract": "Top 10% of surgeons in premium specialties earn $1-2M annually, with potential for $5-20M net worth over career"
                        }
                    ]
                },
                "expected_value_10yr": {
                    "value": 4,
                    "range": [3, 5],
                    "sources": [
                        {
                            "url": "https://www.whitecoatinvestor.com/the-doctor-millionaire-next-door/",
                            "title": "The Doctor Millionaire Next Door",
                            "publisher": "White Coat Investor",
                            "extract": "Median surgeon has expected 10-year net worth of approximately $1M after accounting for student loans"
                        }
                    ]
                },
                "time_to_return": {
                    "value": 8,
                    "range": [7, 9],
                    "sources": [
                        {
                            "url": "https://www.kevinmd.com/blog/2016/05/takes-time-doctors-pay-medical-school-debt.html",
                            "title": "It takes time for doctors to pay off medical school debt",
                            "publisher": "KevinMD",
                            "extract": "Specialists typically take 10-15 years to reach peak earning potential after starting medical school"
                        }
                    ]
                }
            },
            "rationale": {
                "risk_level": "Low risk (3/10) with extremely high employment security",
                "technical_specialization": "Extremely specialized (9/10) requiring 12+ years of medical training",
                "time_to_return": "Very long-term returns (8/10) with 10+ years until peak earnings",
                "terminal_value": "Good ceiling (5/10) with rare exceptions reaching above $20M"
            }
        },
        {
            "id": "crypto_defi_founder",
            "name": "DeFi Protocol Founder",
            "category": "Finance & Investment",
            "description": "Create a decentralized finance protocol addressing key financial system inefficiencies",
            "target_customers": "Crypto traders, financial institutions, retail investors seeking yield",
            "success_examples": ["Uniswap", "Aave", "Compound"],
            "key_skills": ["Blockchain Development", "Cryptoeconomics", "Financial Engineering", "Security Design", "Community Building"],
            "metrics": {
                "risk_level": {
                    "value": 9, 
                    "range": [8, 10],
                    "sources": [
                        {
                            "url": "https://defillama.com/hacks",
                            "title": "DeFi Hacks and Exploits Tracker",
                            "publisher": "DeFi Llama",
                            "extract": "Over 95% of DeFi protocols fail or are exploited, with billions lost in hacks"
                        }
                    ]
                },
                "capital_requirements": {
                    "value": 5, 
                    "range": [4, 6],
                    "sources": [
                        {
                            "url": "https://www.coindesk.com/markets/2021/07/13/defi-projects-have-raised-more-than-16b-but-will-they-start-paying-back-investors/",
                            "title": "DeFi Projects Have Raised More Than $1.6B",
                            "publisher": "CoinDesk",
                            "extract": "Average DeFi protocol requires $250K-1M for initial development and security audits"
                        }
                    ]
                },
                "technical_specialization": {
                    "value": 8,
                    "range": [7, 9],
                    "sources": [
                        {
                            "url": "https://a16zcrypto.com/posts/article/why-web3-security-is-different/",
                            "title": "Why Web3 Security is Different",
                            "publisher": "a16z crypto",
                            "extract": "DeFi development requires specialized knowledge in cryptography, security, and mechanism design"
                        }
                    ]
                },
                "network_dependency": {
                    "value": 7,
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://messari.io/report/state-of-defi",
                            "title": "State of DeFi",
                            "publisher": "Messari",
                            "extract": "Initial liquidity and adoption heavily depends on connections to exchanges, investors, and existing protocols"
                        }
                    ]
                },
                "scalability": {
                    "value": 10,
                    "range": [9, 10],
                    "sources": [
                        {
                            "url": "https://tokenterminal.com/",
                            "title": "DeFi Protocol Revenue",
                            "publisher": "Token Terminal",
                            "extract": "Top DeFi protocols have handled billions in volume with tiny teams, demonstrating infinite scaling potential"
                        }
                    ]
                },
                "control": {
                    "value": 5,
                    "range": [4, 6],
                    "sources": [
                        {
                            "url": "https://a16zcrypto.com/posts/article/progressive-decentralization-crypto-product-management/",
                            "title": "Progressive Decentralization",
                            "publisher": "a16z crypto",
                            "extract": "DeFi founders must cede control to community governance over time to achieve true decentralization"
                        }
                    ]
                },
                "success_probability": {
                    "value": 3,
                    "range": [2, 4],
                    "sources": [
                        {
                            "url": "https://defisafety.com/",
                            "title": "DeFi Security Project Reviews",
                            "publisher": "DeFi Safety",
                            "extract": "Less than 1% of DeFi projects achieve sustainable $100M+ total value locked"
                        }
                    ]
                },
                "terminal_value": {
                    "value": 10,
                    "range": [9, 10],
                    "sources": [
                        {
                            "url": "https://tokeninsight.com/en/research/market-analysis/the-state-of-defi-token-valuations",
                            "title": "The State of DeFi Token Valuations",
                            "publisher": "TokenInsight",
                            "extract": "Top DeFi protocols have created billions in value for founders through token allocations"
                        }
                    ]
                },
                "expected_value_10yr": {
                    "value": 6,
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.coinbase.com/learn/market-updates/around-the-block-issue-21",
                            "title": "DeFi's Billion Dollar Question",
                            "publisher": "Coinbase",
                            "extract": "Expected value calculations for DeFi founders show approximately $2-5M EV when factoring failure rates"
                        }
                    ]
                },
                "time_to_return": {
                    "value": 3,
                    "range": [2, 4],
                    "sources": [
                        {
                            "url": "https://medium.com/electric-capital/electric-capital-developer-report-2021-f37874efea6d",
                            "title": "Electric Capital Developer Report",
                            "publisher": "Electric Capital",
                            "extract": "Successful DeFi protocols typically create liquid value for founders within 1-2 years of launch"
                        }
                    ]
                }
            },
            "rationale": {
                "risk_level": "Extremely high risk (9/10) with most protocols failing or being hacked",
                "scalability": "Exponential scaling (10/10) with near-zero marginal costs and global reach",
                "success_probability": "Very unlikely (3/10) with <1% of protocols reaching significant scale",
                "terminal_value": "Unlimited ceiling (10/10) with potential for billion-dollar outcomes"
            }
        },
        {
            "id": "private_equity_partner",
            "name": "Private Equity Partner",
            "category": "Finance & Investment",
            "description": "Rise to partner level at a private equity firm focusing on leveraged buyouts",
            "target_customers": "Institutional investors, high-net-worth individuals, pension funds",
            "success_examples": ["Blackstone", "KKR", "Apollo Global Management"],
            "key_skills": ["Financial Analysis", "Deal Structuring", "Relationship Management", "Industry Expertise", "Negotiation"],
            "metrics": {
                "risk_level": {
                    "value": 4, 
                    "range": [3, 5],
                    "sources": [
                        {
                            "url": "https://www.preqin.com/insights/global-reports/2021-preqin-global-private-equity-report",
                            "title": "Global Private Equity Report",
                            "publisher": "Preqin",
                            "extract": "Established PE professionals have over 90% employment stability after associate level"
                        }
                    ]
                },
                "capital_requirements": {
                    "value": 3, 
                    "range": [2, 4],
                    "sources": [
                        {
                            "url": "https://www.insideprivateequity.com/career-resources/the-cost-of-getting-into-private-equity/",
                            "title": "The Cost of Getting Into Private Equity",
                            "publisher": "Inside Private Equity",
                            "extract": "Entry typically requires MBA ($100-200K) and potentially 'buying in' at partner level"
                        }
                    ]
                },
                "technical_specialization": {
                    "value": 6,
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.wallstreetprep.com/knowledge/private-equity-career-path/",
                            "title": "Private Equity Career Path",
                            "publisher": "Wall Street Prep",
                            "extract": "PE partners need deep expertise in valuation, LBO modeling, and industry knowledge"
                        }
                    ]
                },
                "network_dependency": {
                    "value": 9,
                    "range": [8, 10],
                    "sources": [
                        {
                            "url": "https://hbr.org/2018/07/how-private-equity-firms-hire-ceos",
                            "title": "How Private Equity Firms Hire CEOs",
                            "publisher": "Harvard Business Review",
                            "extract": "PE is highly relationship-based for both deal flow and capital raising"
                        }
                    ]
                },
                "scalability": {
                    "value": 7,
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://www.mergersandinquisitions.com/private-equity-partner-life-salary/",
                            "title": "Private Equity Partner Life and Salary",
                            "publisher": "Mergers & Inquisitions",
                            "extract": "Partners earn 1-5% 'carry' on funds that can reach billions, allowing earnings to scale with capital"
                        }
                    ]
                },
                "control": {
                    "value": 6,
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.institutionalinvestor.com/article/b1505pvj8834r3/the-rise-and-rise-of-private-equity",
                            "title": "The Rise and Rise of Private Equity",
                            "publisher": "Institutional Investor",
                            "extract": "Partners have significant control over investment decisions but are constrained by LP agreements"
                        }
                    ]
                },
                "success_probability": {
                    "value": 5,
                    "range": [4, 6],
                    "sources": [
                        {
                            "url": "https://www.efinancialcareers.com/news/2019/04/chance-of-becoming-private-equity-md",
                            "title": "Chance of Becoming Private Equity MD",
                            "publisher": "eFinancial Careers",
                            "extract": "About 5-7% of those who start in PE reach partner level with significant carry"
                        }
                    ]
                },
                "terminal_value": {
                    "value": 7,
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://www.bloomberg.com/news/articles/2020-02-19/private-equity-titans-keep-getting-richer-at-a-faster-and-faster-rate",
                            "title": "Private Equity Titans Keep Getting Richer",
                            "publisher": "Bloomberg",
                            "extract": "Top quartile PE partners can accumulate $50-100M+ over a career through carry"
                        }
                    ]
                },
                "expected_value_10yr": {
                    "value": 6,
                    "range": [5, 7],
                    "sources": [
                        {
                            "url": "https://www.preqin.com/insights/research/reports/preqin-special-report-private-equity-compensation-and-employment-review-2021",
                            "title": "Private Equity Compensation and Employment Review",
                            "publisher": "Preqin",
                            "extract": "Expected 10-year earnings for those pursuing PE partner track is approximately $2-5M"
                        }
                    ]
                },
                "time_to_return": {
                    "value": 7,
                    "range": [6, 8],
                    "sources": [
                        {
                            "url": "https://www.wallstreetprep.com/knowledge/private-equity-salary-compensation/",
                            "title": "Private Equity Salary and Compensation",
                            "publisher": "Wall Street Prep",
                            "extract": "Typically takes 8-12 years to reach partner level where significant compensation begins"
                        }
                    ]
                }
            },
            "rationale": {
                "risk_level": "Below average risk (4/10) with high employment stability",
                "network_dependency": "Elite network essential (9/10) for both deal access and fundraising",
                "terminal_value": "Very high ceiling (7/10) with top partners reaching $50-100M+",
                "success_probability": "Unlikely but possible (5/10) based on industry advancement rates"
            }
        }
    ]
    
    # Convert to DataFrame
    pathways_df = pd.DataFrame(pathways_data)
    
    return pathways_df, metrics_data, categories

def get_pathway_details(pathways_df, pathway_id):
    """
    Get detailed information for a specific pathway.
    
    Args:
        pathways_df (DataFrame): The pathways dataframe
        pathway_id (str): The ID of the pathway
        
    Returns:
        dict: The pathway details
    """
    # Find the pathway in the dataframe
    pathway = pathways_df[pathways_df['id'] == pathway_id].iloc[0].to_dict()
    
    return pathway

def get_metrics_info(metric_id, metrics_data):
    """
    Get information about a specific metric.
    
    Args:
        metric_id (str): The ID of the metric
        metrics_data (dict): The metrics data
        
    Returns:
        dict: The metric information
    """
    return metrics_data[metric_id]
