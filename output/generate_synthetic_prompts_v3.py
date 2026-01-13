"""
Synthetic Prompt Generator v3 - Enterprise Context with Variety
================================================================

This version addresses:
1. VARIETY: 10 truly unique prompts per intent with enforced diversity
2. CONTEXT: Real-world enterprise context for actions that need it
3. CONTEXT_TEXT: Separate column with 1+ page content for SUMMARIZE, EXPLAIN, etc.
4. QUALITY: Each prompt is self-contained and clear

Key Improvements over v2:
- Enforced variety constraints (no similar prompts)
- Enterprise context library (meetings, emails, reports, policies)
- Long-form context_text for actions needing input content
- Real-world scenarios (specific projects, teams, industries)
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import random
import hashlib


# =============================================================================
# ENTERPRISE CONTEXT LIBRARY
# =============================================================================

class EnterpriseContextLibrary:
    """
    Library of real-world enterprise contexts for generating realistic prompts.
    Each context type provides varied, specific, realistic content.
    """
    
    # Project names for variety
    PROJECTS = [
        "Project Atlas", "Q2 Product Launch", "Customer Portal Redesign",
        "Cloud Migration Initiative", "Digital Transformation Program",
        "Employee Experience Platform", "Supply Chain Optimization",
        "AI Integration Pilot", "Security Enhancement Program",
        "Mobile App 2.0", "Data Analytics Platform", "CRM Modernization",
        "Sustainability Initiative", "Remote Work Infrastructure",
        "Customer Success Program", "DevOps Transformation"
    ]
    
    # Team names
    TEAMS = [
        "Engineering", "Product", "Marketing", "Sales", "Finance",
        "HR", "Operations", "Customer Success", "Legal", "IT",
        "Design", "Research", "Strategy", "Compliance", "Support"
    ]
    
    # Stakeholder roles
    STAKEHOLDERS = [
        "VP of Engineering", "Chief Product Officer", "Marketing Director",
        "Sales Lead", "CFO", "CHRO", "COO", "CTO", "CEO",
        "Board of Directors", "External Investors", "Key Clients",
        "Regional Manager", "Department Head", "Team Lead"
    ]
    
    # Meeting types
    MEETING_TYPES = [
        "quarterly business review", "sprint planning", "all-hands meeting",
        "project kickoff", "stakeholder sync", "budget review",
        "performance review", "strategy session", "client presentation",
        "team retrospective", "product roadmap review", "executive briefing"
    ]
    
    # Document types
    DOCUMENT_TYPES = [
        "project proposal", "technical specification", "business case",
        "executive summary", "quarterly report", "policy document",
        "training material", "process documentation", "RFP response",
        "product requirements", "market analysis", "competitive analysis"
    ]
    
    # Industries for variety
    INDUSTRIES = [
        "technology", "healthcare", "financial services", "retail",
        "manufacturing", "energy", "telecommunications", "automotive",
        "education", "government", "media", "real estate"
    ]
    
    # Time frames
    TIMEFRAMES = [
        "this week", "last month", "Q3 2025", "the past quarter",
        "since January", "over the last 6 months", "this fiscal year",
        "the past 30 days", "since the last release", "year-to-date"
    ]
    
    # Urgency levels
    URGENCY = [
        "before the board meeting tomorrow",
        "for the client call in 2 hours",
        "by end of day",
        "for Monday's presentation",
        "before the deadline next week",
        "as soon as possible",
        "for the quarterly review",
        "before budget submission"
    ]
    
    @classmethod
    def get_random_project(cls) -> str:
        return random.choice(cls.PROJECTS)
    
    @classmethod
    def get_random_team(cls) -> str:
        return random.choice(cls.TEAMS)
    
    @classmethod
    def get_random_stakeholder(cls) -> str:
        return random.choice(cls.STAKEHOLDERS)
    
    @classmethod
    def get_random_meeting_type(cls) -> str:
        return random.choice(cls.MEETING_TYPES)
    
    @classmethod
    def get_random_timeframe(cls) -> str:
        return random.choice(cls.TIMEFRAMES)


# =============================================================================
# LONG-FORM CONTEXT GENERATORS
# =============================================================================

class LongFormContextGenerator:
    """
    Generates realistic 1+ page context content for actions that need input text.
    """
    
    @staticmethod
    def generate_meeting_notes(project: str, team: str, topic: str) -> str:
        """Generate realistic meeting notes (500-800 words)"""
        date = "January 6, 2026"
        attendees = ["Sarah Chen (Product Lead)", "Marcus Johnson (Engineering Manager)", 
                     "Emily Rodriguez (Design Lead)", "David Kim (QA Lead)", 
                     "Lisa Thompson (Project Manager)", "James Wilson (DevOps)"]
        
        content = f"""MEETING NOTES
=============
Date: {date}
Project: {project}
Team: {team}
Subject: {topic}
Attendees: {', '.join(attendees)}

AGENDA
------
1. Project Status Update
2. Technical Challenges Discussion
3. Timeline Review
4. Resource Allocation
5. Next Steps and Action Items

DISCUSSION SUMMARY
------------------

1. PROJECT STATUS UPDATE

Sarah Chen opened the meeting by providing an overview of the current project status. The team has completed 75% of the planned features for the current sprint. Key milestones achieved include:

- User authentication module completed and deployed to staging
- Database migration scripts tested and validated
- API endpoints for core functionality are 90% complete
- UI components for the main dashboard have been reviewed and approved

However, there are some areas requiring attention. The integration with the third-party payment gateway is experiencing delays due to API documentation issues from the vendor. Marcus mentioned that his team has been working with the vendor's technical support to resolve these issues.

2. TECHNICAL CHALLENGES DISCUSSION

Marcus Johnson presented the technical challenges the engineering team is facing:

a) Performance Optimization: The current implementation shows latency issues when handling more than 1,000 concurrent users. The team is evaluating options including:
   - Implementing Redis caching for frequently accessed data
   - Optimizing database queries with proper indexing
   - Considering horizontal scaling for the application servers

b) Security Concerns: A recent security audit identified three medium-priority vulnerabilities that need to be addressed before the production release:
   - SQL injection risk in the legacy search module
   - Missing rate limiting on authentication endpoints
   - Outdated TLS configuration on some internal services

c) Integration Issues: The third-party API for payment processing has been unreliable, with a 15% failure rate during testing. Alternative vendors are being evaluated.

3. TIMELINE REVIEW

Lisa Thompson reviewed the project timeline. The original launch date was February 15, 2026, but given the current challenges, the team discussed adjusting expectations:

- Best case scenario: February 22, 2026 (one-week delay)
- Most likely scenario: March 1, 2026 (two-week delay)
- Worst case: March 15, 2026 (if major issues arise)

The team agreed to communicate a revised timeline of March 1st to stakeholders, with a caveat that this depends on resolving the payment gateway integration issues by January 20th.

4. RESOURCE ALLOCATION

The discussion on resources highlighted several concerns:

- The front-end team is currently understaffed with only two developers
- Additional QA resources are needed for the security testing phase
- DevOps capacity is stretched thin due to parallel infrastructure projects

David Kim proposed bringing in a contract QA specialist for 6 weeks to support the security testing. Lisa will work with HR to expedite the hiring process.

5. ACTION ITEMS

| Owner | Task | Due Date |
|-------|------|----------|
| Marcus Johnson | Implement Redis caching POC | Jan 10, 2026 |
| Sarah Chen | Finalize vendor evaluation for payment gateway | Jan 12, 2026 |
| Emily Rodriguez | Complete UI accessibility audit | Jan 13, 2026 |
| David Kim | Prepare security testing plan | Jan 8, 2026 |
| Lisa Thompson | Update project timeline for stakeholders | Jan 7, 2026 |
| James Wilson | Configure staging environment monitoring | Jan 9, 2026 |

DECISIONS MADE
--------------
1. Proceed with Redis implementation for caching
2. Evaluate two alternative payment vendors by end of week
3. Communicate revised launch date of March 1, 2026
4. Hire contract QA specialist for security testing phase

NEXT MEETING
------------
Date: January 13, 2026
Time: 2:00 PM - 3:30 PM
Location: Conference Room B / Teams
Focus: Technical solutions review and vendor decision

RISKS AND CONCERNS
------------------
- Payment gateway vendor response time remains unpredictable
- Team morale may be affected by the timeline extension
- Budget implications of the delay need to be assessed
- Client expectations need to be managed proactively

---
Notes prepared by: Lisa Thompson
Distribution: All attendees, Department Heads, PMO
"""
        return content
    
    @staticmethod
    def generate_email_thread(subject: str, context: str) -> str:
        """Generate realistic email thread (400-600 words)"""
        content = f"""EMAIL THREAD
============

From: Jennifer Martinez <jennifer.martinez@company.com>
To: Product Team <product-team@company.com>
Cc: Michael Chang <michael.chang@company.com>
Date: January 8, 2026 9:15 AM
Subject: {subject}

Hi Team,

I wanted to follow up on {context} from our discussion last week. After reviewing the feedback from our beta users, I've identified several areas that need our attention before we can proceed with the wider rollout.

Key findings from the beta program:
- 78% of users found the new interface intuitive
- Average task completion time improved by 23%
- However, 35% reported confusion with the new navigation menu
- Mobile responsiveness issues were reported on tablets

I've attached the detailed feedback report for your review. Can we schedule a meeting this week to discuss our action plan?

Best regards,
Jennifer

---

From: Michael Chang <michael.chang@company.com>
To: Jennifer Martinez <jennifer.martinez@company.com>
Cc: Product Team <product-team@company.com>
Date: January 8, 2026 10:42 AM
Subject: Re: {subject}

Jennifer,

Thanks for consolidating this feedback. The navigation confusion is concerning - we saw similar patterns in our usability testing but hoped the in-app tooltips would help. Clearly, we need a different approach.

I've spoken with the design team, and they can have revised mockups ready by Friday. Proposed changes:
1. Add breadcrumb navigation to all pages
2. Simplify the main menu to max 6 items
3. Introduce a "quick actions" sidebar for power users
4. Create an optional guided tour for first-time users

Regarding the tablet issues - this is a known limitation of the current CSS framework. We have two options:
a) Quick fix: Adjust breakpoints (2-day effort)
b) Proper fix: Migrate to responsive design system (2-week effort)

My recommendation is option (a) for now, with option (b) planned for v2.1.

Let me know when works for the team meeting.

Michael

---

From: Sarah Park <sarah.park@company.com>
To: Michael Chang <michael.chang@company.com>
Cc: Jennifer Martinez <jennifer.martinez@company.com>, Product Team <product-team@company.com>
Date: January 8, 2026 11:30 AM
Subject: Re: {subject}

All,

Adding my perspective from the customer success side. We've received 12 support tickets related to navigation issues in the past week, which is higher than usual. The most common complaints:

1. "Can't find settings anymore" (7 tickets)
2. "Dashboard doesn't load on iPad" (3 tickets)
3. "Logout button is hidden" (2 tickets)

I support Michael's quick fix approach for tablets. For navigation, can we also consider adding a search/command bar? Our enterprise customers have been requesting this for months.

Also flagging that three of our largest accounts are scheduled to onboard next month. We need to resolve these issues before then to avoid churn risk.

Happy to join the discussion.

Sarah

---

From: Jennifer Martinez <jennifer.martinez@company.com>
To: Product Team <product-team@company.com>
Date: January 8, 2026 2:15 PM
Subject: Re: {subject} - Meeting Scheduled

Team,

Thank you all for the quick responses. I've scheduled a meeting for tomorrow at 2 PM to discuss:

1. Navigation redesign approach
2. Quick fix for tablet responsiveness  
3. Search/command bar feasibility
4. Timeline for enterprise onboarding readiness

Meeting invite sent. Please come prepared with any additional customer feedback.

Jennifer
"""
        return content
    
    @staticmethod
    def generate_project_report(project: str, timeframe: str) -> str:
        """Generate project status report (600-900 words)"""
        content = f"""PROJECT STATUS REPORT
=====================

Project: {project}
Reporting Period: {timeframe}
Report Date: January 9, 2026
Prepared By: Project Management Office

EXECUTIVE SUMMARY
-----------------

{project} continues to progress toward its strategic objectives, with significant milestones achieved during {timeframe}. Overall project health is rated YELLOW due to timeline pressures and resource constraints, though quality metrics remain strong.

Key achievements this period:
• Completed Phase 2 technical architecture review
• Onboarded 500+ users to the pilot program
• Achieved 99.7% system uptime during pilot
• Received positive feedback from 82% of pilot participants

Areas of concern:
• Timeline slippage of approximately 2 weeks
• Two key team members transitioning to other projects
• Vendor delivery delays impacting integration testing

BUDGET STATUS
-------------

| Category | Budgeted | Actual | Variance |
|----------|----------|--------|----------|
| Personnel | $450,000 | $425,000 | -$25,000 (favorable) |
| Technology | $200,000 | $215,000 | +$15,000 (unfavorable) |
| Consulting | $100,000 | $85,000 | -$15,000 (favorable) |
| Infrastructure | $150,000 | $160,000 | +$10,000 (unfavorable) |
| Contingency | $50,000 | $30,000 | -$20,000 (used) |
| TOTAL | $950,000 | $915,000 | -$35,000 (favorable) |

The project remains under budget by 3.7%. The technology cost overrun is attributed to additional cloud resources required for performance testing. This was partially offset by lower-than-expected consulting costs.

TIMELINE STATUS
---------------

Original Completion Date: March 31, 2026
Current Projected Date: April 14, 2026
Variance: +14 days

Phase Status:
• Phase 1 - Discovery: COMPLETE (On schedule)
• Phase 2 - Design: COMPLETE (2 days late)
• Phase 3 - Development: IN PROGRESS (5 days behind)
• Phase 4 - Testing: NOT STARTED (Projected 7 days late)
• Phase 5 - Deployment: NOT STARTED (Projected 14 days late)

Root causes for delays:
1. Unexpected complexity in legacy system integration
2. Key subject matter expert availability constraints
3. Requirement changes requested by stakeholders mid-development

Mitigation actions:
1. Added two senior developers to the integration team
2. Scheduled dedicated SME sessions twice weekly
3. Implemented change freeze for remaining development scope

RISK REGISTER UPDATE
--------------------

| Risk | Probability | Impact | Mitigation Status |
|------|-------------|--------|-------------------|
| Vendor delays | High | Medium | Active - Weekly vendor calls |
| Resource attrition | Medium | High | Active - Retention bonuses approved |
| Scope creep | Medium | Medium | Closed - Change freeze in effect |
| Technical debt | Low | High | Monitoring - Refactoring planned for Q2 |
| Security vulnerabilities | Low | Critical | Active - Penetration testing scheduled |

STAKEHOLDER FEEDBACK
--------------------

Feedback collected from key stakeholders during {timeframe}:

"The pilot program exceeded our expectations. The new system is much more intuitive than our current solution." - Operations Director

"We need to ensure the training materials are ready well before go-live. Last time we had issues with user adoption due to inadequate training." - HR Business Partner

"The integration with our CRM is critical. Please prioritize this in the testing phase." - Sales VP

"Cost savings projections look promising. Looking forward to realizing these benefits." - CFO

UPCOMING MILESTONES
-------------------

| Milestone | Target Date | Owner | Status |
|-----------|-------------|-------|--------|
| Complete user acceptance testing | Jan 31, 2026 | QA Lead | On Track |
| Security audit completion | Feb 14, 2026 | InfoSec | On Track |
| Training material finalization | Feb 21, 2026 | L&D Team | At Risk |
| Production environment ready | Feb 28, 2026 | DevOps | On Track |
| Go-live | Apr 14, 2026 | PM | Delayed |

RECOMMENDATIONS
---------------

1. Approve additional budget of $25,000 for accelerated testing resources
2. Expedite vendor escalation process through executive sponsorship
3. Begin change management communications to prepare end users for delayed launch
4. Schedule executive steering committee meeting to review revised timeline

NEXT STEPS
----------

• Weekly status reviews with project sponsors (Fridays at 3 PM)
• Vendor escalation meeting scheduled for January 12
• Risk review session with steering committee on January 15
• User acceptance testing kickoff on January 20

---
Report Distribution: Executive Steering Committee, Project Sponsors, Department Heads
Next Report Due: January 23, 2026
"""
        return content
    
    @staticmethod
    def generate_policy_document(topic: str) -> str:
        """Generate policy document (500-700 words)"""
        content = f"""CORPORATE POLICY DOCUMENT
=========================

Policy Title: {topic}
Policy Number: POL-2026-001
Effective Date: January 1, 2026
Last Reviewed: December 15, 2025
Policy Owner: Human Resources Department
Approval Authority: Chief Human Resources Officer

1. PURPOSE
----------

This policy establishes guidelines and procedures for {topic.lower()} within the organization. It ensures consistency, compliance with applicable regulations, and alignment with organizational values and strategic objectives.

2. SCOPE
--------

This policy applies to:
• All full-time and part-time employees
• Contractors and temporary workers
• Consultants engaged for more than 30 days
• Interns and co-op students
• Third-party vendors with system access

This policy covers all company locations, including:
• Corporate headquarters
• Regional offices
• Remote work environments
• Client sites where employees are deployed

3. POLICY STATEMENT
-------------------

The organization is committed to maintaining the highest standards regarding {topic.lower()}. All employees are expected to adhere to the following principles:

3.1 Core Requirements
- All activities must comply with applicable federal, state, and local regulations
- Employees must complete mandatory training within 30 days of hire
- Annual recertification is required for all covered individuals
- Violations may result in disciplinary action up to and including termination

3.2 Specific Guidelines

a) Documentation Requirements
   - All relevant activities must be documented within 24 hours
   - Records must be retained for a minimum of 7 years
   - Documentation must be stored in approved systems only
   - Personal devices may not be used for storing sensitive information

b) Approval Workflows
   - Level 1 approvals (under $5,000): Direct manager
   - Level 2 approvals ($5,000-$25,000): Department head
   - Level 3 approvals (over $25,000): Vice President or above
   - Emergency exceptions require CFO approval within 48 hours

c) Reporting Obligations
   - Suspected violations must be reported immediately
   - Anonymous reporting available through ethics hotline
   - No retaliation against good-faith reporters
   - Investigations completed within 30 business days

4. ROLES AND RESPONSIBILITIES
-----------------------------

4.1 Employees
- Understand and comply with this policy
- Complete required training on schedule
- Report violations or concerns promptly
- Cooperate with audits and investigations

4.2 Managers
- Ensure team awareness of policy requirements
- Monitor compliance within their teams
- Address violations consistently
- Escalate complex issues appropriately

4.3 Human Resources
- Maintain policy documentation
- Coordinate training programs
- Investigate reported violations
- Recommend policy updates as needed

4.4 Compliance Team
- Conduct periodic audits
- Track compliance metrics
- Report to executive leadership
- Coordinate with legal counsel

5. EXCEPTIONS
-------------

Exceptions to this policy may be granted in extraordinary circumstances. Exception requests must:
- Be submitted in writing to the Policy Owner
- Include business justification
- Specify the duration of the exception
- Be approved by a Vice President or above
- Be documented in the exception log

6. ENFORCEMENT
--------------

Violations of this policy may result in:
- Verbal warning (first offense, minor violation)
- Written warning (repeated minor or first major violation)
- Performance improvement plan
- Suspension without pay
- Termination of employment
- Legal action where warranted

7. RELATED POLICIES
-------------------

- Employee Code of Conduct (POL-2024-003)
- Data Protection and Privacy Policy (POL-2025-012)
- Information Security Policy (POL-2025-008)
- Anti-Harassment Policy (POL-2024-015)

8. REVISION HISTORY
-------------------

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2024 | HR Team | Initial release |
| 1.1 | Jul 2024 | Legal | Updated compliance language |
| 2.0 | Jan 2026 | HR Team | Major revision for new regulations |

---
For questions about this policy, contact: policy@company.com
"""
        return content
    
    @staticmethod
    def generate_technical_document(topic: str) -> str:
        """Generate technical specification (600-800 words)"""
        content = f"""TECHNICAL SPECIFICATION DOCUMENT
=================================

Document Title: {topic}
Version: 2.1.0
Date: January 9, 2026
Author: Technical Architecture Team
Status: Draft for Review

1. OVERVIEW
-----------

This document provides the technical specification for {topic.lower()}. It outlines the system architecture, component design, integration points, and implementation requirements necessary for successful delivery.

1.1 Background
The current system has been in production for 5 years and has accumulated significant technical debt. Key limitations include:
- Monolithic architecture limiting scalability
- Legacy database schema reducing query performance
- Outdated authentication mechanism (security concern)
- Limited API capabilities for partner integrations

1.2 Objectives
- Modernize the system architecture for cloud-native deployment
- Improve system scalability to handle 10x current load
- Implement industry-standard security practices
- Enable seamless third-party integrations via RESTful APIs

2. SYSTEM ARCHITECTURE
----------------------

2.1 High-Level Design
The proposed architecture follows a microservices pattern with the following key components:

┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│              (Authentication, Rate Limiting)                 │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ User Service  │    │ Order Service │    │Product Service│
│   (Node.js)   │    │   (Python)    │    │    (Java)     │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌───────────────┐
                    │ Message Queue │
                    │   (RabbitMQ)  │
                    └───────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  PostgreSQL   │    │  MongoDB      │    │   Redis       │
│  (Primary)    │    │  (Documents)  │    │   (Cache)     │
└───────────────┘    └───────────────┘    └───────────────┘

2.2 Component Specifications

User Service:
- Runtime: Node.js 20 LTS
- Framework: Express.js with TypeScript
- Responsibilities: Authentication, authorization, user profile management
- Database: PostgreSQL (user accounts, permissions)
- Cache: Redis (session data, tokens)

Order Service:
- Runtime: Python 3.12
- Framework: FastAPI
- Responsibilities: Order processing, payment integration, fulfillment
- Database: PostgreSQL (transactions), MongoDB (order history)
- Queue: RabbitMQ (async processing)

Product Service:
- Runtime: Java 21
- Framework: Spring Boot 3.2
- Responsibilities: Product catalog, inventory, search
- Database: PostgreSQL (products), Elasticsearch (search index)
- Cache: Redis (product cache)

3. API SPECIFICATIONS
---------------------

3.1 Authentication
All API requests require JWT authentication:
- Token endpoint: POST /api/v1/auth/token
- Token lifetime: 1 hour (access), 7 days (refresh)
- Algorithm: RS256 with 2048-bit keys

3.2 Rate Limiting
- Anonymous: 100 requests/minute
- Authenticated: 1000 requests/minute
- Premium tier: 10000 requests/minute

3.3 Sample Endpoints

GET /api/v1/users/{{user_id}}
Response: 200 OK
{{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2026-01-09T10:30:00Z"
}}

4. NON-FUNCTIONAL REQUIREMENTS
------------------------------

4.1 Performance
- API response time: < 200ms (95th percentile)
- Database query time: < 50ms (95th percentile)
- Throughput: 10,000 requests/second

4.2 Availability
- Target uptime: 99.9% (excluding maintenance)
- RTO: 4 hours
- RPO: 1 hour

4.3 Security
- Encryption at rest: AES-256
- Encryption in transit: TLS 1.3
- Authentication: OAuth 2.0 / OpenID Connect
- Regular penetration testing (quarterly)

5. DEPLOYMENT ARCHITECTURE
--------------------------

- Cloud Provider: Azure
- Container Orchestration: Kubernetes (AKS)
- CI/CD: Azure DevOps
- Monitoring: Azure Monitor, Application Insights
- Logging: ELK Stack

---
Next Review Date: January 23, 2026
Distribution: Engineering Team, Architecture Review Board
"""
        return content


# =============================================================================
# VARIETY ENFORCER
# =============================================================================

class VarietyEnforcer:
    """
    Ensures 10 prompts per intent are truly unique and diverse.
    Tracks used patterns to prevent similarity.
    """
    
    def __init__(self):
        self.used_patterns = set()
        self.used_contexts = set()
        self.used_scenarios = set()
    
    def reset(self):
        """Reset for new intent"""
        self.used_patterns.clear()
        self.used_contexts.clear()
        self.used_scenarios.clear()
    
    def get_unique_scenario(self, scenarios: List[str]) -> str:
        """Get a scenario not yet used"""
        available = [s for s in scenarios if s not in self.used_scenarios]
        if not available:
            available = scenarios
        choice = random.choice(available)
        self.used_scenarios.add(choice)
        return choice
    
    def get_unique_context(self, contexts: List[str]) -> str:
        """Get a context not yet used"""
        available = [c for c in contexts if c not in self.used_contexts]
        if not available:
            available = contexts
        choice = random.choice(available)
        self.used_contexts.add(choice)
        return choice


# =============================================================================
# MAIN GENERATOR CLASS
# =============================================================================

@dataclass
class IntentRow:
    """Parsed intent row from CSV"""
    action_rank: int
    rank_in_action: int
    reliable: bool
    inv_quality: bool
    inv_retention: bool
    unreliable: bool
    action: str
    object_: str
    subject: str
    output: str
    pct_users: str
    user_count: str
    pct_impressions: str
    impression_count: str
    sat_rate: str
    feedback_count: int
    apology_rate: str
    no_citation_rate: str
    active_weeks_p75: float
    active_weeks_p90: float
    active_weeks_p95: float
    active_weeks_p99: float
    pct_active_weeks_p75: str
    pct_active_weeks_p90: str
    pct_active_weeks_p95: str
    pct_active_weeks_p99: str
    active_days_p75: float
    active_days_p90: float
    active_days_p95: float
    active_days_p99: float
    focus_days_p75: str
    focus_days_p90: str
    focus_days_p95: str
    focus_days_p99: str
    tenant_count: int
    conversation_count: float
    day_count: str
    week_count: str
    thumbs_up_count: int
    thumbs_down_count: int


class SyntheticPromptGeneratorV3:
    """
    V3 Generator with:
    1. Enforced variety across 10 prompts
    2. Enterprise context for all prompts
    3. Long-form context_text for actions that need it
    4. Real-world scenarios
    """
    
    # Actions that NEED context_text (content to process)
    ACTIONS_NEEDING_CONTEXT = {
        'SUMMARIZE', 'EXPLAIN', 'REVIEW', 'ANALYZE', 'ASSESS',
        'EVALUATE', 'PROOFREAD', 'EDIT', 'TRANSLATE', 'REWRITE'
    }
    
    def __init__(self):
        self.prompt_counter = 0
        self.variety = VarietyEnforcer()
        self.context_lib = EnterpriseContextLibrary()
        self.long_form = LongFormContextGenerator()
    
    def _clean_value(self, value: str) -> str:
        """Clean input value"""
        if not value or value.strip() in ['?', '-', 'N/A', 'null', 'undefined']:
            return ''
        return value.strip()
    
    def _needs_context_text(self, action: str) -> bool:
        """Check if action needs long-form context"""
        return action.upper() in self.ACTIONS_NEEDING_CONTEXT
    
    def _generate_context_text(self, action: str, obj: str, variant_idx: int) -> str:
        """Generate appropriate long-form context based on action and object"""
        project = self.context_lib.get_random_project()
        team = self.context_lib.get_random_team()
        
        action_upper = action.upper()
        obj_upper = obj.upper()
        
        # Select context type based on object and variant for variety
        if 'MEETING' in obj_upper or 'NOTES' in obj_upper or variant_idx < 3:
            return self.long_form.generate_meeting_notes(
                project, team, f"{action} discussion for {obj}"
            )
        elif 'EMAIL' in obj_upper or 'MESSAGE' in obj_upper or variant_idx < 5:
            return self.long_form.generate_email_thread(
                f"Re: {project} - {obj}",
                f"the {obj.lower()} implementation"
            )
        elif 'REPORT' in obj_upper or 'STATUS' in obj_upper or variant_idx < 7:
            return self.long_form.generate_project_report(
                project, self.context_lib.get_random_timeframe()
            )
        elif 'POLICY' in obj_upper or 'DOCUMENT' in obj_upper:
            return self.long_form.generate_policy_document(
                f"{obj} Guidelines and Procedures"
            )
        else:
            return self.long_form.generate_technical_document(
                f"{project} - {obj} Technical Specification"
            )
    
    def generate_prompts_for_intent(self, intent: IntentRow) -> List[Dict[str, Any]]:
        """Generate 10 unique, contextual prompts for an intent"""
        
        # Reset variety tracker
        self.variety.reset()
        
        # Clean inputs
        action = self._clean_value(intent.action).upper()
        obj = self._clean_value(intent.object_)
        subject = self._clean_value(intent.subject)
        output = self._clean_value(intent.output)
        
        if not action or not obj:
            return []
        
        # Check subject redundancy
        has_subject = subject and subject.upper() != obj.upper()
        has_output = output and output.upper() != obj.upper()
        
        source_intent = f"{action} + {obj}"
        if has_subject:
            source_intent += f" (Subject: {subject})"
        if has_output:
            source_intent += f" → {output}"
        
        # Determine if we need context_text
        needs_context = self._needs_context_text(action)
        
        prompts = []
        
        # Generate 10 truly diverse prompts
        prompt_configs = self._get_diverse_prompt_configs(action, obj, subject, output, needs_context)
        
        for idx, config in enumerate(prompt_configs):
            self.prompt_counter += 1
            
            # Generate context_text if needed
            context_text = ""
            if needs_context:
                context_text = self._generate_context_text(action, obj, idx)
            
            prompt_record = {
                'synthetic_prompt_id': f'SP_{self.prompt_counter:06d}',
                'source_intent': source_intent,
                'synthetic_prompt': config['prompt'],
                'prompt_scenario': config['scenario'],
                'prompt_variant_type': config['variant_type'],
                'complexity_level': config['complexity'],
                'context_text': context_text,
                'has_context_text': 'Yes' if context_text else 'No',
                'expected_response_criteria': json.dumps(config['criteria']),
                'evaluation_dimensions': json.dumps(config['dimensions']),
                # Input columns
                'input_action': intent.action,
                'input_object': intent.object_,
                'input_subject': intent.subject,
                'input_output': intent.output,
                # Original metadata (keep all)
                'action_rank': intent.action_rank,
                'rank_in_action': intent.rank_in_action,
                'reliable': intent.reliable,
                'inv_quality': intent.inv_quality,
                'inv_retention': intent.inv_retention,
                'unreliable': intent.unreliable,
                'action': intent.action,
                'object': intent.object_,
                'subject': intent.subject,
                'output': intent.output,
                'pct_users': intent.pct_users,
                'user_count': intent.user_count,
                'pct_impressions': intent.pct_impressions,
                'impression_count': intent.impression_count,
                'sat_rate': intent.sat_rate,
                'feedback_count': intent.feedback_count,
                'apology_rate': intent.apology_rate,
                'no_citation_rate': intent.no_citation_rate,
                'active_weeks_p75': intent.active_weeks_p75,
                'active_weeks_p90': intent.active_weeks_p90,
                'active_weeks_p95': intent.active_weeks_p95,
                'active_weeks_p99': intent.active_weeks_p99,
                'pct_active_weeks_p75': intent.pct_active_weeks_p75,
                'pct_active_weeks_p90': intent.pct_active_weeks_p90,
                'pct_active_weeks_p95': intent.pct_active_weeks_p95,
                'pct_active_weeks_p99': intent.pct_active_weeks_p99,
                'active_days_p75': intent.active_days_p75,
                'active_days_p90': intent.active_days_p90,
                'active_days_p95': intent.active_days_p95,
                'active_days_p99': intent.active_days_p99,
                'focus_days_p75': intent.focus_days_p75,
                'focus_days_p90': intent.focus_days_p90,
                'focus_days_p95': intent.focus_days_p95,
                'focus_days_p99': intent.focus_days_p99,
                'tenant_count': intent.tenant_count,
                'conversation_count': intent.conversation_count,
                'day_count': intent.day_count,
                'week_count': intent.week_count,
                'thumbs_up_count': intent.thumbs_up_count,
                'thumbs_down_count': intent.thumbs_down_count
            }
            
            prompts.append(prompt_record)
        
        return prompts
    
    def _get_diverse_prompt_configs(
        self, action: str, obj: str, subject: str, output: str, needs_context: bool
    ) -> List[Dict]:
        """Generate 10 diverse prompt configurations"""
        
        configs = []
        
        # Different scenarios for variety
        scenarios = [
            self._gen_executive_briefing,
            self._gen_client_meeting_prep,
            self._gen_team_collaboration,
            self._gen_quarterly_review,
            self._gen_project_milestone,
            self._gen_compliance_audit,
            self._gen_training_development,
            self._gen_vendor_evaluation,
            self._gen_budget_planning,
            self._gen_strategic_initiative
        ]
        
        for idx, scenario_func in enumerate(scenarios):
            config = scenario_func(action, obj, subject, output, idx, needs_context)
            configs.append(config)
        
        return configs
    
    # ==========================================================================
    # 10 UNIQUE SCENARIO GENERATORS
    # ==========================================================================
    
    def _gen_executive_briefing(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 1: Executive briefing context"""
        project = self.context_lib.get_random_project()
        stakeholder = self.context_lib.get_random_stakeholder()
        
        if needs_context:
            prompt = f"I have the following document that I need to {action.lower()} for a briefing to the {stakeholder}. Please review the content in the context_text column and provide a clear, executive-friendly {output.lower() if output else 'summary'}."
        else:
            prompt = f"I'm preparing a briefing for the {stakeholder} about {project}. Can you {action.lower()} the key {obj.lower()} that I should highlight? Focus on strategic impact and business outcomes."
        
        return {
            'prompt': prompt,
            'scenario': f'Executive Briefing for {stakeholder}',
            'variant_type': 'executive_briefing',
            'complexity': 'expert',
            'criteria': [
                "Response should be executive-appropriate in tone and format",
                f"Should effectively {action.lower()} the {obj.lower()}",
                "Content should focus on strategic value and business impact",
                "Should be concise while covering all critical points"
            ],
            'dimensions': ['accuracy', 'clarity', 'strategic_relevance', 'conciseness', 'professionalism']
        }
    
    def _gen_client_meeting_prep(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 2: Client meeting preparation"""
        industry = random.choice(self.context_lib.INDUSTRIES)
        
        if needs_context:
            prompt = f"I have a meeting with a {industry} client in 2 hours. Please {action.lower()} the attached document (in context_text) and highlight the points most relevant to their industry needs."
        else:
            prompt = f"I have a meeting with a major {industry} client tomorrow. Can you help me {action.lower()} the {obj.lower()} that would be most relevant to their business needs? Include talking points I can use."
        
        return {
            'prompt': prompt,
            'scenario': f'Client Meeting Prep - {industry.title()} Sector',
            'variant_type': 'client_meeting',
            'complexity': 'complex',
            'criteria': [
                f"Response should help prepare for {industry} client meeting",
                f"Should appropriately {action.lower()} the {obj.lower()}",
                "Content should be client-focused and value-oriented",
                "Should include actionable talking points"
            ],
            'dimensions': ['accuracy', 'relevance', 'client_focus', 'actionability', 'clarity']
        }
    
    def _gen_team_collaboration(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 3: Team collaboration context"""
        team = self.context_lib.get_random_team()
        
        if needs_context:
            prompt = f"Our {team} team needs to collaborate on this document. Please {action.lower()} the content in context_text and identify areas where different team members should provide input."
        else:
            prompt = f"I'm working with the {team} team on a cross-functional initiative. Can you {action.lower()} the {obj.lower()} in a way that's accessible to team members with different backgrounds? Include sections for different skill sets."
        
        return {
            'prompt': prompt,
            'scenario': f'Cross-functional {team} Team Collaboration',
            'variant_type': 'team_collaboration',
            'complexity': 'medium',
            'criteria': [
                f"Response should facilitate {team} team collaboration",
                "Should be accessible to team members with varied backgrounds",
                f"Should effectively {action.lower()} the {obj.lower()}",
                "Should identify areas for team input"
            ],
            'dimensions': ['clarity', 'accessibility', 'collaboration_focus', 'organization', 'actionability']
        }
    
    def _gen_quarterly_review(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 4: Quarterly business review"""
        timeframe = "Q4 2025"
        
        if needs_context:
            prompt = f"For our {timeframe} quarterly business review, I need to {action.lower()} this document. Please process the context_text and highlight trends, achievements, and areas needing attention."
        else:
            prompt = f"I'm preparing the {timeframe} quarterly business review. Can you {action.lower()} the {obj.lower()} with focus on quarter-over-quarter trends, key achievements, and areas requiring leadership attention?"
        
        return {
            'prompt': prompt,
            'scenario': f'{timeframe} Quarterly Business Review',
            'variant_type': 'quarterly_review',
            'complexity': 'complex',
            'criteria': [
                "Response should be suitable for quarterly review format",
                "Should highlight trends and quarter-over-quarter changes",
                f"Should effectively {action.lower()} the {obj.lower()}",
                "Should identify achievements and areas of concern"
            ],
            'dimensions': ['accuracy', 'trend_analysis', 'completeness', 'strategic_insight', 'clarity']
        }
    
    def _gen_project_milestone(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 5: Project milestone context"""
        project = self.context_lib.get_random_project()
        milestone = random.choice(["Phase 2 completion", "UAT sign-off", "Go-live readiness", "MVP delivery"])
        
        if needs_context:
            prompt = f"We're approaching the {milestone} milestone for {project}. Please {action.lower()} the document in context_text and assess our readiness status."
        else:
            prompt = f"We're approaching {milestone} for {project}. Can you {action.lower()} the {obj.lower()} to assess readiness? Include any blockers or risks that might delay the milestone."
        
        return {
            'prompt': prompt,
            'scenario': f'{project} - {milestone} Assessment',
            'variant_type': 'project_milestone',
            'complexity': 'complex',
            'criteria': [
                "Response should assess milestone readiness",
                "Should identify blockers and risks",
                f"Should effectively {action.lower()} the {obj.lower()}",
                "Should provide actionable recommendations"
            ],
            'dimensions': ['accuracy', 'risk_identification', 'completeness', 'actionability', 'timeliness']
        }
    
    def _gen_compliance_audit(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 6: Compliance and audit context"""
        regulation = random.choice(["SOC 2", "GDPR", "HIPAA", "ISO 27001", "PCI DSS"])
        
        if needs_context:
            prompt = f"We have an upcoming {regulation} audit. Please {action.lower()} the document in context_text from a compliance perspective and flag any potential gaps."
        else:
            prompt = f"We're preparing for a {regulation} compliance audit next month. Can you {action.lower()} the {obj.lower()} with focus on compliance requirements? Highlight any gaps or documentation we might need."
        
        return {
            'prompt': prompt,
            'scenario': f'{regulation} Compliance Audit Preparation',
            'variant_type': 'compliance_audit',
            'complexity': 'expert',
            'criteria': [
                f"Response should address {regulation} compliance requirements",
                "Should identify compliance gaps or risks",
                f"Should effectively {action.lower()} the {obj.lower()}",
                "Should recommend remediation steps"
            ],
            'dimensions': ['accuracy', 'compliance_awareness', 'completeness', 'risk_identification', 'actionability']
        }
    
    def _gen_training_development(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 7: Training and development context"""
        audience = random.choice(["new hires", "managers", "technical staff", "sales team", "customer support"])
        
        if needs_context:
            prompt = f"I'm developing training materials for {audience}. Please {action.lower()} the content in context_text and restructure it for a learning-focused format."
        else:
            prompt = f"I'm creating training content for {audience}. Can you {action.lower()} the {obj.lower()} in a way that's educational and easy to learn? Include key takeaways and potential quiz questions."
        
        return {
            'prompt': prompt,
            'scenario': f'Training Development for {audience.title()}',
            'variant_type': 'training_development',
            'complexity': 'medium',
            'criteria': [
                f"Response should be appropriate for {audience} learning level",
                "Should be structured for educational purposes",
                f"Should effectively {action.lower()} the {obj.lower()}",
                "Should include learning aids and key takeaways"
            ],
            'dimensions': ['clarity', 'educational_value', 'accessibility', 'engagement', 'accuracy']
        }
    
    def _gen_vendor_evaluation(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 8: Vendor evaluation context"""
        vendor_type = random.choice(["SaaS platform", "consulting firm", "hardware supplier", "cloud provider"])
        
        if needs_context:
            prompt = f"We're evaluating a {vendor_type} vendor. Please {action.lower()} their proposal (in context_text) and create a comparison framework for our evaluation committee."
        else:
            prompt = f"We're evaluating {vendor_type} vendors. Can you {action.lower()} the {obj.lower()} to help with our vendor selection process? Include evaluation criteria and scoring recommendations."
        
        return {
            'prompt': prompt,
            'scenario': f'{vendor_type.title()} Vendor Evaluation',
            'variant_type': 'vendor_evaluation',
            'complexity': 'complex',
            'criteria': [
                "Response should support vendor evaluation process",
                "Should provide objective comparison framework",
                f"Should effectively {action.lower()} the {obj.lower()}",
                "Should include scoring or ranking methodology"
            ],
            'dimensions': ['objectivity', 'completeness', 'analytical_depth', 'decision_support', 'clarity']
        }
    
    def _gen_budget_planning(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 9: Budget planning context"""
        fiscal_year = "FY2027"
        
        if needs_context:
            prompt = f"I'm working on {fiscal_year} budget planning. Please {action.lower()} the financial document in context_text and identify cost optimization opportunities."
        else:
            prompt = f"I'm preparing the {fiscal_year} budget proposal. Can you {action.lower()} the {obj.lower()} with focus on cost drivers, investment priorities, and potential savings? Include budget justification talking points."
        
        return {
            'prompt': prompt,
            'scenario': f'{fiscal_year} Budget Planning',
            'variant_type': 'budget_planning',
            'complexity': 'expert',
            'criteria': [
                "Response should support budget planning process",
                "Should identify cost drivers and savings opportunities",
                f"Should effectively {action.lower()} the {obj.lower()}",
                "Should provide budget justification support"
            ],
            'dimensions': ['financial_accuracy', 'analytical_depth', 'completeness', 'actionability', 'clarity']
        }
    
    def _gen_strategic_initiative(self, action: str, obj: str, subject: str, output: str, idx: int, needs_context: bool) -> Dict:
        """Scenario 10: Strategic initiative context"""
        initiative = random.choice([
            "Digital Transformation", "Sustainability Program", "Market Expansion",
            "Customer Experience Enhancement", "Operational Excellence", "Innovation Labs"
        ])
        
        if needs_context:
            prompt = f"Our {initiative} initiative needs strategic review. Please {action.lower()} the document in context_text and assess alignment with our corporate strategy."
        else:
            prompt = f"I'm leading the {initiative} strategic initiative. Can you {action.lower()} the {obj.lower()} from a strategic perspective? Focus on competitive advantage, long-term value, and alignment with corporate goals."
        
        return {
            'prompt': prompt,
            'scenario': f'{initiative} Strategic Initiative',
            'variant_type': 'strategic_initiative',
            'complexity': 'expert',
            'criteria': [
                "Response should address strategic considerations",
                "Should assess alignment with corporate strategy",
                f"Should effectively {action.lower()} the {obj.lower()}",
                "Should identify competitive advantages and long-term value"
            ],
            'dimensions': ['strategic_insight', 'completeness', 'analytical_depth', 'forward_thinking', 'clarity']
        }


def load_intents_from_csv(csv_path: str) -> List[IntentRow]:
    """Load and parse intent rows from CSV file"""
    intents = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            action = row.get('Action', '').strip()
            obj = row.get('Object', '').strip()
            
            if not action or not obj or action == '?' or obj == '?':
                continue
            
            try:
                intent = IntentRow(
                    action_rank=int(row.get('action_rank', 0) or 0),
                    rank_in_action=int(row.get('rank_in_action', 0) or 0),
                    reliable=row.get('Reliable', 'FALSE').upper() == 'TRUE',
                    inv_quality=row.get('Inv_Quality', 'FALSE').upper() == 'TRUE',
                    inv_retention=row.get('Inv_Retention', 'FALSE').upper() == 'TRUE',
                    unreliable=row.get('Unreliable', 'FALSE').upper() == 'TRUE',
                    action=action,
                    object_=obj,
                    subject=row.get('Subject', '').strip(),
                    output=row.get('Output', '').strip(),
                    pct_users=row.get('%_Users', '').strip(),
                    user_count=row.get(' UserCount ', '').strip(),
                    pct_impressions=row.get('%_Impressions', '').strip(),
                    impression_count=row.get(' ImpressionCount ', '').strip(),
                    sat_rate=row.get('SatRate', '').strip(),
                    feedback_count=int(row.get('FeedbackCount', 0) or 0),
                    apology_rate=row.get('ApologyRate', '').strip(),
                    no_citation_rate=row.get('NoCitationRate', '').strip(),
                    active_weeks_p75=float(row.get('Active_Weeks_p75', 1.0) or 1.0),
                    active_weeks_p90=float(row.get('Active_Weeks_p90', 1.0) or 1.0),
                    active_weeks_p95=float(row.get('Active_Weeks_p95', 1.0) or 1.0),
                    active_weeks_p99=float(row.get('Active_Weeks_p99', 1.0) or 1.0),
                    pct_active_weeks_p75=row.get('%_Active_weeks_p75', '').strip(),
                    pct_active_weeks_p90=row.get('%_Active_weeks_p90', '').strip(),
                    pct_active_weeks_p95=row.get('%_Active_weeks_p95', '').strip(),
                    pct_active_weeks_p99=row.get('%_Active_weeks_p99', '').strip(),
                    active_days_p75=float(row.get('Active_Days_p75', 1.0) or 1.0),
                    active_days_p90=float(row.get('Active_Days_p90', 1.0) or 1.0),
                    active_days_p95=float(row.get('Active_Days_p95', 1.0) or 1.0),
                    active_days_p99=float(row.get('Active_Days_p99', 1.0) or 1.0),
                    focus_days_p75=row.get('Focus_Days_p75', '').strip(),
                    focus_days_p90=row.get('Focus_Days_p90', '').strip(),
                    focus_days_p95=row.get('Focus_Days_p95', '').strip(),
                    focus_days_p99=row.get('Focus_Days_p99', '').strip(),
                    tenant_count=int(row.get('TenantCount', 0) or 0),
                    conversation_count=float(row.get('ConversationCount', 0) or 0),
                    day_count=row.get('DayCount', '').strip(),
                    week_count=row.get('WeekCount', '').strip(),
                    thumbs_up_count=int(row.get('ThumbsUpCountClipped', 0) or 0),
                    thumbs_down_count=int(row.get('ThumbsDownCountClipped', 0) or 0)
                )
                intents.append(intent)
            except Exception as e:
                print(f"Warning: Skipping row due to error: {e}")
                continue
    
    return intents


def main():
    """Main entry point"""
    INPUT_CSV = "bizchat-work-nam_exploded-intents_20250215-20250509.csv"
    OUTPUT_DIR = Path("synthetic_prompts")
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 80)
    print("Synthetic Prompt Generator v3 - Enterprise Context with Variety")
    print("=" * 80)
    print(f"\nInput: {INPUT_CSV}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    # Load intents
    print("Loading intents from CSV...")
    intents = load_intents_from_csv(INPUT_CSV)
    print(f"Loaded {len(intents)} valid intent rows")
    
    # Initialize generator
    generator = SyntheticPromptGeneratorV3()
    
    # Generate prompts
    print("\nGenerating synthetic prompts with enterprise context...")
    all_prompts = []
    
    for i, intent in enumerate(intents):
        prompts = generator.generate_prompts_for_intent(intent)
        all_prompts.extend(prompts)
        
        if (i + 1) % 25 == 0:
            print(f"  Processed {i + 1}/{len(intents)} intents... ({len(all_prompts)} prompts)")
    
    print(f"\nGenerated {len(all_prompts)} synthetic prompts")
    
    # Count context_text prompts
    with_context = sum(1 for p in all_prompts if p.get('context_text'))
    print(f"Prompts with context_text: {with_context}")
    
    # Export to CSV
    csv_path = OUTPUT_DIR / f"synthetic_prompts_v3_{timestamp}.csv"
    
    if all_prompts:
        fieldnames = list(all_prompts[0].keys())
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_prompts)
        
        print(f"\nExported to: {csv_path}")
    
    # Export to JSON
    json_path = OUTPUT_DIR / f"synthetic_prompts_v3_{timestamp}.json"
    
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'source_file': INPUT_CSV,
            'total_intents': len(intents),
            'total_prompts': len(all_prompts),
            'prompts_with_context': with_context,
            'prompts_per_intent': 10,
            'version': '3.0',
            'features': [
                'Enforced variety across 10 prompts per intent',
                'Enterprise context for all prompts',
                'Long-form context_text for SUMMARIZE/EXPLAIN/etc actions',
                '10 unique business scenarios per intent',
                'Real-world enterprise scenarios'
            ]
        },
        'prompts': all_prompts
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported to: {json_path}")
    
    # Print samples
    print("\n" + "=" * 80)
    print("SAMPLE PROMPTS (First Intent - 10 Variants)")
    print("=" * 80)
    
    if len(all_prompts) >= 10:
        for i in range(10):
            p = all_prompts[i]
            print(f"\n[{p['synthetic_prompt_id']}] {p['prompt_scenario']}")
            print(f"  Type: {p['prompt_variant_type']} ({p['complexity_level']})")
            print(f"  Prompt: {p['synthetic_prompt'][:200]}...")
            print(f"  Has Context: {p['has_context_text']}")
    
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    
    # Scenario distribution
    scenario_counts = {}
    for p in all_prompts:
        st = p['prompt_variant_type']
        scenario_counts[st] = scenario_counts.get(st, 0) + 1
    
    print("\nScenario Distribution:")
    for st, count in sorted(scenario_counts.items()):
        print(f"  {st}: {count}")
    
    print("\n" + "=" * 80)
    print("Generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
