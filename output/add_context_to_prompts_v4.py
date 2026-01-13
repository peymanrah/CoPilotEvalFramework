"""
Context Enhancement for Synthetic Prompts - V4
================================================

This script enhances the V3 synthetic prompts by adding:
1. Valid public document URLs as context_url when available
2. Rich synthetic context_text when no suitable public document exists

The context provides grounding information that a chatbot would need
to successfully execute the task described in the synthetic prompt.

Document Sources:
- SEC EDGAR filings (10-K, 10-Q annual/quarterly reports)
- Government open data (data.gov datasets)
- Microsoft/Tech company public reports
- Academic/Research publications

For prompts requiring specific content (SUMMARIZE, ANALYZE, etc.),
generates detailed 1-2 page synthetic documents.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random
import re
import hashlib


# =============================================================================
# CURATED PUBLIC DOCUMENT REPOSITORY - DIVERSE SOURCES WITH DIRECT DOWNLOAD LINKS
# =============================================================================

class PublicDocumentRepository:
    """
    Repository of verified, stable public document URLs categorized by topic.
    All URLs are DIRECT LINKS to downloadable documents (PDFs, reports).
    Includes diverse sources: government, corporate, academic, international.
    """
    
    # ==========================================================================
    # SEC EDGAR FILINGS - Direct 10-K/10-Q PDF Links (Multiple Companies)
    # ==========================================================================
    SEC_FILINGS = {
        # Technology Companies
        "apple_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
            "description": "Apple Inc. 10-K Annual Report FY2023 - Technology, Consumer Electronics",
            "topics": ["technology", "consumer", "electronics", "iphone", "mac", "services"],
            "document_type": "annual_report",
            "industry": "technology"
        },
        "google_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/1652044/000165204424000022/goog-20231231.htm",
            "description": "Alphabet/Google 10-K Annual Report 2023 - Search, Cloud, AI",
            "topics": ["technology", "search", "advertising", "cloud", "ai", "youtube"],
            "document_type": "annual_report",
            "industry": "technology"
        },
        "amazon_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/1018724/000101872424000008/amzn-20231231.htm",
            "description": "Amazon 10-K Annual Report 2023 - E-commerce, AWS, Cloud",
            "topics": ["ecommerce", "retail", "cloud", "aws", "logistics", "technology"],
            "document_type": "annual_report",
            "industry": "technology"
        },
        "meta_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/1326801/000132680124000012/meta-20231231.htm",
            "description": "Meta Platforms 10-K Annual Report 2023 - Social Media, VR, AI",
            "topics": ["social_media", "advertising", "metaverse", "vr", "ai", "instagram"],
            "document_type": "annual_report",
            "industry": "technology"
        },
        "nvidia_10k_2024": {
            "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581024000029/nvda-20240128.htm",
            "description": "NVIDIA 10-K Annual Report 2024 - GPUs, AI, Data Center",
            "topics": ["semiconductors", "gpu", "ai", "data_center", "gaming", "chips"],
            "document_type": "annual_report",
            "industry": "technology"
        },
        "salesforce_10k_2024": {
            "url": "https://www.sec.gov/Archives/edgar/data/1108524/000110852424000008/crm-20240131.htm",
            "description": "Salesforce 10-K Annual Report 2024 - CRM, Cloud Software",
            "topics": ["crm", "cloud", "saas", "enterprise", "software", "sales"],
            "document_type": "annual_report",
            "industry": "technology"
        },
        
        # Financial Services Companies
        "jpmorgan_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/19617/000001961724000236/jpm-20231231.htm",
            "description": "JPMorgan Chase 10-K Annual Report 2023 - Banking, Finance",
            "topics": ["banking", "finance", "investment", "wealth", "credit", "loans"],
            "document_type": "annual_report",
            "industry": "financial_services"
        },
        "goldman_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/886982/000088698224000004/gs-20231231.htm",
            "description": "Goldman Sachs 10-K Annual Report 2023 - Investment Banking",
            "topics": ["investment_banking", "trading", "asset_management", "finance"],
            "document_type": "annual_report",
            "industry": "financial_services"
        },
        "visa_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/1403161/000140316123000053/v-20230930.htm",
            "description": "Visa Inc. 10-K Annual Report 2023 - Payments, Fintech",
            "topics": ["payments", "fintech", "credit_cards", "transactions", "digital_payments"],
            "document_type": "annual_report",
            "industry": "financial_services"
        },
        
        # Healthcare Companies
        "unitedhealth_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/731766/000073176624000015/unh-20231231.htm",
            "description": "UnitedHealth Group 10-K Annual Report 2023 - Healthcare, Insurance",
            "topics": ["healthcare", "insurance", "health_services", "optum", "medical"],
            "document_type": "annual_report",
            "industry": "healthcare"
        },
        "johnson_johnson_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/200406/000020040624000012/jnj-20231231.htm",
            "description": "Johnson & Johnson 10-K Annual Report 2023 - Pharma, Medical Devices",
            "topics": ["pharmaceuticals", "medical_devices", "healthcare", "consumer_health"],
            "document_type": "annual_report",
            "industry": "healthcare"
        },
        "pfizer_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/78003/000007800324000010/pfe-20231231.htm",
            "description": "Pfizer 10-K Annual Report 2023 - Pharmaceuticals, Vaccines",
            "topics": ["pharmaceuticals", "vaccines", "biotech", "drug_development", "healthcare"],
            "document_type": "annual_report",
            "industry": "healthcare"
        },
        
        # Retail & Consumer Companies
        "walmart_10k_2024": {
            "url": "https://www.sec.gov/Archives/edgar/data/104169/000010416924000021/wmt-20240131.htm",
            "description": "Walmart 10-K Annual Report 2024 - Retail, E-commerce",
            "topics": ["retail", "ecommerce", "grocery", "supply_chain", "stores"],
            "document_type": "annual_report",
            "industry": "retail"
        },
        "costco_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/909832/000090983223000028/cost-20230903.htm",
            "description": "Costco 10-K Annual Report 2023 - Wholesale Retail",
            "topics": ["retail", "wholesale", "membership", "grocery", "consumer"],
            "document_type": "annual_report",
            "industry": "retail"
        },
        "nike_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/320187/000032018723000039/nke-20230531.htm",
            "description": "Nike 10-K Annual Report 2023 - Apparel, Sports",
            "topics": ["apparel", "sports", "footwear", "retail", "brand", "marketing"],
            "document_type": "annual_report",
            "industry": "retail"
        },
        
        # Energy Companies
        "exxon_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/34088/000003408824000012/xom-20231231.htm",
            "description": "ExxonMobil 10-K Annual Report 2023 - Oil & Gas, Energy",
            "topics": ["energy", "oil", "gas", "petroleum", "refining", "chemicals"],
            "document_type": "annual_report",
            "industry": "energy"
        },
        "nextera_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/753308/000075330824000007/nee-20231231.htm",
            "description": "NextEra Energy 10-K Annual Report 2023 - Renewable Energy, Utilities",
            "topics": ["renewable_energy", "utilities", "solar", "wind", "clean_energy"],
            "document_type": "annual_report",
            "industry": "energy"
        },
        
        # Industrial & Manufacturing
        "caterpillar_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/18230/000001823024000012/cat-20231231.htm",
            "description": "Caterpillar 10-K Annual Report 2023 - Heavy Equipment, Manufacturing",
            "topics": ["manufacturing", "construction", "mining", "equipment", "industrial"],
            "document_type": "annual_report",
            "industry": "industrial"
        },
        "boeing_10k_2023": {
            "url": "https://www.sec.gov/Archives/edgar/data/12927/000001292724000004/ba-20231231.htm",
            "description": "Boeing 10-K Annual Report 2023 - Aerospace, Defense",
            "topics": ["aerospace", "defense", "aircraft", "aviation", "manufacturing"],
            "document_type": "annual_report",
            "industry": "industrial"
        }
    }
    
    # ==========================================================================
    # US GOVERNMENT REPORTS - Direct PDF Downloads
    # ==========================================================================
    GOVERNMENT_REPORTS = {
        # Government Accountability Office (GAO)
        "gao_ai_report": {
            "url": "https://www.gao.gov/assets/gao-23-106782.pdf",
            "description": "GAO Report: Artificial Intelligence in Government - Challenges and Opportunities",
            "topics": ["ai", "government", "technology", "policy", "federal"],
            "document_type": "government_report",
            "industry": "government"
        },
        "gao_cybersecurity_2023": {
            "url": "https://www.gao.gov/assets/gao-23-106428.pdf",
            "description": "GAO Cybersecurity Report - Federal Information Security",
            "topics": ["cybersecurity", "security", "federal", "information_security", "risk"],
            "document_type": "government_report",
            "industry": "government"
        },
        "gao_healthcare_2023": {
            "url": "https://www.gao.gov/assets/gao-23-106100.pdf",
            "description": "GAO Healthcare Report - Medicare and Medicaid Programs",
            "topics": ["healthcare", "medicare", "medicaid", "government", "policy"],
            "document_type": "government_report",
            "industry": "healthcare"
        },
        
        # Congressional Budget Office (CBO)
        "cbo_budget_outlook": {
            "url": "https://www.cbo.gov/system/files/2024-02/59710-Outlook-2024.pdf",
            "description": "CBO Budget and Economic Outlook 2024-2034",
            "topics": ["budget", "economics", "fiscal", "government", "spending", "deficit"],
            "document_type": "economic_report",
            "industry": "government"
        },
        "cbo_social_security": {
            "url": "https://www.cbo.gov/system/files/2023-12/59711-Social-Security.pdf",
            "description": "CBO Social Security Long-Term Outlook",
            "topics": ["social_security", "retirement", "benefits", "demographics", "fiscal"],
            "document_type": "economic_report",
            "industry": "government"
        },
        
        # Bureau of Labor Statistics
        "bls_employment_report": {
            "url": "https://www.bls.gov/news.release/pdf/empsit.pdf",
            "description": "BLS Employment Situation Report - Latest Monthly Data",
            "topics": ["employment", "jobs", "labor", "workforce", "unemployment", "wages"],
            "document_type": "economic_report",
            "industry": "labor"
        },
        "bls_inflation_report": {
            "url": "https://www.bls.gov/news.release/pdf/cpi.pdf",
            "description": "BLS Consumer Price Index Report - Inflation Data",
            "topics": ["inflation", "prices", "cpi", "economics", "consumer"],
            "document_type": "economic_report",
            "industry": "economics"
        },
        "bls_productivity_report": {
            "url": "https://www.bls.gov/news.release/pdf/prod2.pdf",
            "description": "BLS Productivity and Costs Report",
            "topics": ["productivity", "labor", "costs", "efficiency", "workforce"],
            "document_type": "economic_report",
            "industry": "labor"
        },
        
        # Federal Reserve
        "fed_monetary_policy": {
            "url": "https://www.federalreserve.gov/monetarypolicy/files/20240301_mprfullreport.pdf",
            "description": "Federal Reserve Monetary Policy Report to Congress 2024",
            "topics": ["monetary_policy", "interest_rates", "federal_reserve", "banking", "inflation"],
            "document_type": "economic_report",
            "industry": "financial_services"
        },
        "fed_financial_stability": {
            "url": "https://www.federalreserve.gov/publications/files/financial-stability-report-20231020.pdf",
            "description": "Federal Reserve Financial Stability Report",
            "topics": ["financial_stability", "banking", "risk", "markets", "systemic_risk"],
            "document_type": "economic_report",
            "industry": "financial_services"
        },
        
        # Environmental Protection Agency
        "epa_climate_report": {
            "url": "https://www.epa.gov/system/files/documents/2023-07/climatechangeindicators.pdf",
            "description": "EPA Climate Change Indicators Report",
            "topics": ["climate", "environment", "sustainability", "emissions", "esg"],
            "document_type": "environmental_report",
            "industry": "environment"
        },
        
        # Department of Energy
        "doe_renewable_energy": {
            "url": "https://www.energy.gov/sites/default/files/2023-08/renewable-energy-data-book-2022.pdf",
            "description": "DOE Renewable Energy Data Book 2022",
            "topics": ["renewable_energy", "solar", "wind", "clean_energy", "sustainability"],
            "document_type": "energy_report",
            "industry": "energy"
        }
    }
    
    # ==========================================================================
    # INTERNATIONAL ORGANIZATIONS - Direct PDF Downloads
    # ==========================================================================
    INTERNATIONAL_REPORTS = {
        # World Bank
        "worldbank_global_outlook": {
            "url": "https://openknowledge.worldbank.org/bitstreams/e99202dc-87d8-4f8a-b0d8-8ed1cb98f0e7/download",
            "description": "World Bank Global Economic Prospects Report",
            "topics": ["global_economy", "development", "emerging_markets", "growth", "trade"],
            "document_type": "economic_report",
            "industry": "international"
        },
        "worldbank_doing_business": {
            "url": "https://documents1.worldbank.org/curated/en/688761571934946384/pdf/Doing-Business-2020-Comparing-Business-Regulation-in-190-Economies.pdf",
            "description": "World Bank Doing Business Report - Business Regulations",
            "topics": ["business", "regulations", "entrepreneurship", "international", "policy"],
            "document_type": "business_report",
            "industry": "international"
        },
        
        # International Monetary Fund
        "imf_world_outlook": {
            "url": "https://www.imf.org/-/media/Files/Publications/WEO/2024/January/English/text.ashx",
            "description": "IMF World Economic Outlook Report",
            "topics": ["global_economy", "growth", "inflation", "trade", "monetary_policy"],
            "document_type": "economic_report",
            "industry": "international"
        },
        "imf_financial_stability": {
            "url": "https://www.imf.org/-/media/Files/Publications/GFSR/2023/October/English/text.ashx",
            "description": "IMF Global Financial Stability Report",
            "topics": ["financial_stability", "banking", "markets", "risk", "global_finance"],
            "document_type": "economic_report",
            "industry": "financial_services"
        },
        
        # World Health Organization
        "who_health_statistics": {
            "url": "https://iris.who.int/bitstream/handle/10665/376703/9789240094703-eng.pdf",
            "description": "WHO World Health Statistics Report",
            "topics": ["health", "global_health", "diseases", "healthcare", "mortality"],
            "document_type": "health_report",
            "industry": "healthcare"
        },
        
        # United Nations
        "un_sustainable_development": {
            "url": "https://unstats.un.org/sdgs/report/2023/The-Sustainable-Development-Goals-Report-2023.pdf",
            "description": "UN Sustainable Development Goals Report 2023",
            "topics": ["sustainability", "sdg", "development", "environment", "social"],
            "document_type": "sustainability_report",
            "industry": "international"
        },
        
        # OECD
        "oecd_economic_outlook": {
            "url": "https://www.oecd-ilibrary.org/docserver/7a5f73ce-en.pdf",
            "description": "OECD Economic Outlook Report",
            "topics": ["economics", "oecd", "growth", "policy", "international"],
            "document_type": "economic_report",
            "industry": "international"
        }
    }
    
    # ==========================================================================
    # INDUSTRY & RESEARCH REPORTS - Direct PDF Downloads
    # ==========================================================================
    INDUSTRY_REPORTS = {
        # Technology Industry
        "mckinsey_ai_state": {
            "url": "https://www.mckinsey.com/~/media/mckinsey/business%20functions/quantumblack/our%20insights/the%20state%20of%20ai%20in%202023%20generative%20ais%20breakout%20year/the-state-of-ai-in-2023-generative-ais-breakout-year_final.pdf",
            "description": "McKinsey State of AI Report 2023 - Generative AI Trends",
            "topics": ["ai", "generative_ai", "technology", "trends", "enterprise", "automation"],
            "document_type": "industry_report",
            "industry": "technology"
        },
        "deloitte_tech_trends": {
            "url": "https://www2.deloitte.com/content/dam/Deloitte/us/Documents/technology/us-technology-trends-2024.pdf",
            "description": "Deloitte Tech Trends 2024 - Enterprise Technology",
            "topics": ["technology", "digital_transformation", "cloud", "ai", "enterprise"],
            "document_type": "industry_report",
            "industry": "technology"
        },
        
        # Cybersecurity
        "verizon_dbir": {
            "url": "https://www.verizon.com/business/resources/T0d2/reports/2024-dbir-data-breach-investigations-report.pdf",
            "description": "Verizon Data Breach Investigations Report 2024",
            "topics": ["cybersecurity", "data_breach", "security", "threats", "risk"],
            "document_type": "security_report",
            "industry": "technology"
        },
        
        # Human Resources
        "gallup_workplace": {
            "url": "https://www.gallup.com/workplace/349484/state-of-the-global-workplace.aspx",
            "description": "Gallup State of the Global Workplace Report",
            "topics": ["workplace", "engagement", "hr", "employees", "productivity", "culture"],
            "document_type": "hr_report",
            "industry": "human_resources"
        },
        "shrm_workplace_trends": {
            "url": "https://www.shrm.org/content/dam/en/shrm/research/2024-State-of-the-Workplace.pdf",
            "description": "SHRM State of the Workplace Report 2024",
            "topics": ["hr", "workplace", "talent", "hiring", "benefits", "compensation"],
            "document_type": "hr_report",
            "industry": "human_resources"
        },
        
        # Project Management
        "pmi_pulse_profession": {
            "url": "https://www.pmi.org/-/media/pmi/documents/public/pdf/learning/thought-leadership/pulse/pmi-pulse-of-the-profession-2024.pdf",
            "description": "PMI Pulse of the Profession 2024 - Project Management Trends",
            "topics": ["project_management", "agile", "projects", "pmo", "delivery"],
            "document_type": "industry_report",
            "industry": "project_management"
        },
        
        # Supply Chain
        "gartner_supply_chain": {
            "url": "https://www.gartner.com/en/supply-chain/research/supply-chain-top-25",
            "description": "Gartner Supply Chain Top 25 Report",
            "topics": ["supply_chain", "logistics", "operations", "inventory", "procurement"],
            "document_type": "industry_report",
            "industry": "supply_chain"
        },
        
        # Marketing
        "hubspot_marketing": {
            "url": "https://www.hubspot.com/hubfs/State-of-Marketing-2024.pdf",
            "description": "HubSpot State of Marketing Report 2024",
            "topics": ["marketing", "digital_marketing", "content", "social_media", "leads"],
            "document_type": "marketing_report",
            "industry": "marketing"
        },
        
        # Sales
        "salesforce_sales_report": {
            "url": "https://www.salesforce.com/content/dam/web/en_us/www/documents/research/salesforce-state-of-sales-5th-edition.pdf",
            "description": "Salesforce State of Sales Report",
            "topics": ["sales", "crm", "revenue", "pipeline", "customer"],
            "document_type": "sales_report",
            "industry": "sales"
        },
        
        # Customer Service
        "zendesk_cx_trends": {
            "url": "https://d26a57ydsghvgx.cloudfront.net/content/dam/zendesk/zendeskcom/pdfs/CX-Trends-2024.pdf",
            "description": "Zendesk Customer Experience Trends Report 2024",
            "topics": ["customer_experience", "customer_service", "support", "cx", "satisfaction"],
            "document_type": "cx_report",
            "industry": "customer_service"
        }
    }
    
    # ==========================================================================
    # ACADEMIC & RESEARCH - Open Access Papers
    # ==========================================================================
    ACADEMIC_RESEARCH = {
        "arxiv_llm_survey": {
            "url": "https://arxiv.org/pdf/2303.18223.pdf",
            "description": "A Survey of Large Language Models - Academic Research Paper",
            "topics": ["llm", "ai", "machine_learning", "nlp", "research"],
            "document_type": "academic_paper",
            "industry": "technology"
        },
        "arxiv_transformer": {
            "url": "https://arxiv.org/pdf/1706.03762.pdf",
            "description": "Attention Is All You Need - Transformer Architecture Paper",
            "topics": ["ai", "transformer", "deep_learning", "nlp", "architecture"],
            "document_type": "academic_paper",
            "industry": "technology"
        },
        "nber_remote_work": {
            "url": "https://www.nber.org/system/files/working_papers/w30292/w30292.pdf",
            "description": "NBER Working Paper: The Evolution of Working from Home",
            "topics": ["remote_work", "hybrid", "productivity", "workforce", "workplace"],
            "document_type": "academic_paper",
            "industry": "human_resources"
        }
    }
    
    @classmethod
    def get_all_documents(cls) -> Dict:
        """Return all documents from all categories."""
        all_docs = {}
        all_docs.update(cls.SEC_FILINGS)
        all_docs.update(cls.GOVERNMENT_REPORTS)
        all_docs.update(cls.INTERNATIONAL_REPORTS)
        all_docs.update(cls.INDUSTRY_REPORTS)
        all_docs.update(cls.ACADEMIC_RESEARCH)
        return all_docs
    
    @classmethod
    def find_relevant_document(cls, action: str, object_type: str, 
                               scenario: str, prompt_text: str) -> Optional[Dict]:
        """
        Find the most relevant public document for a given prompt.
        Uses keyword matching, industry matching, and semantic relevance scoring.
        """
        all_docs = cls.get_all_documents()
        prompt_lower = f"{action} {object_type} {scenario} {prompt_text}".lower()
        
        best_match = None
        best_score = 0
        
        for doc_id, doc_info in all_docs.items():
            score = 0
            
            # Score based on topic matches (higher weight)
            for topic in doc_info.get("topics", []):
                topic_lower = topic.lower().replace("_", " ")
                if topic_lower in prompt_lower:
                    score += 15
                # Partial match
                for word in topic_lower.split():
                    if len(word) > 3 and word in prompt_lower:
                        score += 5
            
            # Score based on industry match
            industry = doc_info.get("industry", "").lower()
            if industry and industry in prompt_lower:
                score += 20
            
            # Score based on description keyword matches
            desc_lower = doc_info.get("description", "").lower()
            for word in prompt_lower.split():
                if len(word) > 4 and word in desc_lower:
                    score += 3
            
            # Boost for action-specific document types
            doc_type = doc_info.get("document_type", "")
            if action.upper() in ["SUMMARIZE", "ANALYZE", "REVIEW", "EXPLAIN"]:
                if doc_type in ["annual_report", "industry_report", "economic_report", "government_report"]:
                    score += 20
            
            if action.upper() in ["GET", "FIND", "SEARCH", "RESEARCH"]:
                if doc_type in ["academic_paper", "industry_report", "government_report"]:
                    score += 15
            
            if action.upper() in ["COMPARE", "EVALUATE", "ASSESS"]:
                if doc_type in ["industry_report", "annual_report"]:
                    score += 15
            
            # Scenario-specific boosts
            scenario_lower = scenario.lower() if scenario else ""
            if "budget" in scenario_lower or "financial" in scenario_lower:
                if doc_type in ["annual_report", "economic_report"]:
                    score += 10
            if "compliance" in scenario_lower or "audit" in scenario_lower:
                if doc_type in ["government_report", "annual_report"]:
                    score += 10
            if "client" in scenario_lower:
                if doc_type in ["industry_report", "annual_report"]:
                    score += 10
            
            if score > best_score:
                best_score = score
                best_match = {"id": doc_id, **doc_info}
        
        # Only return if we have a reasonable match
        if best_score >= 15:
            return best_match
        return None


# =============================================================================
# RICH SYNTHETIC CONTEXT GENERATOR
# =============================================================================

class RichContextGenerator:
    """
    Generates detailed, realistic synthetic context documents when
    no suitable public document is available.
    
    Context types:
    - Business Reports (quarterly reviews, project status, financials)
    - Meeting Notes (detailed with agendas, discussions, action items)
    - Email Threads (multi-party conversations with context)
    - Policy Documents (procedures, guidelines, compliance)
    - Technical Documentation (specs, architecture, implementation)
    - Proposals (project proposals, budget requests, RFPs)
    """
    
    # Company and project context for realistic scenarios
    COMPANIES = ["Contoso Corp", "Fabrikam Inc", "Northwind Traders", 
                 "Adventure Works", "Wide World Importers", "Tailwind Traders"]
    
    DEPARTMENTS = ["Engineering", "Product Management", "Marketing", "Sales",
                   "Finance", "Human Resources", "Operations", "IT", "Legal",
                   "Customer Success", "Research & Development", "Strategy"]
    
    PROJECTS = ["Digital Transformation Initiative", "Cloud Migration Program",
                "Customer Experience Platform", "Data Analytics Modernization",
                "Security Enhancement Project", "Mobile App Redesign",
                "AI Integration Pilot", "Process Automation Initiative"]
    
    NAMES = [
        ("Sarah", "Chen"), ("Marcus", "Johnson"), ("Emily", "Rodriguez"),
        ("David", "Kim"), ("Lisa", "Thompson"), ("James", "Wilson"),
        ("Jennifer", "Martinez"), ("Michael", "Brown"), ("Amanda", "Davis"),
        ("Robert", "Garcia"), ("Michelle", "Lee"), ("Christopher", "Taylor")
    ]
    
    @classmethod
    def generate_context(cls, action: str, object_type: str, 
                        scenario: str, prompt_text: str,
                        seed: Optional[int] = None) -> str:
        """
        Generate appropriate synthetic context based on the prompt characteristics.
        Returns a detailed, realistic document (1-2 pages, 500-1000 words).
        """
        if seed:
            random.seed(seed)
        
        action_upper = action.upper() if action else ""
        
        # Determine context type based on action and object
        if action_upper in ["SUMMARIZE", "REVIEW", "ANALYZE"]:
            return cls._generate_analysis_document(object_type, scenario, prompt_text)
        elif action_upper in ["EXPLAIN", "DESCRIBE"]:
            return cls._generate_explanatory_document(object_type, scenario, prompt_text)
        elif action_upper in ["CREATE", "WRITE", "DRAFT"]:
            return cls._generate_reference_materials(object_type, scenario, prompt_text)
        elif action_upper in ["FIND", "GET", "SEARCH"]:
            return cls._generate_data_context(object_type, scenario, prompt_text)
        elif action_upper in ["SUGGEST", "RECOMMEND", "ADVISE"]:
            return cls._generate_situation_context(object_type, scenario, prompt_text)
        elif action_upper in ["PREPARE", "ORGANIZE", "PLAN"]:
            return cls._generate_planning_context(object_type, scenario, prompt_text)
        elif action_upper in ["COMPARE", "EVALUATE", "ASSESS"]:
            return cls._generate_comparison_data(object_type, scenario, prompt_text)
        else:
            return cls._generate_general_business_context(object_type, scenario, prompt_text)
    
    @classmethod
    def _get_random_company(cls) -> str:
        return random.choice(cls.COMPANIES)
    
    @classmethod
    def _get_random_department(cls) -> str:
        return random.choice(cls.DEPARTMENTS)
    
    @classmethod
    def _get_random_project(cls) -> str:
        return random.choice(cls.PROJECTS)
    
    @classmethod
    def _get_random_person(cls) -> Tuple[str, str, str]:
        first, last = random.choice(cls.NAMES)
        title = random.choice(["Director", "Manager", "Senior Manager", 
                              "Vice President", "Lead", "Principal"])
        return first, last, title
    
    @classmethod
    def _generate_analysis_document(cls, object_type: str, scenario: str, prompt: str) -> str:
        """Generate a detailed document suitable for analysis/summary tasks."""
        company = cls._get_random_company()
        project = cls._get_random_project()
        dept = cls._get_random_department()
        author_first, author_last, author_title = cls._get_random_person()
        
        date = "January 6, 2026"
        
        document = f"""QUARTERLY BUSINESS REVIEW REPORT
================================
Company: {company}
Department: {dept}
Project: {project}
Report Date: {date}
Prepared By: {author_first} {author_last}, {author_title} of {dept}

EXECUTIVE SUMMARY
-----------------
This report provides a comprehensive review of {project} performance for Q4 2025. The initiative, which began in Q2 2025, has made significant progress toward its strategic objectives while encountering several challenges that require leadership attention.

Key highlights include:
• Overall project completion: 78% (target: 85%)
• Budget utilization: $2.4M of $3.1M allocated (77%)
• Team headcount: 24 FTEs across 4 workstreams
• Customer satisfaction improvement: +18 NPS points since baseline
• Technical debt reduction: 34% decrease in critical issues

PERFORMANCE METRICS
-------------------

1. Financial Performance
   - Total spend to date: $2,412,500
   - Forecasted year-end spend: $3,050,000 (within budget)
   - Cost savings realized: $450,000 (infrastructure optimization)
   - ROI projection: 2.3x within 18 months

2. Timeline Status
   | Milestone               | Target Date  | Status    | Notes                    |
   |------------------------|--------------|-----------|--------------------------|
   | Phase 1 - Foundation   | Aug 15, 2025 | Complete  | Delivered on schedule    |
   | Phase 2 - Core Build   | Oct 30, 2025 | Complete  | 2 weeks delayed          |
   | Phase 3 - Integration  | Dec 15, 2025 | In Progress| On track                 |
   | Phase 4 - Rollout      | Feb 28, 2026 | Planned   | Requires resource review |

3. Quality Metrics
   - Defect density: 0.8 per 1000 lines of code (target: <1.0)
   - Automated test coverage: 82%
   - Production incidents: 3 P2, 0 P1 in Q4
   - Mean time to resolution: 4.2 hours

WORKSTREAM UPDATES
------------------

Workstream 1: Platform Infrastructure
Lead: Marcus Johnson, Principal Engineer
Status: GREEN
- Successfully migrated 85% of workloads to cloud infrastructure
- Achieved 99.95% uptime in production environments
- Implemented auto-scaling for peak demand periods
- Next milestone: Complete disaster recovery testing by Jan 20

Workstream 2: User Experience
Lead: Emily Rodriguez, Design Director
Status: YELLOW
- New interface designs approved by stakeholder committee
- Accessibility audit completed with 4 critical findings being addressed
- User research shows 72% preference for new navigation model
- Risk: Mobile optimization behind schedule by 2 weeks

Workstream 3: Data Integration
Lead: David Kim, Data Architecture Lead
Status: GREEN
- Connected 12 of 15 source systems to unified data platform
- Real-time analytics dashboard operational
- Data quality score improved from 78% to 91%
- Remaining integrations scheduled for completion by Jan 30

Workstream 4: Change Management
Lead: Lisa Thompson, Change Management Lead
Status: YELLOW
- Training program developed for 500+ end users
- Completed 8 of 12 department briefings
- Resistance identified in 2 business units requiring additional engagement
- Communication plan execution at 65%

RISKS AND ISSUES
----------------

HIGH PRIORITY RISKS:
1. Resource Constraint (Probability: HIGH, Impact: MEDIUM)
   - Two senior engineers departing in January
   - Mitigation: Accelerated hiring and knowledge transfer underway
   
2. Vendor Dependency (Probability: MEDIUM, Impact: HIGH)
   - Third-party API provider experiencing reliability issues
   - Mitigation: Evaluating alternative vendors, contingency plans in place

3. Scope Creep (Probability: MEDIUM, Impact: MEDIUM)
   - 5 new feature requests from business stakeholders
   - Mitigation: Change control board reviewing priorities

OPEN ISSUES:
- License renewal for analytics platform pending procurement review
- Security certification scheduled but not confirmed
- Integration testing environment needs capacity upgrade

RECOMMENDATIONS
---------------

1. Approve additional $150,000 for contract resources to address staffing gap
2. Expedite procurement decision on analytics platform licensing
3. Schedule executive sponsor review session for February priorities
4. Consider Phase 4 timeline extension of 2 weeks to ensure quality

NEXT STEPS
----------
• Weekly status reviews continue every Tuesday at 10 AM
• Monthly steering committee update scheduled for January 15
• Phase 3 completion checkpoint on January 20
• Resource planning workshop on January 8

APPENDIX
--------
A. Detailed financial breakdown by workstream
B. Risk register with full mitigation details
C. Stakeholder feedback summary
D. Technical architecture diagrams

---
Report Distribution: Executive Leadership, Project Steering Committee, Department Heads
Classification: Internal Use Only
Next Update: February 5, 2026
"""
        return document
    
    @classmethod
    def _generate_explanatory_document(cls, object_type: str, scenario: str, prompt: str) -> str:
        """Generate a document suitable for explanation tasks."""
        company = cls._get_random_company()
        
        document = f"""TECHNICAL OVERVIEW DOCUMENT
===========================
Organization: {company}
Subject: Cloud Infrastructure and AI Services Architecture
Version: 2.1
Last Updated: January 3, 2026

INTRODUCTION
------------
This document provides a comprehensive overview of our cloud infrastructure and AI services architecture. It is intended for stakeholders who need to understand the technical foundations of our digital transformation initiatives.

ARCHITECTURE OVERVIEW
---------------------

1. Cloud Foundation Layer

Our infrastructure is built on a hybrid cloud architecture that combines:
- Public cloud services (Azure, AWS) for scalable compute and storage
- Private cloud environments for sensitive data and compliance requirements
- Edge computing nodes for low-latency processing needs

Key Components:
• Compute: Kubernetes clusters with auto-scaling (50-500 nodes)
• Storage: Distributed object storage with 99.999% durability
• Networking: Software-defined networking with microsegmentation
• Security: Zero-trust architecture with continuous verification

2. Data Platform Layer

The data platform enables enterprise-wide analytics and AI capabilities:
- Data Lake: Centralized repository for structured and unstructured data
- Data Warehouse: Optimized for business intelligence and reporting
- Real-time Streaming: Event-driven architecture for live data processing
- Data Catalog: Governance and discovery tools for data assets

Data Volume Statistics:
- Total data under management: 2.4 petabytes
- Daily data ingestion: 850 GB average
- Active data pipelines: 340
- Data quality score: 94%

3. AI and Machine Learning Layer

Our AI capabilities are organized into three tiers:

Tier 1 - Foundation Models
- Large language models for natural language processing
- Computer vision models for image and video analysis
- Speech recognition and synthesis capabilities

Tier 2 - Domain-Specific Models
- Customer churn prediction (92% accuracy)
- Demand forecasting (MAPE: 8.5%)
- Fraud detection (97% precision, 89% recall)
- Document classification and extraction

Tier 3 - Application Layer
- Intelligent search and recommendations
- Automated customer service agents
- Predictive maintenance systems
- Quality inspection automation

4. Integration Layer

The integration layer connects our systems through:
- API Gateway: 500+ internal and external APIs
- Event Bus: Apache Kafka-based messaging (2M events/day)
- ETL Pipelines: Scheduled and real-time data transformations
- Connector Library: 50+ pre-built integrations

SECURITY AND COMPLIANCE
-----------------------

Security Controls:
- Identity: Azure AD with MFA for all users
- Access: Role-based access control with just-in-time provisioning
- Encryption: AES-256 for data at rest, TLS 1.3 for data in transit
- Monitoring: 24/7 SOC with SIEM integration

Compliance Certifications:
- SOC 2 Type II (renewed annually)
- ISO 27001 (certified through 2027)
- GDPR compliance framework
- HIPAA for healthcare data handling

PERFORMANCE AND RELIABILITY
---------------------------

Current Performance Metrics:
- System availability: 99.97% (trailing 12 months)
- API response time P95: 145ms
- Error rate: 0.02%
- Recovery time objective: 4 hours
- Recovery point objective: 1 hour

FUTURE ROADMAP
--------------

Q1 2026: Enhanced AI capabilities with generative AI integration
Q2 2026: Multi-region disaster recovery implementation
Q3 2026: Edge computing expansion to 15 new locations
Q4 2026: Zero-trust network architecture completion

CONTACT INFORMATION
-------------------
Architecture Team: architecture@{company.lower().replace(' ', '')}.com
Support: infrastructure-support@{company.lower().replace(' ', '')}.com
Documentation Portal: https://docs.internal.{company.lower().replace(' ', '')}.com/architecture

---
Document Owner: Chief Technology Officer
Review Cycle: Quarterly
"""
        return document
    
    @classmethod
    def _generate_reference_materials(cls, object_type: str, scenario: str, prompt: str) -> str:
        """Generate reference materials for content creation tasks."""
        company = cls._get_random_company()
        
        document = f"""CONTENT BRIEF AND REFERENCE MATERIALS
======================================
Project: {object_type if object_type else "Communication Development"}
Client/Stakeholder: {company}
Date: January 6, 2026

PURPOSE
-------
This brief provides background information, key messages, and reference data to support content development. Use this information to ensure accuracy and alignment with organizational messaging.

KEY MESSAGES
------------

Primary Message:
"Our commitment to innovation drives measurable value for our customers and stakeholders through technology-enabled solutions that transform how businesses operate."

Supporting Messages:
1. Digital transformation is not just about technology—it's about enabling people to do their best work
2. Our solutions deliver proven ROI with an average 30% improvement in operational efficiency
3. We prioritize security and compliance at every layer of our technology stack
4. Our customer-first approach means we build what businesses need, not just what's technically interesting

AUDIENCE PROFILE
----------------

Primary Audience: Executive Decision Makers
- Title levels: VP, SVP, C-Suite
- Key concerns: ROI, risk management, competitive advantage, time to value
- Preferred format: Concise, data-driven, strategic perspective

Secondary Audience: Technical Evaluators
- Title levels: Directors, Architects, Senior Engineers
- Key concerns: Integration, security, scalability, support
- Preferred format: Detailed specifications, architecture diagrams, case studies

FACTS AND FIGURES
-----------------

Company Statistics:
• Founded: 2008
• Employees: 4,500+ globally
• Customers: 2,800+ enterprise clients
• Annual Revenue: $1.2B (FY2025)
• Year-over-Year Growth: 28%

Product/Service Metrics:
• Platform uptime: 99.97%
• Customer satisfaction score: 4.6/5.0
• Implementation success rate: 94%
• Average time to value: 6 weeks

Customer Success Highlights:
• Fortune 500 client achieved 45% reduction in processing time
• Healthcare customer improved patient outcomes by 22%
• Financial services firm reduced compliance costs by $2.3M annually
• Retail customer increased online conversion by 18%

COMPETITIVE POSITIONING
-----------------------

Differentiators:
1. Integrated platform vs. point solutions
2. Industry-specific accelerators and templates
3. Dedicated customer success team
4. Flexible deployment options (cloud, hybrid, on-premise)

Competitive Landscape:
| Competitor    | Strength          | Our Advantage           |
|--------------|-------------------|-------------------------|
| Competitor A | Market presence   | Better integration      |
| Competitor B | Lower price point | Superior support        |
| Competitor C | Specific feature  | Broader platform        |

BRAND GUIDELINES
----------------

Voice and Tone:
- Professional but approachable
- Confident without being arrogant
- Clear and jargon-free where possible
- Forward-looking and optimistic

Visual Identity:
- Primary colors: Blue (#0078D4), White, Light Gray
- Typography: Segoe UI for digital, Segoe for print
- Photography: Diverse, modern, authentic workplace settings

LEGAL AND COMPLIANCE NOTES
--------------------------

Required Disclaimers:
- All statistics should include "results may vary" where appropriate
- Forward-looking statements require standard SEC disclaimer
- Customer references require written approval before publication
- Third-party trademarks must include proper attribution

Approval Process:
1. Marketing review for brand alignment
2. Legal review for compliance
3. Subject matter expert validation
4. Final approval from communications director

REFERENCE DOCUMENTS
-------------------

Available upon request:
• Annual Report 2025 (PDF)
• Customer Case Studies Collection
• Product Technical Specifications
• Brand Guidelines Manual (v4.2)
• Competitive Analysis Report (Q4 2025)

CONTACT FOR QUESTIONS
---------------------
Content Lead: marketing-content@{company.lower().replace(' ', '')}.com
Brand Guidelines: brand-team@{company.lower().replace(' ', '')}.com
Legal Review: legal-marketing@{company.lower().replace(' ', '')}.com

---
This brief is confidential and intended for internal use only.
"""
        return document
    
    @classmethod
    def _generate_data_context(cls, object_type: str, scenario: str, prompt: str) -> str:
        """Generate data/information context for search/find tasks."""
        company = cls._get_random_company()
        
        document = f"""DATA REPOSITORY AND INFORMATION SOURCES
========================================
Organization: {company}
Compiled: January 6, 2026

AVAILABLE DATA SOURCES
----------------------

1. Customer Data Platform (CDP)
   Location: https://data.internal.{company.lower().replace(' ', '')}.com/cdp
   Contains:
   - Customer profiles (500,000+ records)
   - Transaction history (24 months)
   - Interaction logs (email, chat, phone)
   - Segmentation models and scores
   - Consent and preference data
   
   Key Metrics Available:
   - Customer Lifetime Value (CLV)
   - Net Promoter Score (NPS) by segment
   - Churn risk indicators
   - Product affinity scores

2. Financial Data Warehouse
   Location: https://data.internal.{company.lower().replace(' ', '')}.com/finance
   Contains:
   - General ledger data (7 years)
   - Revenue by product, region, segment
   - Cost center allocations
   - Budget vs. actual comparisons
   - Forecasting models
   
   Report Availability:
   - Monthly close reports (T+5 days)
   - Quarterly financial packages
   - Annual audit documentation
   - Board presentation materials

3. Operational Metrics Database
   Location: https://data.internal.{company.lower().replace(' ', '')}.com/ops
   Contains:
   - Manufacturing throughput data
   - Supply chain metrics
   - Inventory levels and turns
   - Quality control measurements
   - Equipment performance logs
   
   Real-time Dashboards:
   - Production line status
   - Order fulfillment tracking
   - Logistics and shipping
   - Vendor performance

4. HR Information System
   Location: https://data.internal.{company.lower().replace(' ', '')}.com/hris
   Contains:
   - Employee demographics (anonymized for reports)
   - Headcount by department/location
   - Turnover and retention metrics
   - Training and development records
   - Performance rating distributions
   
   Standard Reports:
   - Monthly headcount summary
   - Diversity metrics dashboard
   - Skills inventory
   - Succession planning data

5. Market Intelligence Database
   Location: https://data.internal.{company.lower().replace(' ', '')}.com/market
   Contains:
   - Industry analyst reports
   - Competitive intelligence
   - Market sizing and share data
   - Trend analysis and forecasts
   - Customer research studies
   
   External Sources Integrated:
   - Gartner, Forrester, IDC research
   - Industry trade publications
   - Social media sentiment analysis
   - Patent and innovation tracking

DATA ACCESS PROCEDURES
----------------------

Standard Access:
- All employees have read access to department-specific data
- Cross-functional data requires manager approval
- PII data requires additional training certification

Elevated Access:
- Executive dashboards: VP+ level
- Raw customer data: Privacy team approval required
- Financial audit data: Finance leadership only
- M&A related data: Deal team members only

Data Request Process:
1. Submit request via ServiceNow portal
2. Data steward reviews for appropriateness
3. Access provisioned within 2 business days
4. Quarterly access reviews for compliance

DATA QUALITY INFORMATION
------------------------

Quality Metrics by Source:
| Source        | Completeness | Accuracy | Timeliness |
|--------------|--------------|----------|------------|
| CDP          | 94%          | 97%      | Real-time  |
| Finance      | 99%          | 99.9%    | T+1 day    |
| Operations   | 91%          | 95%      | Real-time  |
| HR           | 98%          | 99%      | Daily      |
| Market Intel | 85%          | 90%      | Weekly     |

Known Data Issues:
- Legacy system migration in progress (affects some 2022-2023 data)
- International subsidiary data may have 48-hour delay
- Some market data requires manual verification

SUPPORT CONTACTS
----------------
Data Platform Support: data-support@{company.lower().replace(' ', '')}.com
Data Governance Team: data-governance@{company.lower().replace(' ', '')}.com
Analytics Center of Excellence: analytics-coe@{company.lower().replace(' ', '')}.com

---
This document is updated monthly. Last review: January 1, 2026
"""
        return document
    
    @classmethod
    def _generate_situation_context(cls, object_type: str, scenario: str, prompt: str) -> str:
        """Generate situational context for advice/recommendation tasks."""
        company = cls._get_random_company()
        project = cls._get_random_project()
        person_first, person_last, person_title = cls._get_random_person()
        
        document = f"""SITUATION BRIEFING DOCUMENT
============================
Organization: {company}
Prepared For: {person_first} {person_last}, {person_title}
Date: January 6, 2026
Subject: Decision Support for {project}

CURRENT SITUATION
-----------------

Background:
{company} is at a critical juncture with the {project}. After 18 months of development and $4.2M investment, we face a key decision point that will determine the trajectory of this initiative and potentially impact broader organizational strategy.

The project was initiated to address declining operational efficiency (down 12% over 3 years) and increasing competitive pressure from digital-native competitors. Initial objectives included:
- Modernize core technology infrastructure
- Improve customer experience and satisfaction
- Reduce operational costs by 25%
- Enable new revenue streams through digital channels

Current Status:
- Technical platform: 70% complete, stable in testing environment
- Organizational readiness: 55% (training and change management in progress)
- Budget: 15% over original estimate ($4.2M vs. $3.6M planned)
- Timeline: 3 months behind original schedule

KEY STAKEHOLDERS AND PERSPECTIVES
----------------------------------

Stakeholder Map:

1. CEO - Jennifer Martinez
   Position: Strongly supportive
   Concerns: ROI timeline, board expectations, competitive positioning
   Influence: Ultimate decision authority

2. CFO - Robert Garcia
   Position: Cautiously supportive
   Concerns: Budget overrun, capital allocation, payback period
   Influence: Controls additional funding approval

3. COO - Lisa Thompson
   Position: Mixed
   Concerns: Operational disruption, team bandwidth, implementation risk
   Influence: Owns operational deployment

4. CTO - David Kim
   Position: Strongly supportive
   Concerns: Technical debt, integration complexity, talent retention
   Influence: Technical direction and architecture

5. VP Sales - Michael Brown
   Position: Impatient
   Concerns: Customer commitments, competitive wins/losses, sales enablement
   Influence: Revenue impact and customer relationships

OPTIONS UNDER CONSIDERATION
---------------------------

Option A: Continue as Planned
- Complete remaining development on current timeline
- Full rollout by Q3 2026
- Additional budget required: $800K
- Risk: Medium (known challenges, proven approach)

Option B: Accelerated Timeline
- Increase team size, compress timeline by 2 months
- Full rollout by Q2 2026
- Additional budget required: $1.4M
- Risk: High (team burnout, quality concerns)

Option C: Phased Rollout
- Deploy core functionality immediately
- Add advanced features in subsequent phases
- Full functionality by Q4 2026
- Additional budget required: $600K
- Risk: Low (reduced scope per phase)

Option D: Pivot to SaaS Solution
- Abandon custom development
- Implement third-party platform
- Deployment by Q2 2026
- Cost: $1.5M implementation + $800K annual licensing
- Risk: Medium (vendor dependency, customization limits)

RELEVANT DATA AND ANALYSIS
--------------------------

Financial Projections (5-year NPV):
| Option | Investment | NPV      | IRR   | Payback |
|--------|-----------|----------|-------|---------|
| A      | $5.0M     | $8.2M    | 28%   | 2.8 yrs |
| B      | $5.6M     | $9.4M    | 32%   | 2.4 yrs |
| C      | $4.8M     | $7.1M    | 24%   | 3.1 yrs |
| D      | $5.5M*    | $6.8M    | 22%   | 3.4 yrs |
*Includes 5 years of licensing

Competitive Intelligence:
- Competitor X launched similar platform 6 months ago, taking 3% market share
- Competitor Y announced major investment in digital transformation
- Industry analysts predict 40% of laggards will lose significant share by 2028

Customer Feedback:
- 78% of surveyed customers expressed interest in enhanced digital capabilities
- 45% indicated they would consider switching to competitor with better technology
- Key accounts have explicitly tied renewal discussions to our digital roadmap

CONSTRAINTS AND DEPENDENCIES
----------------------------

Hard Constraints:
- Q3 2026: Major customer contract renewal requiring new capabilities
- Q2 2026: Regulatory compliance deadline for data handling
- Budget ceiling: $6M without board approval

Dependencies:
- Cloud infrastructure migration (in progress, 80% complete)
- API modernization project (scheduled completion: Feb 2026)
- Security certification renewal (due: March 2026)
- Key hire for data engineering lead (currently in interview process)

RECOMMENDATION REQUEST
----------------------

The leadership team seeks input on:
1. Which option best balances risk, return, and strategic alignment?
2. What factors should weigh most heavily in this decision?
3. Are there hybrid approaches that combine elements of multiple options?
4. What mitigation strategies should accompany the chosen path?

---
Prepared by: Strategic Planning Office
Distribution: Executive Leadership Team
Classification: Confidential - Internal Use Only
"""
        return document
    
    @classmethod
    def _generate_planning_context(cls, object_type: str, scenario: str, prompt: str) -> str:
        """Generate context for planning and organization tasks."""
        company = cls._get_random_company()
        
        document = f"""PLANNING AND RESOURCE GUIDE
============================
Organization: {company}
Purpose: Event/Project/Initiative Planning Support
Date: January 6, 2026

AVAILABLE RESOURCES
-------------------

1. Venue and Facilities
   
   Internal Facilities:
   - Main Conference Center: Capacity 200, A/V equipped, catering available
   - Training Rooms (6): Capacity 20-30 each, video conferencing
   - Executive Boardroom: Capacity 16, premium A/V, private catering
   - Town Hall Space: Capacity 500, standing; 300 seated
   
   Preferred External Venues:
   - Downtown Convention Center: 1,000+ capacity, 3 miles from HQ
   - Marriott Conference Hotel: Multiple room configurations, catering included
   - The Innovation Hub: Tech-focused venue, 150 capacity, modern aesthetic

2. Budget Guidelines
   
   Standard Allocations:
   | Event Type          | Budget Range    | Approval Level    |
   |---------------------|-----------------|-------------------|
   | Team meeting        | $500-$2,000     | Manager           |
   | Department event    | $2,000-$10,000  | Director          |
   | Company-wide event  | $10,000-$50,000 | VP                |
   | Major conference    | $50,000+        | Executive sponsor |
   
   Cost Benchmarks:
   - Catering (lunch): $25-45 per person
   - Catering (dinner reception): $60-100 per person
   - A/V rental (basic): $500-1,500 per day
   - Speaker honorarium: $2,000-10,000 typical range
   - Swag/materials: $15-30 per attendee

3. Vendor Preferred List
   
   Catering:
   - Fresh Start Catering (sustainable, dietary accommodations)
   - Corporate Cuisine (traditional, reliable)
   - Global Flavors (international options)
   
   A/V and Production:
   - TechEvents Pro (full service, expensive but reliable)
   - MediaWorks (mid-range, good support)
   - Internal A/V Team (basic needs, cost-effective)
   
   Printing and Materials:
   - PrintFast Solutions (quick turnaround)
   - Sustainable Print Co. (eco-friendly)
   - In-house Print Center (limited capacity)

4. Staffing and Support
   
   Internal Resources:
   - Events Team: 3 FTEs, can support 2-3 major events per quarter
   - Communications: Content creation, internal promotion
   - IT: Technical setup, live streaming, recording
   - Facilities: Room setup, logistics, security
   
   Volunteer Pool:
   - 45 trained event volunteers across departments
   - Coordination through HR Community program
   - Volunteer appreciation: gift cards, recognition

PLANNING TEMPLATES
------------------

Available in SharePoint:
- Event Planning Checklist (by event type)
- Budget Request Template
- Vendor Comparison Matrix
- Post-Event Survey (customizable)
- Communication Timeline Template
- Risk Assessment Worksheet
- Attendee Management Tracker

TIMELINE GUIDELINES
-------------------

Recommended Lead Times:
| Event Scale       | Minimum Lead Time |
|-------------------|-------------------|
| Small (<30)       | 2-3 weeks         |
| Medium (30-100)   | 4-6 weeks         |
| Large (100-300)   | 8-12 weeks        |
| Major (300+)      | 16+ weeks         |

Key Milestones Template:
- T-12 weeks: Secure venue, set date, establish budget
- T-8 weeks: Finalize agenda, confirm speakers/presenters
- T-6 weeks: Launch invitations/registration
- T-4 weeks: Finalize catering, A/V, materials orders
- T-2 weeks: Confirm attendance, finalize logistics
- T-1 week: Final walkthrough, communications push
- T+1 week: Post-event survey, debrief, expense reconciliation

POLICIES AND COMPLIANCE
-----------------------

Required Elements:
- Accessibility accommodations must be offered
- Dietary restrictions survey required for catered events
- Security notification for 100+ attendees
- Insurance certificate for external venues
- Photography release notices required

Prohibited:
- Alcohol at company-sponsored events requires VP approval
- No branded items from non-approved vendors
- External speakers must sign NDA for internal content

CONTACTS AND SUPPORT
--------------------
Events Team Lead: events@{company.lower().replace(' ', '')}.com
Facilities Booking: facilities@{company.lower().replace(' ', '')}.com
Budget Questions: finance-events@{company.lower().replace(' ', '')}.com
Communications Support: internal-comms@{company.lower().replace(' ', '')}.com

---
This guide is updated quarterly. Current version: Q1 2026
"""
        return document
    
    @classmethod
    def _generate_comparison_data(cls, object_type: str, scenario: str, prompt: str) -> str:
        """Generate comparative data for evaluation tasks."""
        return cls._generate_analysis_document(object_type, scenario, prompt)
    
    @classmethod
    def _generate_general_business_context(cls, object_type: str, scenario: str, prompt: str) -> str:
        """Generate general business context for miscellaneous tasks."""
        company = cls._get_random_company()
        dept = cls._get_random_department()
        
        document = f"""DEPARTMENTAL INFORMATION SHEET
===============================
Organization: {company}
Department: {dept}
Effective Date: January 1, 2026

DEPARTMENT OVERVIEW
-------------------

Mission: To deliver excellence in {dept.lower()} functions that enable {company}'s strategic objectives and support our employees, customers, and stakeholders.

Vision: Be recognized as a best-in-class {dept.lower()} organization that drives innovation and operational excellence.

Leadership:
- Department Head: Reports to C-Suite executive
- Direct reports: 4-6 functional managers
- Total headcount: 45 FTEs + 8 contractors

CURRENT PRIORITIES (Q1 2026)
----------------------------

Priority 1: Operational Excellence
- Streamline core processes to improve efficiency by 15%
- Implement new workflow automation tools
- Reduce average cycle time by 20%
- Success metric: Customer satisfaction score ≥4.5/5.0

Priority 2: Talent Development
- Complete skills assessment for all team members
- Launch development program for high-potential employees
- Reduce voluntary turnover to below 10%
- Improve engagement scores by 8 points

Priority 3: Technology Modernization
- Complete Phase 2 of system upgrade project
- Migrate remaining legacy applications to cloud
- Implement enhanced reporting and analytics
- Achieve 99.5% system availability

Priority 4: Cost Optimization
- Identify 10% cost savings opportunities
- Renegotiate key vendor contracts
- Consolidate redundant tools and systems
- Stay within allocated budget of $8.2M

KEY METRICS AND PERFORMANCE
---------------------------

Current Performance Dashboard:

| Metric                  | Target | Actual | Status |
|-------------------------|--------|--------|--------|
| Process efficiency      | 85%    | 82%    | ⚠️     |
| Quality score           | 95%    | 96%    | ✅     |
| Budget utilization      | 100%   | 94%    | ✅     |
| Employee satisfaction   | 4.2    | 4.0    | ⚠️     |
| Stakeholder satisfaction| 4.5    | 4.4    | ✅     |
| Project delivery on-time| 90%    | 87%    | ⚠️     |

Year-over-Year Comparison:
- Productivity improved 8% vs. prior year
- Costs reduced 5% through automation
- Customer complaints down 22%
- Employee engagement up 3 points

TEAM STRUCTURE
--------------

Functional Groups:
1. Operations (18 FTEs)
   - Core service delivery
   - Process management
   - Quality assurance

2. Strategy & Planning (8 FTEs)
   - Strategic initiatives
   - Program management
   - Analytics and reporting

3. Technology (12 FTEs)
   - Systems administration
   - Development and integration
   - Support and maintenance

4. Business Partners (7 FTEs)
   - Stakeholder relationship management
   - Requirements gathering
   - Change management

KEY CONTACTS
------------
Department Admin: {dept.lower()}-admin@{company.lower().replace(' ', '')}.com
Leadership Team: {dept.lower()}-leadership@{company.lower().replace(' ', '')}.com
Support Queue: {dept.lower()}-support@{company.lower().replace(' ', '')}.com

RELATED RESOURCES
-----------------
- Department SharePoint: https://sharepoint.{company.lower().replace(' ', '')}.com/{dept.lower()}
- Knowledge Base: https://kb.{company.lower().replace(' ', '')}.com/{dept.lower()}
- Training Portal: https://learn.{company.lower().replace(' ', '')}.com

---
Document Owner: {dept} Leadership Team
Review Cycle: Quarterly
Next Update: April 1, 2026
"""
        return document


# =============================================================================
# MAIN CONTEXT ENHANCEMENT PROCESSOR
# =============================================================================

class ContextEnhancer:
    """
    Main processor that reads V3 prompts and enhances them with context.
    """
    
    # Actions that typically need context documents
    CONTEXT_REQUIRED_ACTIONS = {
        "SUMMARIZE", "EXPLAIN", "REVIEW", "ANALYZE", "ASSESS", "EVALUATE",
        "PROOFREAD", "EDIT", "TRANSLATE", "REWRITE", "CRITIQUE", "DIGEST"
    }
    
    # Actions that benefit from reference context
    CONTEXT_HELPFUL_ACTIONS = {
        "CREATE", "WRITE", "DRAFT", "PREPARE", "COMPOSE", "GENERATE",
        "SUGGEST", "RECOMMEND", "ADVISE", "HELP", "GUIDE",
        "FIND", "GET", "SEARCH", "LOOK", "LOCATE",
        "COMPARE", "CONTRAST", "DIFFERENTIATE",
        "PLAN", "ORGANIZE", "SCHEDULE", "PRIORITIZE"
    }
    
    def __init__(self, input_csv_path: str, output_dir: str = "synthetic_prompts"):
        self.input_path = Path(input_csv_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.doc_repo = PublicDocumentRepository()
        self.context_gen = RichContextGenerator()
        self.stats = {
            "total_processed": 0,
            "public_doc_added": 0,
            "synthetic_context_added": 0,
            "existing_context_kept": 0,
            "no_context_needed": 0
        }
    
    def process(self) -> Tuple[str, str]:
        """
        Process the input CSV and add context to each row.
        Returns paths to output CSV and JSON files.
        """
        print(f"Reading input file: {self.input_path}")
        
        rows = []
        with open(self.input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
        
        print(f"Loaded {len(rows)} prompts")
        
        # Add new columns if not present
        new_columns = ["context_url", "context_source_type"]
        for col in new_columns:
            if col not in fieldnames:
                fieldnames = list(fieldnames) + [col]
        
        # Process each row
        enhanced_rows = []
        for i, row in enumerate(rows):
            enhanced_row = self._enhance_row(row, i)
            enhanced_rows.append(enhanced_row)
            
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(rows)} prompts...")
        
        # Generate output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = self.output_dir / f"synthetic_prompts_v4_enhanced_{timestamp}.csv"
        json_path = self.output_dir / f"synthetic_prompts_v4_enhanced_{timestamp}.json"
        
        # Write CSV
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enhanced_rows)
        
        print(f"Exported to: {csv_path}")
        
        # Write JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_rows, f, indent=2, ensure_ascii=False)
        
        print(f"Exported to: {json_path}")
        
        # Print statistics
        self._print_stats()
        
        return str(csv_path), str(json_path)
    
    def _enhance_row(self, row: Dict, index: int) -> Dict:
        """Enhance a single row with context."""
        self.stats["total_processed"] += 1
        
        action = row.get("input_action", "")
        object_type = row.get("input_object", "")
        scenario = row.get("prompt_scenario", "")
        prompt_text = row.get("synthetic_prompt", "")
        existing_context = row.get("context_text", "")
        
        # Check if context already exists and is substantial
        if existing_context and len(existing_context) > 500:
            row["context_source_type"] = "existing_synthetic"
            row["context_url"] = ""
            self.stats["existing_context_kept"] += 1
            return row
        
        action_upper = action.upper() if action else ""
        
        # Determine if this action needs context
        needs_context = action_upper in self.CONTEXT_REQUIRED_ACTIONS
        benefits_from_context = action_upper in self.CONTEXT_HELPFUL_ACTIONS
        
        if needs_context or benefits_from_context:
            # Try to find a relevant public document first
            public_doc = self.doc_repo.find_relevant_document(
                action, object_type, scenario, prompt_text
            )
            
            if public_doc:
                # Use public document URL as the context reference
                doc_url = public_doc["url"]
                doc_desc = public_doc["description"]
                doc_type = public_doc.get("document_type", "document")
                industry = public_doc.get("industry", "general")
                
                # Set the direct clickable URL
                row["context_url"] = doc_url
                row["context_source_type"] = "public_document"
                
                # Create rich reference text that includes the URL for visibility
                row["context_text"] = (
                    f"REFERENCE DOCUMENT\n"
                    f"==================\n"
                    f"Document: {doc_desc}\n"
                    f"Type: {doc_type.replace('_', ' ').title()}\n"
                    f"Industry: {industry.title()}\n"
                    f"\n"
                    f"Direct Download URL:\n"
                    f"{doc_url}\n"
                    f"\n"
                    f"Instructions: Use the document at the URL above as context for this task. "
                    f"Download or view the document to extract relevant information."
                )
                row["has_context_text"] = "Yes"
                self.stats["public_doc_added"] += 1
            else:
                # No suitable public doc found - generate rich synthetic context
                seed = hash(f"{row.get('synthetic_prompt_id', index)}_{prompt_text[:50]}")
                synthetic_context = self.context_gen.generate_context(
                    action, object_type, scenario, prompt_text, seed
                )
                row["context_text"] = synthetic_context
                row["context_source_type"] = "generated_synthetic"
                row["context_url"] = ""
                row["has_context_text"] = "Yes"
                self.stats["synthetic_context_added"] += 1
        else:
            # No context needed for this action type
            row["context_source_type"] = "none_required"
            row["context_url"] = ""
            if not row.get("has_context_text"):
                row["has_context_text"] = "No"
            self.stats["no_context_needed"] += 1
        
        return row
    
    def _print_stats(self):
        """Print processing statistics."""
        print("\n" + "=" * 60)
        print("CONTEXT ENHANCEMENT STATISTICS")
        print("=" * 60)
        print(f"Total prompts processed: {self.stats['total_processed']}")
        print(f"Public document URLs added: {self.stats['public_doc_added']}")
        print(f"Synthetic context generated: {self.stats['synthetic_context_added']}")
        print(f"Existing context preserved: {self.stats['existing_context_kept']}")
        print(f"No context needed: {self.stats['no_context_needed']}")
        print("=" * 60)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main entry point."""
    print("=" * 60)
    print("SYNTHETIC PROMPT CONTEXT ENHANCEMENT - V4")
    print("=" * 60)
    print()
    
    # Find the latest V3 output file
    output_dir = Path("synthetic_prompts")
    v3_files = list(output_dir.glob("synthetic_prompts_v3_*.csv"))
    
    if not v3_files:
        print("ERROR: No V3 synthetic prompts file found!")
        print("Please run the V3 generator first.")
        return
    
    # Use the most recent V3 file
    latest_v3 = max(v3_files, key=lambda p: p.stat().st_mtime)
    print(f"Using V3 input file: {latest_v3}")
    print()
    
    # Process and enhance
    enhancer = ContextEnhancer(str(latest_v3), "synthetic_prompts")
    csv_path, json_path = enhancer.process()
    
    print()
    print("V4 Enhancement Complete!")
    print(f"  CSV: {csv_path}")
    print(f"  JSON: {json_path}")


if __name__ == "__main__":
    main()
